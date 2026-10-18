import { useCallback } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { PageIntro } from "../components/PageIntro";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";


export function ProgressPage() {
  const loader = useCallback((signal: AbortSignal) => frontendApi.progress(signal), []);
  const { data, error } = useApiQuery(loader);
  const maximum = Math.max(1, ...(data?.recent_activity.map((item) => item.activity_score) ?? [1]));
  return <AppShell activePage="progress"><div className="page-container"><PageIntro eyebrow="Consistency, not gamification" title="Progress" description="用真实学习天数、完成率、Session 和技能证据判断自己是否持续进步。没有证据时，系统会明确显示数据不足。" />{error && <ErrorState message={error} />}{!data && !error && <LoadingState />}{data && <><section className="metric-grid"><Metric label="Current streak" value={`${data.current_streak} days`} /><Metric label="Longest streak" value={`${data.longest_streak} days`} /><Metric label="Total study days" value={String(data.total_study_days)} /><Metric label="Completion rate" value={`${data.completion_rate}%`} /><Metric label="Study time this week" value={formatMinutes(data.this_week_completed_planned_minutes)} /><Metric label="Tracked study time" value={formatMinutes(Math.round(data.tracked_seconds / 60))} /><Metric label="Completed sessions" value={String(data.completed_sessions)} /><Metric label="Reviews completed" value={String(data.completed_reviews)} /></section><section className="surface-panel activity-panel"><div className="section-heading"><div><p className="eyebrow">Last 28 days</p><h2>Weekly / monthly activity</h2></div></div><div className="activity-chart">{data.recent_activity.map((item) => <div className="activity-column" key={item.activity_date} title={`${item.activity_date}: ${item.completed_modules} modules, ${item.completed_sessions} sessions`}><div style={{ height: `${Math.max(4, item.activity_score / maximum * 100)}%` }} className={item.activity_score ? "active" : ""} /><span>{item.activity_date.slice(8)}</span></div>)}</div></section><section className="skill-progress-grid">{data.skills.map((skill) => <article className="skill-progress-card surface-panel" key={skill.skill}><div className="skill-progress-head"><span>{skill.code}</span><div><h2>{skill.label}</h2><p>{skill.classification_label} · {skill.evidence_label}</p></div><strong>{skill.score ?? "—"}</strong></div><div className="score-track"><span style={{ width: `${skill.score ?? 0}%` }} /></div><div className="skill-progress-stats"><span>{skill.completed_modules} modules</span><span>{skill.completed_sessions} measured sessions</span></div></article>)}</section><div className="weekly-review-link surface-panel"><div><p className="eyebrow">Weekly reflection</p><h2>查看本周的强项、弱项和下周建议</h2></div><a className="primary-button" href="/weekly-review">Open weekly review</a></div></>}</div></AppShell>;
}


function Metric({ label, value }: { label: string; value: string }) { return <article className="metric-card surface-panel"><p>{label}</p><strong>{value}</strong></article>; }
function formatMinutes(value: number) { const hours = Math.floor(value / 60); const minutes = value % 60; return hours ? `${hours}h ${minutes ? `${minutes}m` : ""}` : `${minutes}m`; }
