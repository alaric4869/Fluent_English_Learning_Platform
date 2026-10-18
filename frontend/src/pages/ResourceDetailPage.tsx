import { useCallback, useState } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { MutationNotice } from "../components/PageIntro";
import { ResourceForm } from "../components/ResourceForm";
import { BACKEND_PAGE_URL, frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { ResourcePayload } from "../types/resources";


export function ResourceDetailPage({ resourceId }: { resourceId: number }) {
  const [editing, setEditing] = useState(false);
  const [notice, setNotice] = useState("");
  const [mutationError, setMutationError] = useState("");
  const loader = useCallback((signal: AbortSignal) => frontendApi.resource(resourceId, signal), [resourceId]);
  const { data, error, refresh } = useApiQuery(loader);

  async function update(payload: ResourcePayload) {
    await frontendApi.updateResource(resourceId, payload);
    setEditing(false);
    setNotice("材料内容已保存。");
    refresh();
  }

  async function toggle(key: "favorite" | "saved_for_later" | "archived") {
    if (!data) return;
    try {
      await frontendApi.updateResourceState(resourceId, { [key]: !data[key] });
      setNotice("材料状态已更新。");
      setMutationError("");
      refresh();
    } catch (reason) {
      setMutationError(reason instanceof Error ? reason.message : "更新失败。");
    }
  }

  const startHref = data?.start_href
    ? data.start_href.startsWith("http") ? data.start_href : `${BACKEND_PAGE_URL}${data.start_href}`
    : null;
  const startIsExternal = Boolean(data?.start_href?.startsWith("http"));

  return (
    <AppShell activePage="library" plannedMinutes={data?.estimated_duration_minutes}>
      <div className="page-container">
        <a className="back-link" href="/library">← Back to library</a>
        {error && <ErrorState message={error} />}
        {!data && !error && <LoadingState />}
        {data && <>
          <section className="detail-hero surface-panel">
            <div>
              <div className="resource-card-meta"><span>{data.skill}</span><span>{data.resource_type.replaceAll("_", " ")}</span><span>{data.difficulty ?? "unrated"}</span></div>
              <h1>{data.title}</h1>
              <p>{data.description || `${data.topic} learning resource`}</p>
              <div className="tag-list">{data.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
            </div>
            <div className="detail-actions">
              {startHref && <a className="primary-button" href={startHref} target={startIsExternal ? "_blank" : undefined} rel="noreferrer">Start learning</a>}
              <button className="secondary-button" onClick={() => toggle("favorite")}>{data.favorite ? "★ Favorited" : "☆ Favorite"}</button>
              <button className="secondary-button" onClick={() => toggle("saved_for_later")}>{data.saved_for_later ? "Saved for later" : "Save for later"}</button>
              {data.is_user_owned && <button className="secondary-button" onClick={() => setEditing((value) => !value)}>Edit</button>}
            </div>
          </section>
          <MutationNotice message={notice} error={mutationError} />
          {editing && <ResourceForm initial={data} submitLabel="保存修改" onSubmit={update} onCancel={() => setEditing(false)} />}
          <section className="detail-grid">
            <article className="surface-panel prose-panel"><p className="eyebrow">Content</p><h2>学习材料</h2><p className="pre-wrap">{data.content_text || data.description || "该材料通过外部链接或专项练习工作区提供。"}</p></article>
            <aside className="detail-sidebar">
              <article className="surface-panel"><p className="eyebrow">Metadata</p><dl className="metadata-list"><div><dt>Topic</dt><dd>{data.topic}</dd></div><div><dt>Duration</dt><dd>{data.estimated_duration_minutes} min</dd></div><div><dt>Completed</dt><dd>{data.completed_session_count} sessions</dd></div><div><dt>Priority</dt><dd>{data.priority}/100</dd></div></dl></article>
              {data.notes && <article className="surface-panel"><p className="eyebrow">Personal notes</p><p className="pre-wrap">{data.notes}</p></article>}
            </aside>
          </section>
          {data.transcript && <section className="surface-panel transcript-panel"><p className="eyebrow">Transcript</p><h2>英文文本</h2><p className="pre-wrap">{data.transcript}</p></section>}
        </>}
      </div>
    </AppShell>
  );
}
