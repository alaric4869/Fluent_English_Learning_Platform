(() => {
  const workspace = document.querySelector(".workspace");
  if (!workspace) return;

  const slug = workspace.dataset.practiceSlug;
  const questionCards = [...document.querySelectorAll(".question-card")];
  const progressText = document.querySelector("#progressText");
  const progressBar = document.querySelector("#progressBar");
  const saveStatus = document.querySelector("#saveStatus");
  const submitButton = document.querySelector("#submitAttempt");
  let saveTimer;

  const getAnswer = (card) => {
    const checked = card.querySelector("input[type='radio']:checked");
    const text = card.querySelector("input[type='text']");
    return checked?.value ?? text?.value.trim() ?? "";
  };

  const updateProgress = () => {
    const answered = questionCards.filter((card) => getAnswer(card)).length;
    progressText.textContent = `${answered} / ${questionCards.length}`;
    progressBar.style.width = `${(answered / questionCards.length) * 100}%`;
  };

  const showSection = (sectionNumber) => {
    document.querySelectorAll(".practice-section").forEach((section) => {
      section.classList.toggle("is-hidden", section.dataset.section !== String(sectionNumber));
    });
    document.querySelectorAll(".section-tab").forEach((tab) => {
      tab.classList.toggle("is-active", tab.dataset.sectionTarget === `section-${sectionNumber}`);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const saveAnswer = async (card) => {
    const number = card.dataset.questionNumber;
    saveStatus.textContent = `正在保存第 ${number} 题…`;
    try {
      const response = await fetch(`/api/ielts/${slug}/answers/${number}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: getAnswer(card) }),
      });
      if (!response.ok) throw new Error("save failed");
      saveStatus.textContent = "已自动保存";
      card.classList.remove("is-missing");
      questionCards.forEach((item) => item.classList.remove("is-correct", "is-wrong"));
      document.querySelectorAll(".question-feedback").forEach((item) => item.classList.add("is-hidden"));
      document.querySelector("#scoreCard").classList.add("is-hidden");
      updateProgress();
    } catch {
      saveStatus.textContent = "保存失败，请检查本地服务";
    }
  };

  const renderResults = (results) => {
    results.forEach((result) => {
      const card = document.querySelector(`#question-${result.number}`);
      if (!card) return;
      card.classList.toggle("is-correct", result.is_correct);
      card.classList.toggle("is-wrong", !result.is_correct);
      const feedback = card.querySelector(".question-feedback");
      const title = card.querySelector(".feedback-title");
      if (result.is_correct) {
        feedback.classList.add("is-hidden");
        return;
      }
      feedback.classList.remove("is-hidden");
      title.textContent = "需要复习";
      card.querySelector(".correct-answer").textContent = `正确答案：${result.correct_answers.join(" / ")}`;
      card.querySelector(".explanation").textContent = result.explanation;
    });
  };

  document.querySelectorAll(".section-tab").forEach((tab) => {
    tab.addEventListener("click", () => showSection(tab.dataset.sectionTarget.split("-")[1]));
  });
  document.querySelectorAll(".section-change").forEach((button) => {
    button.addEventListener("click", () => showSection(button.dataset.goSection));
  });

  questionCards.forEach((card) => {
    card.querySelectorAll("input[type='radio']").forEach((input) => {
      input.addEventListener("change", () => saveAnswer(card));
    });
    const textInput = card.querySelector("input[type='text']");
    if (textInput) {
      textInput.addEventListener("input", () => {
        updateProgress();
        clearTimeout(saveTimer);
        saveTimer = setTimeout(() => saveAnswer(card), 650);
      });
      textInput.addEventListener("blur", () => saveAnswer(card));
    }
  });

  submitButton.addEventListener("click", async () => {
    submitButton.disabled = true;
    submitButton.textContent = "正在评分…";
    questionCards.forEach((card) => card.classList.remove("is-missing"));
    try {
      const response = await fetch(`/api/ielts/${slug}/submit`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) {
        const missing = payload.detail?.missing_questions ?? [];
        missing.forEach((number) => document.querySelector(`#question-${number}`)?.classList.add("is-missing"));
        if (missing.length) {
          const firstCard = document.querySelector(`#question-${missing[0]}`);
          showSection(firstCard.closest(".practice-section").dataset.section);
          firstCard.scrollIntoView({ behavior: "smooth", block: "center" });
          saveStatus.textContent = `还有 ${missing.length} 题未完成`;
        }
        return;
      }
      renderResults(payload.questions);
      document.querySelector("#scoreValue").textContent = payload.score;
      document.querySelector("#scoreCard").classList.remove("is-hidden");
      saveStatus.textContent = "评分完成，错题精解已展开";
      const firstWrong = payload.questions.find((item) => !item.is_correct);
      if (firstWrong) {
        const card = document.querySelector(`#question-${firstWrong.number}`);
        showSection(card.closest(".practice-section").dataset.section);
        card.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    } catch {
      saveStatus.textContent = "提交失败，请稍后重试";
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "完成全部并提交";
    }
  });

  updateProgress();
  const initialResults = JSON.parse(document.querySelector("#initialResults")?.textContent || "[]");
  if (initialResults.length) renderResults(initialResults);
})();
