import { useCallback, useState, type FormEvent } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { EmptyState, MutationNotice, PageIntro } from "../components/PageIntro";
import { ResourceForm } from "../components/ResourceForm";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { ResourcePayload, ResourceSummary } from "../types/resources";


type LibraryView = "all" | "favorites" | "saved" | "archived";


export function LibraryPage() {
  const initial = new URLSearchParams(window.location.search);
  const [filters, setFilters] = useState({
    view: (initial.get("view") as LibraryView) || "all",
    search: initial.get("search") ?? "",
    skill: initial.get("skill") ?? "",
    resource_type: initial.get("resource_type") ?? "",
    topic: initial.get("topic") ?? "",
    difficulty: initial.get("difficulty") ?? "",
    completion: initial.get("completion") ?? "all",
    sort: initial.get("sort") ?? "recently_added",
  });
  const [showAdd, setShowAdd] = useState(initial.get("add") === "true");
  const [notice, setNotice] = useState("");
  const [mutationError, setMutationError] = useState("");
  const loader = useCallback(
    (signal: AbortSignal) => frontendApi.library(filters, signal),
    [filters],
  );
  const { data, error, refresh } = useApiQuery(loader);

  function applySearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setFilters((current) => ({ ...current, search: String(values.get("search") ?? "") }));
  }

  async function createResource(payload: ResourcePayload) {
    await frontendApi.createResource(payload);
    setShowAdd(false);
    setNotice("材料已加入永久资源库。");
    refresh();
  }

  async function toggleState(resource: ResourceSummary, key: "favorite" | "saved_for_later" | "archived") {
    setMutationError("");
    setNotice("");
    try {
      await frontendApi.updateResourceState(resource.id, { [key]: !resource[key] });
      setNotice("材料状态已更新。");
      refresh();
    } catch (reason) {
      setMutationError(reason instanceof Error ? reason.message : "更新失败。");
    }
  }

  return (
    <AppShell activePage="library">
      <div className="page-container">
        <PageIntro
          eyebrow="Permanent resource database"
          title="Resource Library"
          description="所有过去、现在和未来的学习材料都保存在这里。用筛选找到下一项合适内容，而不是依赖固定的 14 天清单。"
          actions={<button className="primary-button" onClick={() => setShowAdd((value) => !value)}>＋ Add resource</button>}
        />
        {showAdd && <ResourceForm submitLabel="保存材料" onSubmit={createResource} onCancel={() => setShowAdd(false)} />}
        <MutationNotice message={notice} error={mutationError} />

        <section className="library-toolbar surface-panel">
          <div className="segmented-tabs" aria-label="Library view">
            {data && ([
              ["all", "All", data.counts.all],
              ["favorites", "Favorites", data.counts.favorites],
              ["saved", "Saved", data.counts.saved],
              ["archived", "Archived", data.counts.archived],
            ] as const).map(([value, label, count]) => (
              <button className={filters.view === value ? "active" : ""} key={value} onClick={() => setFilters((current) => ({ ...current, view: value }))}>{label}<span>{count}</span></button>
            ))}
          </div>
          <form className="search-row" onSubmit={applySearch}>
            <input name="search" defaultValue={filters.search} placeholder="Search title, topic or tag…" />
            <button className="secondary-button">Search</button>
          </form>
          {data && (
            <div className="filter-grid">
              <Filter label="Skill" value={filters.skill} options={["", "listening", "speaking", "reading", "writing", "vocabulary"]} onChange={(skill) => setFilters((current) => ({ ...current, skill }))} />
              <Filter label="Type" value={filters.resource_type} options={["", ...data.facets.resource_types]} onChange={(resource_type) => setFilters((current) => ({ ...current, resource_type }))} />
              <Filter label="Topic" value={filters.topic} options={["", ...data.facets.topics]} onChange={(topic) => setFilters((current) => ({ ...current, topic }))} />
              <Filter label="Difficulty" value={filters.difficulty} options={["", ...data.facets.difficulties]} onChange={(difficulty) => setFilters((current) => ({ ...current, difficulty }))} />
              <Filter label="Progress" value={filters.completion} options={["all", "completed", "not_completed"]} onChange={(completion) => setFilters((current) => ({ ...current, completion }))} />
              <Filter label="Sort" value={filters.sort} options={["recently_added", "recently_studied", "title", "priority"]} onChange={(sort) => setFilters((current) => ({ ...current, sort }))} />
            </div>
          )}
        </section>

        {error && <ErrorState message={error} />}
        {!data && !error && <LoadingState />}
        {data && (
          <section>
            <div className="result-heading"><strong>{data.total_count} resources</strong><span>Structured for daily rotation and future AI recommendations</span></div>
            {data.items.length === 0 ? (
              <EmptyState title="没有符合筛选条件的材料">尝试清除筛选，或添加自己的视频、音频和文章。</EmptyState>
            ) : (
              <div className="resource-grid">
                {data.items.map((resource) => (
                  <article className="resource-card" key={resource.id}>
                    <div className="resource-card-meta"><span>{resource.skill}</span><span>{resource.resource_type.replaceAll("_", " ")}</span></div>
                    <a href={`/library/${resource.id}`}><h2>{resource.title}</h2></a>
                    <p>{resource.description || `${resource.topic} · ${resource.difficulty ?? "difficulty not set"}`}</p>
                    <div className="tag-list">{resource.tags.slice(0, 4).map((tag) => <span key={tag}>{tag}</span>)}</div>
                    <div className="resource-card-stats"><span>{resource.estimated_duration_minutes} min</span><span>{resource.completed_session_count} sessions</span></div>
                    <div className="card-actions">
                      <button className={resource.favorite ? "selected" : ""} onClick={() => toggleState(resource, "favorite")}>{resource.favorite ? "★" : "☆"} Favorite</button>
                      <button className={resource.saved_for_later ? "selected" : ""} onClick={() => toggleState(resource, "saved_for_later")}>{resource.saved_for_later ? "Saved" : "Save later"}</button>
                      <a href={`/library/${resource.id}`}>Details →</a>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </AppShell>
  );
}


function Filter({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  const emptyLabels: Record<string, string> = { Skill: "All skills", Type: "All types", Topic: "All topics", Difficulty: "All difficulties" };
  const display = (option: string) => {
    if (!option) return emptyLabels[label] ?? `All ${label.toLowerCase()}`;
    if (label === "Progress" && option === "all") return "All progress";
    return option.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  };
  return <label className="field compact-field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{display(option)}</option>)}</select></label>;
}
