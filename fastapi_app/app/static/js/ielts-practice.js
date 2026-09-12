(() => {
  const workspace = document.querySelector(".workspace");
  if (!workspace) return;

  const slug = workspace.dataset.practiceSlug;
  const answerContainers = [...document.querySelectorAll(".answer-container")];
  const questionButtons = [...document.querySelectorAll("[data-jump-question]")];
  const progressText = document.querySelector("#progressText");
  const progressBar = document.querySelector("#progressBar");
  const saveStatus = document.querySelector("#saveStatus");
  const submitButton = document.querySelector("#submitAttempt");
  const scoreCard = document.querySelector("#scoreCard");
  const scoreValue = document.querySelector("#scoreValue");
  const textTimers = new Map();
  const dirtyNumbers = new Set();
  let saveQueue = Promise.resolve();

  const numbersFor = (container) =>
    container.dataset.questionNumbers.split(" ").map(Number).filter(Number.isInteger);

  const containerForNumber = (number) =>
    answerContainers.find((container) => numbersFor(container).includes(Number(number)));

  const valuesFor = (container) => {
    const numbers = numbersFor(container);
    const values = new Map();
    if (container.dataset.maxSelections) {
      const selections = [...container.querySelectorAll(".group-choice:checked")].map((input) => input.value);
      numbers.forEach((number, index) => values.set(number, selections[index] ?? ""));
      return values;
    }

    numbers.forEach((number) => {
      const controls = [...container.querySelectorAll(`[data-answer-number="${number}"]`)];
      const radio = controls.find((control) => control.type === "radio" && control.checked);
      const text = controls.find((control) => control.type === "text");
      values.set(number, radio?.value ?? text?.value.trim() ?? "");
    });
    return values;
  };

  const answersFromPage = () => {
    const answers = new Map();
    answerContainers.forEach((container) => {
      valuesFor(container).forEach((answer, number) => answers.set(number, answer));
    });
    return answers;
  };

  const updateProgress = () => {
    const answers = answersFromPage();
    const answered = [...answers.values()].filter(Boolean).length;
    const total = questionButtons.length;
    progressText.textContent = `${answered}/${total}`;
    progressBar.style.width = `${total ? (answered / total) * 100 : 0}%`;
    questionButtons.forEach((button) => {
      button.classList.toggle("is-answered", Boolean(answers.get(Number(button.dataset.jumpQuestion))));
    });
  };

  const clearGrading = () => {
    answerContainers.forEach((container) => container.classList.remove("is-correct", "is-wrong"));
    questionButtons.forEach((button) => button.classList.remove("is-correct", "is-wrong"));
    document.querySelectorAll(".question-feedback").forEach((feedback) => feedback.classList.add("is-hidden"));
    scoreCard.classList.add("is-hidden");
  };

  const showSection = (sectionNumber, scroll = true) => {
    document.querySelectorAll(".practice-section").forEach((section) => {
      section.classList.toggle("is-hidden", section.dataset.section !== String(sectionNumber));
    });
    document.querySelectorAll(".section-tab").forEach((tab) => {
      const active = tab.dataset.sectionTarget === `section-${sectionNumber}`;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });
    if (scroll) {
      document.querySelector(".section-picker")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const persistValues = async (container, snapshot) => {
    const label = [...snapshot.keys()].join("–");
    saveStatus.textContent = `正在保存第 ${label} 题…`;
    for (const [number, answer] of snapshot) {
      const response = await fetch(`/api/ielts/${slug}/answers/${number}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      });
      if (!response.ok) throw new Error("save failed");
    }

    const current = answersFromPage();
    snapshot.forEach((answer, number) => {
      if (current.get(number) === answer) dirtyNumbers.delete(number);
    });
    container.classList.remove("is-missing");
    saveStatus.textContent = "已自动保存";
  };

  const queueSave = (container) => {
    const snapshot = valuesFor(container);
    saveQueue = saveQueue
      .catch(() => undefined)
      .then(() => persistValues(container, snapshot))
      .catch(() => {
        saveStatus.textContent = "保存失败，请检查本地服务";
      });
    return saveQueue;
  };

  const markChanged = (container) => {
    numbersFor(container).forEach((number) => dirtyNumbers.add(number));
    container.classList.remove("is-missing");
    clearGrading();
    updateProgress();
  };

  const flushDirtyAnswers = async () => {
    for (const container of answerContainers) {
      if (numbersFor(container).some((number) => dirtyNumbers.has(number))) {
        await queueSave(container);
      }
    }
    await saveQueue;
  };

  const renderResults = (results) => {
    const groupedResults = new Map();
    results.forEach((result) => {
      const container = containerForNumber(result.number);
      if (!container) return;
      if (!groupedResults.has(container)) groupedResults.set(container, []);
      groupedResults.get(container).push(result);

      const button = questionButtons.find((item) => Number(item.dataset.jumpQuestion) === result.number);
      button?.classList.toggle("is-correct", result.is_correct);
      button?.classList.toggle("is-wrong", !result.is_correct);
    });

    groupedResults.forEach((containerResults, container) => {
      const correct = containerResults.every((result) => result.is_correct);
      container.classList.toggle("is-correct", correct);
      container.classList.toggle("is-wrong", !correct);
      const feedback = container.querySelector(".question-feedback");
      if (!feedback || correct) {
        feedback?.classList.add("is-hidden");
        return;
      }

      const submitted = containerResults.map((result) => result.submitted_answer || "未作答").join(" / ");
      const correctAnswers = [...new Set(containerResults.flatMap((result) => result.correct_answers))];
      const explanations = [...new Set(containerResults.map((result) => result.explanation).filter(Boolean))];
      feedback.querySelector(".feedback-title").textContent = `回答错误 · 你的答案：${submitted}`;
      feedback.querySelector(".correct-answer").textContent = `正确答案：${correctAnswers.join(" / ")}`;
      feedback.querySelector(".explanation").textContent = explanations.join(" ");
      feedback.classList.remove("is-hidden");
    });
  };

  document.querySelectorAll(".section-tab").forEach((tab) => {
    tab.addEventListener("click", () => showSection(tab.dataset.sectionTarget.split("-")[1]));
  });
  document.querySelectorAll(".section-change").forEach((button) => {
    button.addEventListener("click", () => showSection(button.dataset.goSection));
  });

  questionButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const number = Number(button.dataset.jumpQuestion);
      showSection(button.dataset.questionSection, false);
      questionButtons.forEach((item) => item.classList.toggle("is-current", item === button));
      requestAnimationFrame(() => {
        containerForNumber(number)?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  });

  answerContainers.forEach((container) => {
    container.querySelectorAll(".group-choice").forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const maximum = Number(container.dataset.maxSelections);
        const checked = container.querySelectorAll(".group-choice:checked");
        const hint = container.querySelector(".selection-hint");
        if (checked.length > maximum) {
          checkbox.checked = false;
          hint.textContent = `这组题只能选择 ${maximum} 项。`;
          hint.classList.add("is-warning");
          window.setTimeout(() => {
            hint.textContent = `最多选择 ${maximum} 项。`;
            hint.classList.remove("is-warning");
          }, 1800);
          return;
        }
        markChanged(container);
        void queueSave(container);
      });
    });

    container.querySelectorAll("input[type='radio']").forEach((radio) => {
      radio.addEventListener("change", () => {
        markChanged(container);
        void queueSave(container);
      });
    });

    container.querySelectorAll("input[type='text']").forEach((input) => {
      input.addEventListener("input", () => {
        markChanged(container);
        window.clearTimeout(textTimers.get(input));
        textTimers.set(input, window.setTimeout(() => void queueSave(container), 650));
      });
      input.addEventListener("blur", () => {
        window.clearTimeout(textTimers.get(input));
        textTimers.delete(input);
        void queueSave(container);
      });
    });
  });

  submitButton.addEventListener("click", async () => {
    submitButton.disabled = true;
    submitButton.textContent = "正在评分…";
    answerContainers.forEach((container) => container.classList.remove("is-missing"));
    try {
      await flushDirtyAnswers();
      const response = await fetch(`/api/ielts/${slug}/submit`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) {
        const missing = payload.detail?.missing_questions ?? [];
        missing.forEach((number) => containerForNumber(number)?.classList.add("is-missing"));
        if (missing.length) {
          const first = containerForNumber(missing[0]);
          showSection(first.closest(".practice-section").dataset.section, false);
          requestAnimationFrame(() => first.scrollIntoView({ behavior: "smooth", block: "center" }));
          saveStatus.textContent = `还有 ${missing.length} 题未完成`;
        }
        return;
      }

      renderResults(payload.questions);
      scoreValue.textContent = payload.score;
      scoreCard.classList.remove("is-hidden");
      saveStatus.textContent = "评分完成，错题精解已展开";
      const firstWrong = payload.questions.find((item) => !item.is_correct);
      if (firstWrong) {
        const container = containerForNumber(firstWrong.number);
        showSection(container.closest(".practice-section").dataset.section, false);
        requestAnimationFrame(() => container.scrollIntoView({ behavior: "smooth", block: "center" }));
      }
    } catch {
      saveStatus.textContent = "提交失败，请稍后重试";
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "完成全部并提交";
    }
  });

  const timerValue = document.querySelector("#timerValue");
  const timerToggle = document.querySelector("#timerToggle");
  const timerCard = document.querySelector(".exam-timer");
  let remainingSeconds = Number(workspace.dataset.durationMinutes) * 60;
  let timerId = null;
  const paintTimer = () => {
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    timerValue.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  };
  timerToggle.addEventListener("click", () => {
    if (timerId) {
      window.clearInterval(timerId);
      timerId = null;
      timerToggle.textContent = "继续计时";
      return;
    }
    if (remainingSeconds <= 0) return;
    timerToggle.textContent = "暂停";
    timerId = window.setInterval(() => {
      remainingSeconds = Math.max(0, remainingSeconds - 1);
      paintTimer();
      if (remainingSeconds === 0) {
        window.clearInterval(timerId);
        timerId = null;
        timerToggle.textContent = "时间到";
        timerToggle.disabled = true;
        timerCard.classList.add("is-finished");
      }
    }, 1000);
  });

  updateProgress();
  const initialResults = JSON.parse(document.querySelector("#initialResults")?.textContent || "[]");
  if (initialResults.length) renderResults(initialResults);
})();
