"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { AppAction, AppStateDto, LearningResourceDto, StudyPlanItemDto } from "../../modules/shared/contracts";
import { DashboardView } from "./DashboardView";
import { TodayView } from "./TodayView";
import { LibraryView } from "./LibraryView";
import { ReviewView } from "./ReviewView";
import { HistoryView } from "./HistoryView";
import { ProgressView } from "./ProgressView";
import { NotebookView } from "./NotebookView";
import { StudyWorkspace } from "./StudyWorkspace";
import { ResourceForm } from "./ResourceForm";
import { IeltsView } from "./IeltsView";

export type AppView = "dashboard" | "today" | "ielts" | "library" | "review" | "history" | "progress" | "notebook";

const NAV_ITEMS: Array<{ view: AppView; label: string; href: string; short: string }> = [
  { view: "dashboard", label: "Dashboard", href: "/", short: "01" },
  { view: "today", label: "Today", href: "/today", short: "02" },
  { view: "ielts", label: "IELTS G", href: "/ielts", short: "03" },
  { view: "library", label: "Library", href: "/library", short: "04" },
  { view: "review", label: "Review", href: "/review", short: "05" },
  { view: "history", label: "History", href: "/history", short: "06" },
  { view: "progress", label: "Progress", href: "/progress", short: "07" },
  { view: "notebook", label: "Notebook", href: "/notebook", short: "08" },
];

export function LearningApp({ view }: { view: AppView }) {
  const [state, setState] = useState<AppStateDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const [resourceEditor, setResourceEditor] = useState<LearningResourceDto | "new" | null>(null);

  const today = useMemo(() => new Intl.DateTimeFormat("en-CA", {
    timeZone: "Australia/Sydney", year: "numeric", month: "2-digit", day: "2-digit",
  }).format(new Date()), []);

  const load = useCallback(async () => {
    try {
      const response = await fetch(`/api/app?date=${today}`, { cache: "no-store" });
      const payload = await response.json() as AppStateDto & { error?: string };
      if (!response.ok) throw new Error(payload.error ?? "Unable to load the dashboard.");
      setState(payload);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load the dashboard.");
    }
  }, [today]);

  useEffect(() => {
    // The dashboard request completes asynchronously before it updates presentation state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  const runAction = useCallback(async (action: AppAction, refresh = true) => {
    setBusy(true);
    try {
      const response = await fetch("/api/actions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(action),
      });
      const payload = await response.json() as { error?: string };
      if (!response.ok) throw new Error(payload.error ?? "Unable to save this change.");
      if (refresh) await load();
      return true;
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Unable to save this change.");
      return false;
    } finally {
      setBusy(false);
    }
  }, [load]);

  const startItem = async (item: StudyPlanItemDto) => {
    setActiveItemId(item.id);
    await runAction({ type: "start_session", planItemId: item.id });
  };

  const activeItem = state?.today.planItems.find((item) => item.id === activeItemId) ?? null;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="Fluent home">
          <span className="brand-mark">F</span>
          <span><strong>Fluent</strong><small>Daily English</small></span>
        </Link>
        <nav className="main-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <Link className={view === item.view ? "active" : ""} href={item.href} key={item.view}>
              <span>{item.short}</span>{item.label}
              {item.view === "review" && state && state.dueReviews.length > 0 && <b>{state.dueReviews.length}</b>}
            </Link>
          ))}
        </nav>
        <div className="sidebar-card">
          <p className="eyebrow">Daily intention</p>
          <p>Small, focused practice creates automatic English.</p>
          <div className="mini-rule"><span /><span /><span /></div>
        </div>
        <div className="sidebar-profile">
          <span>AN</span><div><strong>IELTS General</strong><small>Target · Band 6.5</small></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="mobile-brand"><span className="brand-mark">F</span><strong>Fluent</strong></div>
          <p>{state ? `${state.today.targetMinutes} min planned` : "Preparing today…"}</p>
          <div className="topbar-actions">
            <button className="secondary-button compact" onClick={() => setResourceEditor("new")}>＋ Add resource</button>
            <span className="today-dot" aria-hidden="true" />
            <span className="top-date">Sydney · {today}</span>
          </div>
        </header>

        {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError(null)}>×</button></div>}
        {!state ? (
          <div className="app-loading"><span /><h2>Preparing your study day</h2><p>Selecting fresh material and due reviews…</p></div>
        ) : (
          <>
            {view === "dashboard" && <DashboardView state={state} onStart={startItem} onAction={runAction} onAddResource={() => setResourceEditor("new")} />}
            {view === "today" && <TodayView state={state} onStart={startItem} onAction={runAction} />}
            {view === "ielts" && <IeltsView />}
            {view === "library" && <LibraryView state={state} onAction={runAction} onEdit={setResourceEditor} onAdd={() => setResourceEditor("new")} />}
            {view === "review" && <ReviewView state={state} onAction={runAction} />}
            {view === "history" && <HistoryView state={state} />}
            {view === "progress" && <ProgressView state={state} />}
            {view === "notebook" && <NotebookView state={state} onAction={runAction} />}
          </>
        )}
      </main>

      {activeItem && state && (
        <StudyWorkspace
          item={activeItem}
          date={state.today.date}
          dueReviews={state.dueReviews}
          savedSentences={state.savedSentences}
          busy={busy}
          onAction={runAction}
          onClose={() => setActiveItemId(null)}
        />
      )}
      {resourceEditor && (
        <ResourceForm
          resource={resourceEditor === "new" ? null : resourceEditor}
          busy={busy}
          onAction={runAction}
          onClose={() => setResourceEditor(null)}
        />
      )}
    </div>
  );
}
