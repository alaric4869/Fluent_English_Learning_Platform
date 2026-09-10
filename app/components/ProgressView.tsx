"use client";

import type { AppStateDto } from "../../modules/shared/contracts";
import { MODULE_META } from "./ui";

export function ProgressView({ state }: { state: AppStateDto }) {
  const progress = state.progress;
  const maxMinutes = Math.max(1, ...progress.weeklyActivity.map((day) => day.minutes));
  const weakest = [...progress.skillScores].sort((a, b) => a.score - b.score)[0];
  return (
    <div className="page-wrap">
      <section className="page-title-row"><div><p className="eyebrow">Consistency over points</p><h1>Your learning progress</h1><p>Use these signals to understand your habits, strengths and next focus.</p></div><div className="progress-period">Last 7 days <span>⌄</span></div></section>
      <div className="metric-grid">
        <Metric value={`${progress.currentStreak}`} label="Current streak" note={`Longest: ${progress.longestStreak} days`} />
        <Metric value={`${Math.floor(progress.totalStudyMinutes / 60)}h ${progress.totalStudyMinutes % 60}m`} label="Total study time" note={`${progress.thisWeekMinutes} min this week`} />
        <Metric value={`${progress.completionRate}%`} label="Completion rate" note={`${progress.totalStudyDays} active days`} />
        <Metric value={`${progress.vocabularyLearned}`} label="Chunks learned" note={`${progress.vocabularyMastered} mastered`} />
      </div>
      <div className="progress-main-grid">
        <section className="chart-card"><div className="section-heading compact-heading"><div><p className="eyebrow">Weekly activity</p><h2>Focused minutes</h2></div><strong>{progress.thisWeekMinutes} min</strong></div><div className="activity-chart">{progress.weeklyActivity.map((day) => <div key={day.date}><span className="chart-value">{day.minutes || ""}</span><div><i style={{ height: `${Math.max(day.minutes ? 10 : 2, (day.minutes / maxMinutes) * 100)}%` }} /></div><small>{new Intl.DateTimeFormat("en-AU", { weekday: "short", timeZone: "UTC" }).format(new Date(`${day.date}T00:00:00Z`))}</small></div>)}</div></section>
        <section className="focus-card"><p className="eyebrow">Current focus</p><h2>{MODULE_META[weakest.module].label}</h2><span className="focus-score">{weakest.score}<small>/100</small></span><p>{weakest.sampleCount ? `Based on ${weakest.sampleCount} recent rated sessions. Keep the material comfortable enough to notice exact sentences.` : "Complete and rate two sessions in each skill to unlock adaptive planning."}</p><a href="/today">Practise this skill →</a></section>
      </div>
      <section className="skill-profile-card"><div className="section-heading compact-heading"><div><p className="eyebrow">Learner profile</p><h2>Skill balance</h2></div><span>Calculated from study activity</span></div><div className="skill-score-list">{progress.skillScores.map((skill) => <div key={skill.module}><div className="skill-label"><span>{MODULE_META[skill.module].short}</span><div><strong>{MODULE_META[skill.module].label}</strong><small>{skill.label} · {skill.sampleCount} samples</small></div></div><div className="skill-bar"><span style={{ width: `${skill.score}%` }} /></div><strong>{skill.score}</strong></div>)}</div></section>
      <section className="weekly-review-card"><div><p className="eyebrow">Weekly reflection</p><h2>Things to review next week</h2></div><ul><li>Revisit chunks that received Again or Hard.</li><li>Repeat sentences you could not hear in full.</li><li>Use one familiar topic for a 60-second retelling.</li></ul><a href="/review">Open review queue →</a></section>
    </div>
  );
}

function Metric({ value, label, note }: { value: string; label: string; note: string }) {
  return <article className="metric-card"><strong>{value}</strong><span>{label}</span><small>{note}</small></article>;
}
