(() => {
  const page = document.querySelector(".today-page");
  const status = document.querySelector("#todayActionStatus");
  if (!page) return;

  const planDate = page.dataset.planDate;

  function setStatus(message, isError = false) {
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  }

  async function request(url, options) {
    const response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) }
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(typeof body.detail === "string" ? body.detail : "保存失败，请重试。");
    }
    return body;
  }

  function sessionEndpoint(card) {
    return `/api/study-plans/${planDate}/items/${card.dataset.planItemId}/sessions`;
  }

  function numericValue(element) {
    return element && element.value ? Number(element.value) : null;
  }

  function formatDuration(seconds) {
    const safe = Math.max(0, Number(seconds) || 0);
    const hours = Math.floor(safe / 3600);
    const minutes = Math.floor((safe % 3600) / 60);
    const remaining = safe % 60;
    return hours
      ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remaining).padStart(2, "0")}`
      : `${String(minutes).padStart(2, "0")}:${String(remaining).padStart(2, "0")}`;
  }

  function setupSession(card) {
    const timer = card.querySelector(".session-timer");
    const summaryTimer = card.querySelector(".session-summary-time");
    const timerButton = card.querySelector(".session-timer-button");
    const notes = card.querySelector(".session-notes");
    const difficulty = card.querySelector(".session-difficulty");
    const confidence = card.querySelector(".session-confidence");
    const saveState = card.querySelector(".session-save-state");
    let savedSeconds = Number(card.dataset.activeSeconds || 0);
    let runningSince = null;
    let saveTimer = null;
    let startPromise = null;

    const currentSeconds = () => savedSeconds + (
      runningSince === null ? 0 : Math.floor((performance.now() - runningSince) / 1000)
    );

    const renderTimer = () => {
      const label = formatDuration(currentSeconds());
      if (timer) timer.textContent = label;
      if (summaryTimer) summaryTimer.textContent = label;
    };

    const progressPayload = () => ({
      active_duration_seconds: currentSeconds(),
      notes: notes ? notes.value : "",
      perceived_difficulty: numericValue(difficulty),
      confidence: numericValue(confidence)
    });

    async function startSession() {
      if (card.dataset.sessionStatus === "completed") return card.dataset.sessionId;
      if (!card.dataset.sessionId) {
        if (!startPromise) {
          startPromise = request(sessionEndpoint(card), {
            method: "POST",
            body: JSON.stringify({})
          });
        }
        const session = await startPromise.finally(() => { startPromise = null; });
        card.dataset.sessionId = String(session.id);
        card.dataset.sessionStatus = session.status;
        savedSeconds = session.active_duration_seconds;
        if (saveState) saveState.textContent = "学习记录已开始，并会自动保存。";
      }
      return card.dataset.sessionId;
    }

    async function saveProgress({ quiet = false, keepalive = false } = {}) {
      if (!card.dataset.sessionId || card.dataset.sessionStatus === "completed") return;
      const elapsed = currentSeconds();
      if (runningSince !== null) {
        savedSeconds = elapsed;
        runningSince = performance.now();
      }
      const response = await fetch(
        `${sessionEndpoint(card)}/${card.dataset.sessionId}`,
        {
          method: "PATCH",
          keepalive,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(progressPayload())
        }
      );
      if (!response.ok) {
        if (!quiet) {
          const body = await response.json().catch(() => ({}));
          throw new Error(typeof body.detail === "string" ? body.detail : "学习记录保存失败。");
        }
        return;
      }
      if (saveState) saveState.textContent = "已自动保存计时、笔记和评分。";
    }

    async function toggleTimer() {
      if (runningSince === null) {
        await startSession();
        runningSince = performance.now();
        timerButton.textContent = "暂停并保存";
        if (saveState) saveState.textContent = "正在记录有效学习时间…";
      } else {
        savedSeconds = currentSeconds();
        runningSince = null;
        timerButton.textContent = "继续计时";
        await saveProgress();
      }
      renderTimer();
    }

    async function completeSession() {
      await startSession();
      if (runningSince !== null) {
        savedSeconds = currentSeconds();
        runningSince = null;
      }
      return request(
        `${sessionEndpoint(card)}/${card.dataset.sessionId}/complete`,
        { method: "POST", body: JSON.stringify(progressPayload()) }
      );
    }

    if (timerButton) {
      timerButton.addEventListener("click", async () => {
        timerButton.disabled = true;
        try {
          await toggleTimer();
        } catch (error) {
          setStatus(error.message, true);
        } finally {
          timerButton.disabled = false;
        }
      });
    }

    [notes, difficulty, confidence].filter(Boolean).forEach((field) => {
      field.addEventListener("input", () => {
        window.clearTimeout(saveTimer);
        saveTimer = window.setTimeout(async () => {
          try {
            await startSession();
            await saveProgress();
          } catch (error) {
            setStatus(error.message, true);
          }
        }, 700);
      });
    });

    const startLink = card.querySelector(".module-start-link");
    if (startLink && card.dataset.sessionStatus !== "completed") {
      startLink.addEventListener("click", () => {
        startSession()
          .then(() => {
            if (runningSince === null) {
              runningSince = performance.now();
              if (timerButton) timerButton.textContent = "暂停并保存";
              if (saveState) saveState.textContent = "材料已打开，正在记录有效学习时间…";
            }
          })
          .catch((error) => setStatus(error.message, true));
      });
    }

    window.setInterval(renderTimer, 1000);
    window.setInterval(() => saveProgress({ quiet: true }), 15000);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        saveProgress({ quiet: true, keepalive: true });
      }
    });
    window.addEventListener("pagehide", () => saveProgress({ quiet: true, keepalive: true }));
    renderTimer();
    card.studySession = { complete: completeSession };
  }

  document.querySelectorAll("[data-plan-item-id]").forEach(setupSession);

  document.querySelectorAll(".module-status-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const card = button.closest("[data-plan-item-id]");
      if (!card) return;
      button.disabled = true;
      setStatus("正在更新进度…");
      try {
        if (button.dataset.nextStatus === "completed") {
          await card.studySession.complete();
        } else {
          await request(
            `/api/study-plans/${planDate}/items/${card.dataset.planItemId}/status`,
            { method: "PATCH", body: JSON.stringify({ status: button.dataset.nextStatus }) }
          );
        }
        window.location.reload();
      } catch (error) {
        button.disabled = false;
        setStatus(error.message, true);
      }
    });
  });

  document.querySelectorAll(".plan-override-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const card = form.closest("[data-plan-item-id]");
      const submit = form.querySelector("button[type='submit']");
      if (!card || !submit) return;
      const data = new FormData(form);
      const resourceValue = data.get("resource_id");
      submit.disabled = true;
      setStatus("正在保存调整…");
      try {
        await request(`/api/study-plans/${planDate}/items/${card.dataset.planItemId}`, {
          method: "PUT",
          body: JSON.stringify({
            planned_minutes: Number(data.get("planned_minutes")),
            resource_id: resourceValue ? Number(resourceValue) : null,
            note: String(data.get("note") || "")
          })
        });
        window.location.reload();
      } catch (error) {
        submit.disabled = false;
        setStatus(error.message, true);
      }
    });
  });
})();
