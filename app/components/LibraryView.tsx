"use client";

import { useMemo, useState } from "react";
import type { AppAction, AppStateDto, LearningResourceDto, ResourceType } from "../../modules/shared/contracts";
import { Modal, ModuleMark } from "./ui";

const FILTERS: Array<{ label: string; value: "all" | ResourceType | "favorites" }> = [
  { label: "All resources", value: "all" },
  { label: "Listening", value: "listening" },
  { label: "Speaking", value: "speaking" },
  { label: "Reading", value: "reading" },
  { label: "Vocabulary / Chunks", value: "vocabulary" },
  { label: "Pronunciation", value: "pronunciation" },
  { label: "Grammar", value: "grammar" },
  { label: "IELTS / PTE", value: "ielts_pte" },
  { label: "Australian English", value: "australian_english" },
  { label: "Favorites", value: "favorites" },
];

export function LibraryView({ state, onAction, onEdit, onAdd }: {
  state: AppStateDto;
  onAction: (action: AppAction) => Promise<boolean>;
  onEdit: (resource: LearningResourceDto) => void;
  onAdd: () => void;
}) {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["value"]>("all");
  const [search, setSearch] = useState("");
  const [difficulty, setDifficulty] = useState("all");
  const [sort, setSort] = useState("recommended");
  const [selected, setSelected] = useState<LearningResourceDto | null>(null);

  const resources = useMemo(() => {
    const query = search.trim().toLowerCase();
    return state.resources
      .filter((resource) => filter === "all" || (filter === "favorites" ? resource.isFavorite : resource.type === filter))
      .filter((resource) => difficulty === "all" || resource.difficulty === difficulty)
      .filter((resource) => !query || [resource.title, resource.topic, resource.source, ...resource.tags].join(" ").toLowerCase().includes(query))
      .sort((a, b) => sort === "recent" ? b.createdAt.localeCompare(a.createdAt) : sort === "studied" ? (b.lastStudiedAt ?? "").localeCompare(a.lastStudiedAt ?? "") : b.priority - a.priority);
  }, [state.resources, filter, search, difficulty, sort]);

  return (
    <div className="page-wrap">
      <section className="page-title-row library-title">
        <div><p className="eyebrow">Your permanent learning collection</p><h1>Resource library</h1><p>Find the right material by skill, topic and level—or add your own.</p></div>
        <button className="primary-button" onClick={onAdd}>＋ Add resource</button>
      </section>
      <div className="library-toolbar">
        <label className="search-box"><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search resources, topics or tags…" /></label>
        <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)} aria-label="Filter by difficulty"><option value="all">All levels</option><option value="foundation">Foundation</option><option value="comfortable">Comfortable</option><option value="stretch">Stretch</option></select>
        <select value={sort} onChange={(event) => setSort(event.target.value)} aria-label="Sort resources"><option value="recommended">Recommended</option><option value="recent">Recently added</option><option value="studied">Recently studied</option></select>
      </div>
      <div className="filter-tabs" role="tablist">{FILTERS.map((item) => <button role="tab" aria-selected={filter === item.value} className={filter === item.value ? "active" : ""} key={item.value} onClick={() => setFilter(item.value)}>{item.label}</button>)}</div>
      <div className="library-result-line"><span>{resources.length} resources</span><small>Chosen to support practical, real-world English</small></div>
      <div className="resource-grid">
        {resources.map((resource) => (
          <article className="resource-card" key={resource.id}>
            <div className="resource-card-head"><ModuleMark module={resource.module} /><button className={`favorite-button ${resource.isFavorite ? "active" : ""}`} aria-label={resource.isFavorite ? "Remove from favorites" : "Add to favorites"} onClick={() => void onAction({ type: "toggle_resource_favorite", resourceId: resource.id })}>♡</button></div>
            <div className="resource-meta"><span>{resource.type.replace("_", " / ")}</span><i>·</i><span>{resource.durationMinutes} min</span><i>·</i><span>{resource.difficulty}</span></div>
            <h3>{resource.title}</h3><p>{resource.content.summary}</p>
            <div className="tag-row">{resource.tags.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}</div>
            <div className="resource-card-footer"><span>{resource.lastStudiedAt ? "Studied before" : "Fresh material"}</span><button onClick={() => setSelected(resource)}>View resource →</button></div>
          </article>
        ))}
      </div>
      {selected && (
        <Modal title={selected.title} eyebrow={`${selected.topic} · ${selected.difficulty}`} onClose={() => setSelected(null)} wide>
          <div className="resource-detail">
            <div className="resource-detail-main"><p className="lead-copy">{selected.content.summary}</p>
              {selected.content.transcript && <div className="detail-paper"><p className="eyebrow">Transcript</p><p>{selected.content.transcript}</p></div>}
              {selected.content.article && <div className="detail-paper"><p className="eyebrow">Article</p><p>{selected.content.article}</p></div>}
              {selected.content.chunks && <div className="chunk-list">{selected.content.chunks.map((chunk) => <div className="chunk-row" key={chunk.phrase}><div><strong>{chunk.phrase}</strong><span>{chunk.meaning}</span><p>{chunk.example}</p></div></div>)}</div>}
            </div>
            <aside className="resource-detail-aside"><div><span>Source</span><strong>{selected.source}</strong></div><div><span>Duration</span><strong>{selected.durationMinutes} minutes</strong></div><div><span>Plan module</span><strong>{selected.module}</strong></div>{selected.url && <a className="primary-button full link-button" target="_blank" rel="noreferrer" href={selected.url}>Open source ↗</a>}
              {selected.source !== "Everyday English Lab" && <><button className="secondary-button full" onClick={() => { onEdit(selected); setSelected(null); }}>Edit resource</button><button className="danger-text" onClick={async () => { if (await onAction({ type: "archive_resource", resourceId: selected.id })) setSelected(null); }}>Archive resource</button></>}
            </aside>
          </div>
        </Modal>
      )}
    </div>
  );
}
