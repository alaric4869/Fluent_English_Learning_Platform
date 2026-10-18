import { useCallback, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { EmptyState, PageIntro } from "../components/PageIntro";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { HistoryDay } from "../types/insights";


export function HistoryPage() {
  const currentMonth = new Date().toLocaleDateString("en-CA", { year: "numeric", month: "2-digit" });
  const [view, setView] = useState<"timeline" | "calendar">("timeline");
  const [month, setMonth] = useState(currentMonth);
  const loader = useCallback((signal: AbortSignal) => frontendApi.history(view, month, signal), [view, month]);
  const { data, error } = useApiQuery(loader);
  const calendar = useMemo(() => data ? buildCalendar(data.selected_month, data.days) : [], [data]);

  return <AppShell activePage="history"><div className="page-container">
    <PageIntro eyebrow="Persistent study record" title="History" description="每天的计划、材料、完成状态和真实作答都长期保留。今天的计划变化不会覆盖过去。" />
    <section className="surface-panel history-toolbar"><div className="segmented-tabs"><button className={view === "timeline" ? "active" : ""} onClick={() => setView("timeline")}>Timeline</button><button className={view === "calendar" ? "active" : ""} onClick={() => setView("calendar")}>Calendar</button></div>{view === "calendar" && <div className="month-control"><button onClick={() => data && setMonth(data.previous_month)}>←</button><strong>{data?.month_label ?? month}</strong><button onClick={() => data && setMonth(data.next_month)}>→</button></div>}</section>
    {data && <div className="history-summary"><span><strong>{data.saved_day_count}</strong> saved days</span><span><strong>{data.completed_module_count}</strong> modules completed</span><span><strong>{data.session_count}</strong> measured sessions</span></div>}
    {error && <ErrorState message={error} />}{!data && !error && <LoadingState />}
    {data && view === "timeline" && (data.days.length ? <section className="timeline-list">{data.days.map((day) => <HistoryDayCard day={day} key={day.study_date} />)}</section> : <EmptyState title="还没有学习历史">完成一个 Today 模块或 IELTS 练习后，这里会出现永久记录。</EmptyState>)}
    {data && view === "calendar" && <section className="calendar-panel surface-panel"><div className="calendar-weekdays">{["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => <span key={day}>{day}</span>)}</div><div className="calendar-grid">{calendar.map((cell, index) => cell ? <a className={`calendar-cell ${cell.record ? "has-record" : ""}`} href={cell.record ? `/history/${cell.date}` : undefined} key={cell.date}><span>{cell.day}</span>{cell.record && <><strong>{cell.record.completed_module_count}/{cell.record.assigned_module_count}</strong><small>{cell.record.sessions.length} sessions</small></>}</a> : <div className="calendar-cell blank" key={`blank-${index}`} />)}</div></section>}
  </div></AppShell>;
}


function HistoryDayCard({ day }: { day: HistoryDay }) {
  return <article className="history-day surface-panel"><div className="history-day-header"><div><p className="eyebrow">{day.study_date}</p><h2>{day.display_date}</h2></div><a className="text-link" href={`/history/${day.study_date}`}>Open full record →</a></div><div className="history-module-row">{day.modules.map((module) => <div className={module.completed ? "complete" : ""} key={module.item_id}><span>{module.code}</span><div><strong>{module.title}</strong><small>{module.resource_title}</small></div><b>{module.status.replaceAll("_", " ")}</b></div>)}</div>{day.sessions.length > 0 && <p className="session-summary">{day.sessions.length} measured session{day.sessions.length === 1 ? "" : "s"} · {day.sessions.reduce((total, item) => total + item.incorrect_item_count, 0)} recorded mistakes</p>}</article>;
}


function buildCalendar(selectedMonth: string, days: HistoryDay[]) {
  const [year, month] = selectedMonth.split("-").map(Number);
  const first = new Date(year, month - 1, 1);
  const count = new Date(year, month, 0).getDate();
  const leading = (first.getDay() + 6) % 7;
  const records = new Map(days.map((day) => [day.study_date, day]));
  const cells: Array<{ date: string; day: number; record?: HistoryDay } | null> = Array.from({ length: leading }, () => null);
  for (let day = 1; day <= count; day += 1) {
    const date = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    cells.push({ date, day, record: records.get(date) });
  }
  return cells;
}
