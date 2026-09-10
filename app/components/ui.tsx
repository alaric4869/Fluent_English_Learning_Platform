"use client";

import type { ReactNode } from "react";
import type { PlanItemStatus, StudyModule } from "../../modules/shared/contracts";

export const MODULE_META: Record<StudyModule, { label: string; short: string; eyebrow: string }> = {
  listening: { label: "Intensive listening", short: "LI", eyebrow: "Hear the missing words" },
  speaking: { label: "Shadowing + speaking", short: "SP", eyebrow: "Turn input into output" },
  reading: { label: "Focused reading", short: "RE", eyebrow: "Read for meaning" },
  vocabulary: { label: "Chunks + review", short: "CH", eyebrow: "Make useful language stick" },
};

export function ModuleMark({ module }: { module: StudyModule }) {
  return <span className={`module-mark module-${module}`}>{MODULE_META[module].short}</span>;
}

export function StatusPill({ status }: { status: PlanItemStatus }) {
  const label = status === "completed" ? "Completed" : status === "in_progress" ? "In progress" : "Not started";
  return <span className={`status-pill status-${status}`}>{status === "completed" ? "✓ " : ""}{label}</span>;
}

export function ProgressRing({ value, size = 88 }: { value: number; size?: number }) {
  return (
    <div className="progress-ring" style={{ "--progress": `${Math.max(0, Math.min(100, value)) * 3.6}deg`, width: size, height: size } as React.CSSProperties}>
      <div><strong>{value}%</strong><span>today</span></div>
    </div>
  );
}

export function Modal({ title, eyebrow, children, onClose, wide = false }: {
  title: string; eyebrow?: string; children: ReactNode; onClose: () => void; wide?: boolean;
}) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className={`modal-card ${wide ? "modal-wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}>
        <header className="modal-header">
          <div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h2>{title}</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog">×</button>
        </header>
        {children}
      </section>
    </div>
  );
}

export function EmptyState({ title, copy }: { title: string; copy: string }) {
  return <div className="empty-state"><span>✓</span><h3>{title}</h3><p>{copy}</p></div>;
}

export function formatModule(module: StudyModule) {
  return MODULE_META[module].label;
}

export function formatDate(date: string, options?: Intl.DateTimeFormatOptions) {
  const [year, month, day] = date.split("-").map(Number);
  return new Intl.DateTimeFormat("en-AU", options ?? { weekday: "long", day: "numeric", month: "long" })
    .format(new Date(Date.UTC(year, month - 1, day)));
}
