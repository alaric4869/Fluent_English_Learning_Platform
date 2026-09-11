"use client";

import type { AppAction, AppStateDto, StudyPlanItemDto } from "../../modules/shared/contracts";
import { StudyModuleCard } from "./StudyModuleCard";
import { ProgressRing, formatDate } from "./ui";

export function DashboardView({ state, onStart, onAction, onAddResource }: {
  state: AppStateDto;
  onStart: (item: StudyPlanItemDto) => void;
  onAction: (action: AppAction) => Promise<boolean>;
  onAddResource: () => void;
}) {
  const complete = state.today.planItems.filter((item) => item.status === "completed").length;
  const progress = Math.round((complete / state.today.planItems.length) * 100);
  const nextItem = state.today.planItems.find((item) => item.status !== "completed") ?? state.today.planItems[0];

  return (
    <div className="page-wrap dashboard-page">
      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">{formatDate(state.today.date)} · Day focus</p>
          <h1>Good evening.<br /><em>Let’s make today count.</em></h1>
          <p className="hero-subtitle">Your plan is ready. One focused session at a time—no deciding, no searching.</p>
          <div className="theme-banner">
            <span>Today’s practical theme</span>
            <strong>{state.today.theme}</strong>
          </div>
        </div>
        <aside className="today-summary-card">
          <div className="summary-top"><div><p className="eyebrow">Today’s progress</p><h2>{complete} of 4 modules</h2></div><ProgressRing value={progress} /></div>
          <div className="summary-stats">
            <div><strong>{state.today.targetMinutes}</strong><span>minutes planned</span></div>
            <div><strong>{state.dueReviews.length}</strong><span>reviews due</span></div>
            <div><strong>{state.progress.currentStreak}</strong><span>day streak</span></div>
          </div>
          {nextItem && <button className="primary-button full" onClick={() => onStart(nextItem)}>Continue with {nextItem.module} <span>→</span></button>}
        </aside>
      </section>

      {state.today.adaptationReasons.length > 0 && (
        <section className="adaptation-card">
          <span className="adaptation-mark">i</span>
          <div><p className="eyebrow">Plan adjustment</p><h3>Today’s balance is based on your recent practice.</h3><p>{state.today.adaptationReasons[0]}</p></div>
          <a href="/progress">See why →</a>
        </section>
      )}

      <section className="section-block">
        <div className="section-heading">
          <div><p className="eyebrow">Your next 110 minutes</p><h2>Today’s study plan</h2></div>
          <p>Follow the cards from left to right, or start with the module that fits your energy.</p>
        </div>
        <div className="module-grid">
          {state.today.planItems.map((item) => <StudyModuleCard item={item} key={item.id} onStart={onStart} onAction={onAction} />)}
        </div>
      </section>

      <section className="dashboard-lower-grid">
        <div className="due-review-card">
          <div className="section-heading compact-heading"><div><p className="eyebrow">Memory work</p><h2>Reviews due today</h2></div><span className="count-badge">{state.dueReviews.length}</span></div>
          <div className="review-type-list">
            {[
              ["Vocabulary chunks", state.dueReviews.filter((item) => item.targetType === "vocabulary").length],
              ["Difficult sentences", state.dueReviews.filter((item) => item.targetType === "sentence").length],
              ["Speaking expressions", state.dueReviews.filter((item) => item.targetType === "expression").length],
            ].map(([label, count]) => <div key={String(label)}><span>{label}</span><strong>{count}</strong></div>)}
          </div>
          <a className="secondary-button full link-button" href="/review">Start review session <span>→</span></a>
        </div>
        <div className="week-card">
          <p className="eyebrow">This week</p><h2>{state.progress.thisWeekMinutes} minutes of focused study</h2>
          <div className="week-bars">
            {state.progress.weeklyActivity.map((day) => (
              <div key={day.date}><span style={{ height: `${Math.max(7, Math.min(100, day.minutes))}%` }} /><small>{day.date.slice(8)}</small></div>
            ))}
          </div>
          <div className="week-card-footer"><span><strong>{state.progress.completionRate}%</strong> completion rate</span><a href="/progress">View progress →</a></div>
        </div>
        <div className="quick-actions-card">
          <p className="eyebrow">Shortcuts</p><h2>Quick actions</h2>
          <a href="/ielts"><span>GT</span><div><strong>IELTS G · Band 6.5</strong><small>Open authentic books and audio</small></div></a>
          <button onClick={onAddResource}><span>＋</span><div><strong>Add a resource</strong><small>Video, article or exercise</small></div></button>
          <a href="/library"><span>↗</span><div><strong>Browse the library</strong><small>{state.resources.length} learning resources</small></div></a>
          <a href="/notebook"><span>✎</span><div><strong>Open the notebook</strong><small>{state.notebook.length + state.vocabulary.length} saved items</small></div></a>
        </div>
      </section>
    </div>
  );
}
