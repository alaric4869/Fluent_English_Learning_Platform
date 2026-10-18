(() => {
  const page = document.querySelector(".review-page");
  const status = document.querySelector("#reviewActionStatus");
  if (!page) return;

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

  const form = document.querySelector("#vocabularyForm");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submit = form.querySelector("button[type='submit']");
      const data = new FormData(form);
      submit.disabled = true;
      setStatus("正在保存词块…");
      try {
        await request("/api/vocabulary", {
          method: "POST",
          body: JSON.stringify({
            chunk: String(data.get("chunk") || ""),
            meaning: String(data.get("meaning") || ""),
            example_sentence: String(data.get("example_sentence") || ""),
            learned_on: data.get("learned_on") || null,
            personal_note: String(data.get("personal_note") || ""),
            difficulty: String(data.get("difficulty") || "medium"),
            source_resource_id: null,
            source_context: String(data.get("source_context") || ""),
            tags: String(data.get("tags") || "").split(",").map((tag) => tag.trim()).filter(Boolean)
          })
        });
        window.location.reload();
      } catch (error) {
        submit.disabled = false;
        setStatus(error.message, true);
      }
    });
  }

  document.querySelectorAll(".due-review-card").forEach((card) => {
    const answer = card.querySelector(".review-answer");
    const buttons = Array.from(card.querySelectorAll("[data-rating]"));
    answer?.addEventListener("toggle", () => {
      buttons.forEach((button) => { button.disabled = !answer.open; });
    });
    buttons.forEach((button) => {
      button.addEventListener("click", async () => {
        const rating = button.dataset.rating;
        if (!card.dataset.pendingRequestId || card.dataset.pendingRating !== rating) {
          card.dataset.pendingRequestId = crypto.randomUUID();
          card.dataset.pendingRating = rating;
        }
        buttons.forEach((item) => { item.disabled = true; });
        setStatus("正在安排下一次复习…");
        try {
          const result = await request(
            `/api/reviews/${card.dataset.reviewItemId}/rate`,
            {
              method: "POST",
              body: JSON.stringify({
                rating,
                request_id: card.dataset.pendingRequestId
              })
            }
          );
          card.remove();
          const dueCount = document.querySelector("#dueCount");
          if (dueCount) dueCount.textContent = String(Math.max(0, Number(dueCount.textContent) - 1));
          setStatus(`已保存，下次复习：${result.next_review_date}`);
          if (!document.querySelector(".due-review-card")) window.location.reload();
        } catch (error) {
          buttons.forEach((item) => { item.disabled = false; });
          setStatus(error.message, true);
        }
      });
    });
  });
})();
