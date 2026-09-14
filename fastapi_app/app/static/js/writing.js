(() => {
  const workspace = document.querySelector(".writing-workspace");
  if (!workspace) return;

  const resourceId = workspace.dataset.resourceId;
  const minimumWords = Number(workspace.dataset.minimumWords || 0);
  const responseField = document.querySelector("#writingResponse");
  const outlineField = document.querySelector("#writingOutline");
  const difficultyField = document.querySelector("#writingDifficulty");
  const confidenceField = document.querySelector("#writingConfidence");
  const saveState = document.querySelector("#writingSaveState");
  const actionStatus = document.querySelector("#writingActionStatus");
  const wordCount = document.querySelector("#writingWordCount strong");
  const progress = document.querySelector("#writingTargetProgress");
  const timer = document.querySelector("#writingTimer");
  const timerToggle = document.querySelector("#writingTimerToggle");
  const submitButton = document.querySelector("#submitWriting");
  const submissionNote = document.querySelector("#writingSubmissionNote");
  let accumulatedSeconds = Number(workspace.dataset.savedSeconds || 0);
  let timerStartedAt = null;
  let timerInterval = null;
  let saveTimeout = null;
  let savingPromise = Promise.resolve();

  function words(value) {
    return value.trim().match(/\b[\p{L}\p{N}_]+(?:['’-][\p{L}\p{N}_]+)*\b/gu)?.length || 0;
  }

  function activeSeconds() {
    if (!timerStartedAt) return accumulatedSeconds;
    return accumulatedSeconds + Math.floor((Date.now() - timerStartedAt) / 1000);
  }

  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
    const remainder = (seconds % 60).toString().padStart(2, "0");
    return `${minutes}:${remainder}`;
  }

  function renderTimer() {
    timer.textContent = formatTime(activeSeconds());
  }

  function pauseTimer() {
    if (!timerStartedAt) return;
    accumulatedSeconds = activeSeconds();
    timerStartedAt = null;
    clearInterval(timerInterval);
    timerInterval = null;
    timerToggle.textContent = "继续计时";
    renderTimer();
  }

  function renderWordCount() {
    const count = words(responseField.value);
    wordCount.textContent = String(count);
    progress.style.width = `${Math.min(100, Math.round(count / minimumWords * 100))}%`;
    return count;
  }

  function payload() {
    return {
      response_text: responseField.value,
      outline: outlineField.value,
      active_duration_seconds: activeSeconds(),
      perceived_difficulty: difficultyField.value ? Number(difficultyField.value) : null,
      confidence: confidenceField.value ? Number(confidenceField.value) : null
    };
  }

  function setAction(message, isError = false) {
    actionStatus.textContent = message;
    actionStatus.classList.toggle("is-error", isError);
  }

  async function saveDraft({ quiet = false } = {}) {
    clearTimeout(saveTimeout);
    if (!quiet) saveState.textContent = "正在保存…";
    const response = await fetch(`/api/writing/${resourceId}/draft`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload())
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = typeof body.detail === "string" ? body.detail : "草稿保存失败。";
      saveState.textContent = "保存失败";
      setAction(message, true);
      throw new Error(message);
    }
    accumulatedSeconds = Math.max(accumulatedSeconds, body.active_duration_seconds);
    saveState.textContent = "草稿已保存";
    workspace.dataset.draftStatus = body.status;
    if (body.status !== "submitted") submissionNote.classList.add("is-hidden");
    return body;
  }

  function scheduleSave() {
    renderWordCount();
    saveState.textContent = "等待自动保存…";
    if (workspace.dataset.draftStatus === "submitted") {
      workspace.dataset.draftStatus = "in_progress";
      submissionNote.classList.add("is-hidden");
    }
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      savingPromise = savingPromise.then(() => saveDraft()).catch(() => {});
    }, 700);
  }

  timerToggle.addEventListener("click", () => {
    if (timerStartedAt) {
      pauseTimer();
      savingPromise = savingPromise.then(() => saveDraft({ quiet: true })).catch(() => {});
      return;
    }
    timerStartedAt = Date.now();
    timerToggle.textContent = "暂停计时";
    timerInterval = setInterval(renderTimer, 1000);
  });

  [responseField, outlineField, difficultyField, confidenceField].forEach((field) => {
    field.addEventListener("input", scheduleSave);
    field.addEventListener("change", scheduleSave);
  });

  submitButton.addEventListener("click", async () => {
    submitButton.disabled = true;
    saveState.textContent = "正在提交…";
    try {
      pauseTimer();
      clearTimeout(saveTimeout);
      await savingPromise;
      await saveDraft({ quiet: true });
      const response = await fetch(`/api/writing/${resourceId}/submit`, { method: "POST" });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = body.detail;
        throw new Error(
          typeof detail === "object" && detail?.message
            ? detail.message
            : typeof detail === "string" ? detail : "提交失败。"
        );
      }
      workspace.dataset.draftStatus = "submitted";
      saveState.textContent = `第 ${body.submission_revision} 版已提交`;
      submissionNote.classList.remove("is-hidden");
      setAction(`写作已提交：${body.word_count} 词，学习记录已更新。`);
    } catch (error) {
      saveState.textContent = "提交失败，请检查后重试";
      setAction(error.message, true);
    } finally {
      submitButton.disabled = false;
    }
  });

  window.addEventListener("pagehide", () => {
    if (!responseField.value && !outlineField.value) return;
    fetch(`/api/writing/${resourceId}/draft`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload()),
      keepalive: true
    }).catch(() => {});
  });

  renderTimer();
  renderWordCount();
})();
