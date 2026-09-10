"use client";

import { useMemo, useState } from "react";
import type { AppStateDto, HistoryDayDto, StudyModule } from "../../modules/shared/contracts";
import { EmptyState, MODULE_META, formatDate } from "./ui";

export function HistoryView({ state }: { state: AppStateDto }) {
  const [mode, setMode] = useState<"calendar" | "list">("calendar");
  const [selected, setSelected] = useState<HistoryDayDto | null>(state.history[0] ?? null);
  const calendarDates = useMemo(() => Array.from({ length: 35 }, (_, index) => shiftDate(state.today.date, index - 34)), [state.today.date]);
  const historyMap = new Map(state.history.map((day) => [day.date, day]));

  return (
    <div className="page-wrap">
      <section className="page-title-row"><div><p className="eyebrow">A record that never disappears</p><h1>Study history</h1><p>Return to any day and see the exact materials, progress and time you recorded.</p></div><div className="segmented-control"><button className={mode === "calendar" ? "active" : ""} onClick={() => setMode("calendar")}>Calendar</button><button className={mode === "list" ? "active" : ""} onClick={() => setMode("list")}>Timeline</button></div></section>
      {state.history.length === 0 ? <EmptyState title="Your history starts today" copy="Complete a module and its study record will remain here." /> : (
        <div className="history-layout">
          <section className="history-main">
            {mode === "calendar" ? (
              <div className="calendar-card">
                <div className="calendar-head"><div><p className="eyebrow">Five-week view</p><h2>Learning activity</h2></div><span><i /> Studied</span></div>
                <div className="weekday-row">{["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => <span key={day}>{day}</span>)}</div>
                <div className="calendar-grid">{calendarDates.map((date) => {
                  const day = historyMap.get(date);
                  const percentage = day ? day.completedModules.length / Math.max(1, day.totalModules) : 0;
                  return <button className={`${day ? "has-plan" : ""} ${selected?.date === date ? "selected" : ""}`} key={date} onClick={() => day && setSelected(day)} disabled={!day}><small>{date.slice(5, 7)}</small><strong>{date.slice(8)}</strong>{day && <span style={{ opacity: 0.25 + percentage * 0.75 }} />}</button>;
                })}</div>
              </div>
            ) : (
              <div className="timeline-list">{state.history.map((day) => <button className={selected?.date === day.date ? "active" : ""} key={day.date} onClick={() => setSelected(day)}><span className="timeline-date"><strong>{day.date.slice(8)}</strong><small>{formatDate(day.date, { month: "short" })}</small></span><div><h3>{day.theme}</h3><p>{day.completedModules.length}/{day.totalModules} modules · {day.studyMinutes} minutes</p></div><span>→</span></button>)}</div>
            )}
          </section>
          {selected && <aside className="history-detail"><p className="eyebrow">{formatDate(selected.date)}</p><h2>{selected.theme}</h2><div className="history-day-summary"><div><strong>{selected.studyMinutes}</strong><span>minutes</span></div><div><strong>{selected.completedModules.length}/{selected.totalModules}</strong><span>complete</span></div></div><div className="history-module-list">{selected.planItems.map((item) => <div key={item.id}><span className={`history-check ${item.status === "completed" ? "done" : ""}`}>{item.status === "completed" ? "✓" : "·"}</span><div><strong>{MODULE_META[item.module as StudyModule].label}</strong><p>{item.title}</p></div><small>{item.targetMinutes}m</small></div>)}</div></aside>}
        </div>
      )}
    </div>
  );
}

function shiftDate(date: string, amount: number) {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day + amount)).toISOString().slice(0, 10);
}
