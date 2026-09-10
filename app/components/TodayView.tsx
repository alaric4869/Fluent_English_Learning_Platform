"use client";

import type { AppAction, AppStateDto, StudyPlanItemDto } from "../../modules/shared/contracts";
import { StudyModuleCard } from "./StudyModuleCard";
import { ProgressRing, formatDate } from "./ui";

export function TodayView({ state, onStart, onAction }: {
  state: AppStateDto;
  onStart: (item: StudyPlanItemDto) => void;
  onAction: (action: AppAction) => Promise<boolean>;
}) {
  const complete = state.today.planItems.filter((item) => item.status === "completed").length;
  const progress = Math.round((complete / state.today.planItems.length) * 100);
  return (
    <div className="page-wrap">
      <section className="page-title-row">
        <div><p className="eyebrow">{formatDate(state.today.date)} · {state.today.theme}</p><h1>Today’s study plan</h1><p>Everything you need is here. Work through one clear module at a time.</p></div>
        <div className="title-progress"><ProgressRing value={progress} size={76} /><div><strong>{complete}/4 complete</strong><span>{state.today.targetMinutes} minutes planned</span></div></div>
      </section>
      <div className="today-module-list">
        {state.today.planItems.map((item, index) => (
          <div className="today-module-row" key={item.id}>
            <span className="step-number">0{index + 1}</span>
            <StudyModuleCard item={item} onStart={onStart} onAction={onAction} detailed />
          </div>
        ))}
      </div>
      <section className="today-tip"><span>Keep it practical</span><p>If a lesson feels too hard, replace it. If you are tired, finish two modules well instead of rushing all four.</p></section>
    </div>
  );
}
