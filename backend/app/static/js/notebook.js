(() => {
  const status = document.querySelector("#notebookActionStatus");

  const showStatus = (message, isError = false) => {
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  };

  const splitValues = (value) => value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const formPayload = (form) => {
    const data = Object.fromEntries(new FormData(form).entries());
    if ("tags" in data) data.tags = splitValues(data.tags);
    if ("intended_vocabulary" in data) {
      data.intended_vocabulary = splitValues(data.intended_vocabulary);
    }
    if (form.id === "listeningForm") {
      data.add_to_review = form.elements.add_to_review.checked;
    }
    return data;
  };

  document.querySelectorAll("form[data-endpoint]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button[type='submit']");
      if (button) button.disabled = true;
      try {
        const response = await fetch(form.dataset.endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formPayload(form)),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "保存失败");
        showStatus("已保存");
        window.location.assign(`/notebook?view=${form.dataset.returnView}`);
      } catch (error) {
        showStatus(error.message, true);
        if (button) button.disabled = false;
      }
    });
  });

  document.querySelectorAll(".sentence-status-select").forEach((select) => {
    select.addEventListener("change", async () => {
      const card = select.closest("[data-sentence-id]");
      select.disabled = true;
      try {
        const response = await fetch(
          `/api/listening/sentences/${card.dataset.sentenceId}/status`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ practice_status: select.value }),
          },
        );
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "更新失败");
        showStatus("听辨状态已更新");
        window.location.reload();
      } catch (error) {
        showStatus(error.message, true);
        select.disabled = false;
      }
    });
  });
})();
