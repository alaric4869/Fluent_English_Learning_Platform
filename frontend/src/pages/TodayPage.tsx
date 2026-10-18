import { useCallback } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { BACKEND_PAGE_URL, frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";


export function TodayPage() {
  const loader = useCallback((signal: AbortSignal) => frontendApi.today(signal), []);
  const { data, error } = useApiQuery(loader);

  return (
    <AppShell activePage="today" plannedMinutes={data?.total_minutes}>
      {error && <ErrorState message={error} />}
      {!data && !error && <LoadingState />}
      {data && (
        <div className="page-container">
          <section className="hero-row compact-hero">
            <div>
              <p className="eyebrow">Today's study plan · {data.display_date}</p>
              <h1>打开网站，就知道下一步做什么</h1>
              <p>{data.completed_count}/{data.modules.length} modules completed · {data.due_review_count} reviews due</p>
            </div>
            <strong className="plan-total">{data.total_minutes}<small>min</small></strong>
          </section>

          {data.explanation.length > 0 && (
            <section className="adaptation-note">
              <p className="eyebrow">Why this plan</p>
              <ul>{data.explanation.map((reason) => <li key={reason}>{reason}</li>)}</ul>
            </section>
          )}

          <section className="today-list">
            {data.modules.map((module, index) => (
              <article className={`today-card ${module.completed ? "complete" : ""}`} key={module.item_id}>
                <div className="today-number">{String(index + 1).padStart(2, "0")}</div>
                <div className="today-body">
                  <div className="today-title-row">
                    <div><span className="module-code">{module.code}</span><h2>{module.title}</h2></div>
                    <strong>{module.planned_minutes} min</strong>
                  </div>
                  <div className="resource-block">
                    <p className="eyebrow">Today's material</p>
                    <h3>{module.resource_title}</h3>
                    <p>{module.resource_meta}</p>
                  </div>
                  <div className="instruction-grid">
                    <div><p className="eyebrow">How to study</p><p>{module.instruction}</p></div>
                    <div><p className="eyebrow">Learning objective</p><p>{module.objective}</p></div>
                  </div>
                  {module.ai_recommendation && (
                    <div className="ai-note"><strong>AI suggestion</strong><p>{module.ai_recommendation.reasons.join(" ")}</p></div>
                  )}
                  <div className="today-actions">
                    <span className={`status-pill ${module.status}`}>{module.status.replace("_", " ")}</span>
                    {module.start_href ? (
                      <a className="primary-button" href={`${BACKEND_PAGE_URL}${module.start_href}`}>Start module</a>
                    ) : (
                      <a className="secondary-button" href={`${BACKEND_PAGE_URL}/library`}>Choose material</a>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </section>
          <p className="migration-message">核心学习管理页面已由 React 渲染；IELTS 与专项练习工作区将在 M22 接入同一 API。</p>
        </div>
      )}
    </AppShell>
  );
}
