import type { ReactNode } from "react";


export function PageIntro({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <section className="page-intro">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions && <div className="page-intro-actions">{actions}</div>}
    </section>
  );
}


export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return <div className="empty-state"><strong>{title}</strong><p>{children}</p></div>;
}


export function MutationNotice({ message, error }: { message?: string; error?: string }) {
  if (!message && !error) return null;
  return <p className={`mutation-notice ${error ? "error" : "success"}`} role="status">{error ?? message}</p>;
}
