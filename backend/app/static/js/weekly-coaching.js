(() => {
  const button = document.querySelector("#generateWeeklyCoaching");
  if (!button) return;

  const report = document.querySelector("#agentReport");
  const reportText = document.querySelector("#agentReportText");
  const reportProvider = document.querySelector("#agentReportProvider");
  const reportTime = document.querySelector("#agentReportTime");
  const reportTools = document.querySelector("#agentReportTools");
  const status = document.querySelector("#agentCoachStatus");
  const toolLabels = {
    generate_weekly_report: "本周学习数据",
    get_skill_profile: "技能画像",
    get_weak_skills: "强弱项判断",
    get_due_reviews: "到期复习",
  };

  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "正在分析…";
    status.textContent = "Agent 正在读取允许的结构化学习数据。";
    try {
      const response = await fetch("/api/agent/weekly-coaching", { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "生成失败");

      reportText.textContent = payload.output_text;
      reportProvider.textContent = payload.provider_name.toUpperCase();
      reportTime.textContent = new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Australia/Sydney",
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(payload.created_at));
      reportTools.replaceChildren(
        ...payload.tools_used.map((tool) => {
          const label = document.createElement("span");
          label.textContent = toolLabels[tool] || tool;
          return label;
        }),
      );
      report.classList.remove("is-hidden");
      button.textContent = "重新生成建议";
      status.textContent = "已保存本周 AI 建议；刷新页面后仍可查看。";
    } catch (error) {
      status.textContent = error.message || "AI 服务暂时不可用，请稍后重试。";
      button.textContent = "重试生成";
    } finally {
      button.disabled = false;
    }
  });
})();
