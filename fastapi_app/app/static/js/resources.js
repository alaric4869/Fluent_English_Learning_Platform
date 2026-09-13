(() => {
  const status = document.querySelector("#resourceActionStatus");

  const showStatus = (message, isError = false) => {
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  };

  const splitTags = (value) => value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const formPayload = (form) => {
    const data = Object.fromEntries(new FormData(form).entries());
    data.tags = splitTags(data.tags || "");
    data.estimated_duration_minutes = Number(data.estimated_duration_minutes);
    data.priority = Number(data.priority || 50);
    data.source_url = data.source_url || null;
    data.difficulty = data.difficulty || null;
    return data;
  };

  document.querySelectorAll("[data-resource-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button[type='submit']");
      if (button) button.disabled = true;
      try {
        const response = await fetch(form.dataset.endpoint, {
          method: form.dataset.method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formPayload(form)),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "保存失败");
        showStatus("资源已保存");
        window.location.assign(`/library/${result.id}`);
      } catch (error) {
        showStatus(error.message, true);
        if (button) button.disabled = false;
      }
    });
  });

  document.querySelectorAll("[data-resource-state]").forEach((button) => {
    button.addEventListener("click", async () => {
      const container = button.closest("[data-resource-id]");
      const resourceId = container?.dataset.resourceId
        || document.querySelector("[data-resource-id]")?.dataset.resourceId;
      if (!resourceId) return;
      button.disabled = true;
      const field = button.dataset.resourceState;
      const value = button.dataset.stateValue === "true";
      try {
        const response = await fetch(`/api/resources/${resourceId}/state`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [field]: value }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "更新失败");
        showStatus(field === "archived" ? "归档状态已更新" : "资源状态已更新");
        window.location.assign(field === "archived" ? "/library" : window.location.href);
      } catch (error) {
        showStatus(error.message, true);
        button.disabled = false;
      }
    });
  });
})();
