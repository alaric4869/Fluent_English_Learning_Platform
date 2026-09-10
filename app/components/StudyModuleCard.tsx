"use client";

import type { AppAction, StudyPlanItemDto } from "../../modules/shared/contracts";
import { MODULE_META, ModuleMark, StatusPill } from "./ui";

export function StudyModuleCard({ item, onStart, onAction, detailed = false }: {
  item: StudyPlanItemDto;
  onStart: (item: StudyPlanItemDto) => void;
  onAction: (action: AppAction) => Promise<boolean>;
  detailed?: boolean;
}) {
  return (
    <article className={`study-module-card card-${item.module} ${detailed ? "card-detailed" : ""}`}>
      <div className="module-card-top">
        <ModuleMark module={item.module} />
        <div className="module-card-heading">
          <p className="eyebrow">{MODULE_META[item.module].eyebrow}</p>
          <h3>{MODULE_META[item.module].label}</h3>
        </div>
        <span className="duration-chip">{item.targetMinutes} min</span>
      </div>
      <div className="module-material">
        <span>Today’s material</span>
        <h4>{item.resource.title}</h4>
        <p>{item.resource.content.summary}</p>
      </div>
      {detailed && (
        <div className="module-details-grid">
          <div><span>First step</span><p>{item.instructions[0]}</p></div>
          <div><span>Target</span><p>{item.objectives[0]}</p></div>
        </div>
      )}
      <div className="module-card-footer">
        <StatusPill status={item.status} />
        <div className="module-actions">
          {item.status !== "completed" && (
            <button className="text-button" onClick={() => void onAction({ type: "replace_resource", planItemId: item.id })}>Replace</button>
          )}
          <button className={item.status === "completed" ? "secondary-button compact" : "primary-button compact"} onClick={() => onStart(item)}>
            {item.status === "completed" ? "Revisit" : item.status === "in_progress" ? "Resume" : "Start"} <span>→</span>
          </button>
        </div>
      </div>
    </article>
  );
}
