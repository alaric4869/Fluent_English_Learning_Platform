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

  document.querySelectorAll(".module-status-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const card = button.closest("[data-plan-item-id]");
      if (!card) return;
      button.disabled = true;
      setStatus("正在更新进度…");
      try {
        await request(
          `/api/study-plans/${planDate}/items/${card.dataset.planItemId}/status`,
          { method: "PATCH", body: JSON.stringify({ status: button.dataset.nextStatus }) }
        );
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
