(() => {
  const workspace = document.querySelector(".speaking-workspace");
  if (!workspace) return;

  const resourceId = workspace.dataset.resourceId;
  const fields = {
    written_outline: document.querySelector("#speakingOutline"),
    intended_vocabulary: document.querySelector("#speakingVocabulary"),
    retelling_text: document.querySelector("#speakingRetelling"),
    mistakes: document.querySelector("#speakingMistakes"),
    improved_version: document.querySelector("#speakingImproved"),
    practice_status: document.querySelector("#speakingPracticeStatus"),
    perceived_difficulty: document.querySelector("#speakingDifficulty"),
    confidence: document.querySelector("#speakingConfidence")
  };
  const timer = document.querySelector("#speakingTimer");
  const timerToggle = document.querySelector("#speakingTimerToggle");
  const saveState = document.querySelector("#speakingSaveState");
  const actionStatus = document.querySelector("#speakingActionStatus");
  const submissionNote = document.querySelector("#speakingSubmissionNote");
  const submitButton = document.querySelector("#submitSpeaking");
  const evaluationButton = document.querySelector("#evaluateSpeaking");
  const evaluationAvailable = workspace.dataset.aiEvaluationAvailable === "true";
  let accumulatedSeconds = Number(workspace.dataset.savedSeconds || 0);
  let timerStartedAt = null;
  let timerInterval = null;
  let saveTimeout = null;
  let savingPromise = Promise.resolve();

  function splitChunks(value) {
    return [...new Set(value.split(/[\n,]+/).map((item) => item.trim()).filter(Boolean))];
  }

  function activeSeconds() {
    if (!timerStartedAt) return accumulatedSeconds;
    return accumulatedSeconds + Math.floor((Date.now() - timerStartedAt) / 1000);
  }

  function renderTimer() {
    const seconds = activeSeconds();
    timer.textContent = `${Math.floor(seconds / 60).toString().padStart(2, "0")}:${(seconds % 60).toString().padStart(2, "0")}`;
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

  function payload() {
    return {
      written_outline: fields.written_outline.value,
      intended_vocabulary: splitChunks(fields.intended_vocabulary.value),
      retelling_text: fields.retelling_text.value,
      mistakes: fields.mistakes.value,
      improved_version: fields.improved_version.value,
      practice_status: fields.practice_status.value,
      active_duration_seconds: activeSeconds(),
      perceived_difficulty: fields.perceived_difficulty.value ? Number(fields.perceived_difficulty.value) : null,
      confidence: fields.confidence.value ? Number(fields.confidence.value) : null
    };
  }

  function setAction(message, isError = false) {
    actionStatus.textContent = message;
    actionStatus.classList.toggle("is-error", isError);
  }

  async function saveDraft({ quiet = false } = {}) {
    clearTimeout(saveTimeout);
    if (!quiet) saveState.textContent = "正在保存…";
    const response = await fetch(`/api/speaking/${resourceId}/draft`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload())
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = typeof body.detail === "string" ? body.detail : "口语草稿保存失败。";
      saveState.textContent = "保存失败";
      setAction(message, true);
      throw new Error(message);
    }
    accumulatedSeconds = Math.max(accumulatedSeconds, body.active_duration_seconds);
    workspace.dataset.draftStatus = body.status;
    saveState.textContent = "草稿已保存";
    if (body.status !== "submitted") submissionNote.classList.add("is-hidden");
    return body;
  }

  function scheduleSave() {
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

  Object.values(fields).forEach((field) => {
    field.addEventListener("input", scheduleSave);
    field.addEventListener("change", scheduleSave);
  });

  document.querySelector("#toggleSpeakingTranscript")?.addEventListener("click", (event) => {
    const list = document.querySelector("#shadowingSentenceList");
    list.classList.toggle("transcript-hidden");
    event.currentTarget.textContent = list.classList.contains("transcript-hidden")
      ? "显示 Transcript"
      : "隐藏 Transcript";
  });

  document.querySelectorAll(".shadowing-sentence").forEach((row) => {
    row.querySelectorAll("[data-speaking-status]").forEach((button) => {
      button.addEventListener("click", async () => {
        row.querySelectorAll("[data-speaking-status]").forEach((item) => { item.disabled = true; });
        try {
          const response = await fetch(`/api/speaking/${resourceId}/sentences/${encodeURIComponent(row.dataset.sentenceKey)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ practice_status: button.dataset.speakingStatus })
          });
          const body = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "句子状态保存失败。");
          row.dataset.currentStatus = body.practice_status;
          row.classList.add("has-status");
          row.querySelectorAll("[data-speaking-status]").forEach((item) => {
            item.classList.toggle("is-active", item.dataset.speakingStatus === body.practice_status);
          });
          row.querySelector(".sentence-practice-count").textContent = `练习 ${body.practice_count} 次`;
          renderSentenceCounts();
          setAction("逐句练习状态已保存。");
        } catch (error) {
          setAction(error.message, true);
        } finally {
          row.querySelectorAll("[data-speaking-status]").forEach((item) => { item.disabled = false; });
        }
      });
    });
  });

  function renderSentenceCounts() {
    const rows = [...document.querySelectorAll(".shadowing-sentence")];
    document.querySelector("#speakingMarkedCount").textContent = String(rows.filter((row) => row.dataset.currentStatus).length);
    document.querySelector("#speakingMasteredCount").textContent = String(rows.filter((row) => row.dataset.currentStatus === "mastered").length);
  }

  submitButton.addEventListener("click", async () => {
    submitButton.disabled = true;
    saveState.textContent = "正在提交…";
    try {
      pauseTimer();
      clearTimeout(saveTimeout);
      await savingPromise;
      await saveDraft({ quiet: true });
      const response = await fetch(`/api/speaking/${resourceId}/submit`, { method: "POST" });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "口语练习提交失败。");
      workspace.dataset.draftStatus = "submitted";
      saveState.textContent = `第 ${body.submission_revision} 版已提交`;
      submissionNote.classList.remove("is-hidden");
      if (evaluationButton && evaluationAvailable) evaluationButton.disabled = false;
      setAction("口语练习已提交，History 与 Progress 已更新。");
    } catch (error) {
      saveState.textContent = "提交失败，请检查后重试";
      setAction(error.message, true);
    } finally {
      submitButton.disabled = false;
    }
  });

  evaluationButton?.addEventListener("click", async () => {
    evaluationButton.disabled = true;
    setAction("正在分析当前文字复述…");
    try {
      const response = await fetch(`/api/speaking/${resourceId}/evaluation`, { method: "POST" });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "AI 反馈生成失败。");
      window.location.reload();
    } catch (error) {
      setAction(error.message, true);
      evaluationButton.disabled = !evaluationAvailable;
    }
  });

  window.addEventListener("pagehide", () => {
    const hasContent = [
      fields.written_outline.value,
      fields.retelling_text.value,
      fields.mistakes.value,
      fields.improved_version.value
    ].some((value) => value.trim()) || splitChunks(fields.intended_vocabulary.value).length;
    if (!hasContent) return;
    fetch(`/api/speaking/${resourceId}/draft`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload()),
      keepalive: true
    }).catch(() => {});
  });

  renderTimer();
  renderSentenceCounts();
})();
