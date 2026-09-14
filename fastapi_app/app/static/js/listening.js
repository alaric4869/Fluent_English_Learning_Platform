(() => {
  const workspace = document.querySelector(".listening-workspace");
  if (!workspace) return;
  const status = document.querySelector("#listeningActionStatus");
  const resourceId = workspace.dataset.resourceId;

  function setStatus(message, isError = false) {
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  }

  document.querySelector("#toggleTranscript")?.addEventListener("click", (event) => {
    const sentences = document.querySelector("#transcriptSentences");
    if (!sentences) return;
    sentences.classList.toggle("is-hidden");
    event.currentTarget.textContent = sentences.classList.contains("is-hidden")
      ? "显示 Transcript"
      : "隐藏 Transcript";
  });

  document.querySelectorAll(".transcript-sentence").forEach((row) => {
    row.querySelectorAll("[data-sentence-status]").forEach((button) => {
      button.addEventListener("click", async () => {
        const sentence = row.querySelector(".sentence-text")?.textContent?.trim();
        const state = row.querySelector(".sentence-save-state");
        if (!sentence) return;
        row.querySelectorAll("button").forEach((item) => { item.disabled = true; });
        if (state) state.textContent = "正在保存…";
        try {
          const response = await fetch(`/api/listening/resources/${resourceId}/sentences`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              sentence,
              practice_status: button.dataset.sentenceStatus
            })
          });
          const body = await response.json().catch(() => ({}));
          if (!response.ok) {
            throw new Error(typeof body.detail === "string" ? body.detail : "句子状态保存失败。");
          }
          row.dataset.sentenceId = String(body.id);
          row.dataset.currentStatus = body.practice_status;
          row.classList.add("has-status");
          row.querySelectorAll("[data-sentence-status]").forEach((item) => {
            item.classList.toggle("is-active", item.dataset.sentenceStatus === body.practice_status);
          });
          if (state) state.textContent = body.review_item_id
            ? `已进入 Review · 下次 ${body.next_review_date}`
            : "已保存到 Notebook";
          setStatus("句子状态已保存。困难句会按间隔自动复习。");
        } catch (error) {
          if (state) state.textContent = "保存失败，请重试";
          setStatus(error.message, true);
        } finally {
          row.querySelectorAll("button").forEach((item) => { item.disabled = false; });
        }
      });
    });
  });
})();
