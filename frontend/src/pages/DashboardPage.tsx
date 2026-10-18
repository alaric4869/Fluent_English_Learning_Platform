import { useCallback, type CSSProperties } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";


export function DashboardPage() {
  const loader = useCallback((signal: AbortSignal) => frontendApi.dashboard(signal), []);
  const { data, error } = useApiQuery(loader);

  return (
    <AppShell activePage="dashboard" plannedMinutes={data?.total_minutes}>
      {error && <ErrorState message={error} />}
      {!data && !error && <LoadingState />}
      {data && (
        <div className="page-container">
          <section className="hero-row">
            <div>
              <p className="eyebrow">{data.display_date}</p>
              <h1>{data.greeting}，今天具体学什么？</h1>
              <p>计划已经根据你的学习记录准备好。完成一项，留下一个真实证据。</p>
            </div>
            <div className="progress-orb" style={{ "--progress": `${data.completion_percent * 3.6}deg` } as CSSProperties}>
              <strong>{data.completion_percent}%</strong>
              <span>today</span>
            </div>
          </section>

          <section className="study-panel">
            <div className="section-heading">
              <div><p className="eyebrow">Today's study plan</p><h2>四个清晰模块，约 {data.total_minutes} 分钟</h2></div>
              <a className="text-link" href="/today">打开完整计划 →</a>
            </div>
            <div className="module-grid">
              {data.modules.map((module) => (
                <article className={`module-card ${module.completed ? "complete" : ""}`} key={module.item_id}>
                  <div className="module-card-top"><span>{module.code}</span><b>{module.planned_minutes} min</b></div>
                  <h3>{module.title}</h3>
                  <p>{module.resource_title}</p>
                  <div className="module-card-footer"><small>{module.status.replace("_", " ")}</small><a href="/today">View plan</a></div>
                </article>
              ))}
            </div>
          </section>

          <section className="dashboard-grid">
            <article className="review-card">
              <p className="eyebrow">Reviews due today</p>
              <strong>{data.due_review_count}</strong>
              <p>需要在今天重新遇见的词块与难句。</p>
            </article>
            <div className="stats-grid">
              <Stat label="Current streak" value={`${data.stats.current_streak} days`} />
              <Stat label="Study time this week" value={`${data.stats.this_week_completed_planned_minutes} min`} />
              <Stat label="Completed sessions" value={String(data.stats.completed_sessions)} />
              <Stat label="Reviews completed" value={String(data.stats.completed_reviews)} />
            </div>
          </section>
        </div>
      )}
    </AppShell>
  );
}


function Stat({ label, value }: { label: string; value: string }) {
  return <article className="stat-card"><p>{label}</p><strong>{value}</strong></article>;
}
