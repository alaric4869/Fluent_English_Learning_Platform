import type { ReactNode } from "react";
import { BACKEND_PAGE_URL } from "../lib/api";


type PageKey =
  | "dashboard"
  | "today"
  | "ielts"
  | "library"
  | "review"
  | "history"
  | "progress"
  | "notebook";

const NAV_ITEMS: Array<{
  key: PageKey;
  label: string;
  number: string;
  href: string;
  migrated: boolean;
}> = [
  { key: "dashboard", label: "Dashboard", number: "01", href: "/", migrated: true },
  { key: "today", label: "Today", number: "02", href: "/today", migrated: true },
  { key: "ielts", label: "IELTS G", number: "03", href: "/ielts", migrated: true },
  { key: "library", label: "Library", number: "04", href: "/library", migrated: true },
  { key: "review", label: "Review", number: "05", href: "/review", migrated: true },
  { key: "history", label: "History", number: "06", href: "/history", migrated: true },
  { key: "progress", label: "Progress", number: "07", href: "/progress", migrated: true },
  { key: "notebook", label: "Notebook", number: "08", href: "/notebook", migrated: true },
];


export function AppShell({
  activePage,
  plannedMinutes,
  children,
}: {
  activePage: PageKey;
  plannedMinutes?: number;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Fluent home">
          <span className="brand-mark">F</span>
          <span><strong>Fluent</strong><small>Daily English</small></span>
        </a>
        <nav className="main-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <a
              className={activePage === item.key ? "active" : ""}
              href={item.migrated ? item.href : `${BACKEND_PAGE_URL}${item.href}`}
              key={item.key}
            >
              <span>{item.number}</span>{item.label}
              {!item.migrated && <small className="migration-dot" title="Legacy page during migration">•</small>}
            </a>
          ))}
        </nav>
        <div className="sidebar-card">
          <p className="eyebrow">Daily intention</p>
          <p>Small, focused practice creates automatic English.</p>
          <div className="mini-rule"><span /><span /><span /></div>
        </div>
        <div className="sidebar-profile">
          <span>AN</span>
          <div><strong>IELTS General</strong><small>Target · Band 6.5</small></div>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <div className="mobile-brand"><span className="brand-mark">F</span><strong>Fluent</strong></div>
          <p>{plannedMinutes ? `${plannedMinutes} min planned` : "Preparing today…"}</p>
          <div className="topbar-actions">
            <a className="secondary-button compact" href="/library?add=true">＋ Add resource</a>
            <span className="today-dot" aria-hidden="true" />
            <span className="top-date">Sydney · {new Date().toLocaleDateString("en-CA")}</span>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
