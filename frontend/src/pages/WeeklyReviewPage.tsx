import { useCallback } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { PageIntro } from "../components/PageIntro";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";


export function WeeklyReviewPage() {
  const loader = useCallback((signal: AbortSignal) => frontendApi.weeklyReview(signal), []);
  const { data, error } = useApiQuery(loader);
  return <AppShell activePage="progress"><div className="page-container"><a className="back-link" href="/progress">← Back to progress</a><PageIntro eyebrow="Weekly learning review" title="Weekly Review" description="系统只根据真实完成记录、作答表现和复习历史生成结论，不用虚假的游戏化分数。" />{error && <ErrorState message={error} />}{!data && !error && <LoadingState />}{data && <><section className="weekly-hero surface-panel"><div><p className="eyebrow">{data.date_range}</p><h2>{data.study_days} study days · {data.completion_rate}% completion</h2></div><div className="weekly-highlight"><span>Strongest<strong>{data.strongest_label}</strong></span><span>Needs attention<strong>{data.weakest_label}</strong></span></div></section><section className="metric-grid weekly-metrics"><Metric label="Completed modules" value={`${data.completed_modules}/${data.assigned_modules}`} /><Metric label="Planned study time" value={`${data.completed_planned_minutes} min`} /><Metric label="Measured sessions" value={String(data.completed_sessions)} /><Metric label="Vocabulary learned" value={String(data.vocabulary_learned)} /><Metric label="Difficult sentences" value={String(data.difficult_sentences_collected)} /><Metric label="Review retention" value={data.review_attempts.retention_rate === null ? "—" : `${data.review_attempts.retention_rate}%`} /></section><section className="skill-progress-grid weekly-skills">{data.skills.map((skill) => <article className="skill-progress-card surface-panel" key={skill.skill}><div className="skill-progress-head"><span>{skill.code}</span><div><h2>{skill.label}</h2><p>{skill.completed_sessions} sessions · {skill.incorrect_item_count} mistakes</p></div><strong>{skill.average_accuracy_percent === null ? "—" : `${skill.average_accuracy_percent}%`}</strong></div><div className="score-track"><span style={{ width: `${skill.average_accuracy_percent ?? 0}%` }} /></div></article>)}</section><section className="recommendation-panel surface-panel"><div className="section-heading"><div><p className="eyebrow">Things to review next week</p><h2>基于本周证据的行动建议</h2></div></div><div className="recommendation-list">{data.recommendations.map((item) => <a href={item.href} key={`${item.title}-${item.href}`}><span>→</span><div><strong>{item.title}</strong><p>{item.reason}</p></div></a>)}</div></section></>}</div></AppShell>;
}


function Metric({ label, value }: { label: string; value: string }) { return <article className="metric-card surface-panel"><p>{label}</p><strong>{value}</strong></article>; }
