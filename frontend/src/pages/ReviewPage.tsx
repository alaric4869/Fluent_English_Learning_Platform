import { useCallback, useState, type FormEvent } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { EmptyState, MutationNotice, PageIntro } from "../components/PageIntro";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { ReviewRating, VocabularyPayload } from "../types/review";


export function ReviewPage() {
  const params = new URLSearchParams(window.location.search);
  const [view, setView] = useState(params.get("view") === "library" ? "library" : "due");
  const [filters, setFilters] = useState({ search: "", mastery: "", difficulty: "" });
  const [showAdd, setShowAdd] = useState(false);
  const [revealed, setRevealed] = useState<Set<number>>(new Set());
  const [notice, setNotice] = useState("");
  const [mutationError, setMutationError] = useState("");
  const loader = useCallback((signal: AbortSignal) => frontendApi.review(filters, signal), [filters]);
  const { data, error, refresh } = useApiQuery(loader);

  async function rate(reviewItemId: number, rating: ReviewRating) {
    setMutationError("");
    try {
      await frontendApi.rateReview(reviewItemId, rating);
      setNotice(`已记录 ${rating}，下次复习日期已重新计算。`);
      setRevealed((current) => {
        const next = new Set(current);
        next.delete(reviewItemId);
        return next;
      });
      refresh();
    } catch (reason) {
      setMutationError(reason instanceof Error ? reason.message : "无法记录本次复习。");
    }
  }

  async function addVocabulary(payload: VocabularyPayload) {
    await frontendApi.createVocabulary(payload);
    setNotice("新词块已保存，并自动进入间隔复习计划。");
    setShowAdd(false);
    refresh();
  }

  return (
    <AppShell activePage="review">
      <div className="page-container">
        <PageIntro
          eyebrow="Spaced repetition"
          title="Review"
          description="优先处理今天到期的词块和听力难句。Again / Hard / Good / Easy 会直接决定下一次复习日期。"
          actions={<button className="primary-button" onClick={() => setShowAdd((value) => !value)}>＋ Add chunk</button>}
        />
        {showAdd && <VocabularyForm onSubmit={addVocabulary} onCancel={() => setShowAdd(false)} />}
        <MutationNotice message={notice} error={mutationError} />

        <section className="surface-panel review-toolbar">
          <div className="segmented-tabs">
            <button className={view === "due" ? "active" : ""} onClick={() => setView("due")}>Due today <span>{data?.due_count ?? 0}</span></button>
            <button className={view === "library" ? "active" : ""} onClick={() => setView("library")}>Chunk library <span>{data?.total_count ?? 0}</span></button>
          </div>
          {view === "library" && <div className="filter-grid three-columns">
            <label className="field compact-field"><span>Search</span><input value={filters.search} onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder="Search chunks…" /></label>
            <label className="field compact-field"><span>Mastery</span><select value={filters.mastery} onChange={(event) => setFilters((current) => ({ ...current, mastery: event.target.value }))}><option value="">All states</option>{["new", "learning", "familiar", "mastered"].map((value) => <option key={value}>{value}</option>)}</select></label>
            <label className="field compact-field"><span>Difficulty</span><select value={filters.difficulty} onChange={(event) => setFilters((current) => ({ ...current, difficulty: event.target.value }))}><option value="">All difficulties</option>{["easy", "medium", "hard"].map((value) => <option key={value}>{value}</option>)}</select></label>
          </div>}
        </section>

        {error && <ErrorState message={error} />}
        {!data && !error && <LoadingState />}
        {data && view === "due" && (
          <section className="review-stack">
            {data.due_items.length === 0 ? <EmptyState title="今天的复习已经完成">可以浏览词块库，或回到 Today 开始新内容。</EmptyState> : data.due_items.map((item, index) => {
              const isRevealed = revealed.has(item.review_item_id);
              return <article className="review-item surface-panel" key={item.review_item_id}>
                <div className="review-index">{String(index + 1).padStart(2, "0")}</div>
                <div className="review-content">
                  <div className="review-meta"><span>{item.target_label}</span><span>{item.mastery_status}</span><span>{item.due_label}</span></div>
                  <h2>{item.title}</h2>
                  <p>{item.secondary_text}</p>
                  <small>Source · {item.source_title}</small>
                  {!isRevealed ? (
                    <button className="secondary-button reveal-button" onClick={() => setRevealed((current) => new Set(current).add(item.review_item_id))}>Show answer</button>
                  ) : (
                    <div className="review-answer">
                      <p className="eyebrow">{item.answer_label}</p><strong>{item.answer}</strong>{item.note && <p>{item.note}</p>}
                      <div className="rating-row">
                        {(["again", "hard", "good", "easy"] as ReviewRating[]).map((rating) => <button className={`rating-${rating}`} key={rating} onClick={() => rate(item.review_item_id, rating)}>{rating}</button>)}
                      </div>
                    </div>
                  )}
                </div>
              </article>;
            })}
          </section>
        )}
        {data && view === "library" && (
          <section>
            <div className="result-heading"><strong>{data.total_count} chunks · {data.mastered_count} mastered</strong><span>Focus on reusable phrases, not isolated words</span></div>
            {data.library_items.length === 0 ? <EmptyState title="还没有词块">保存一个完整表达，它会自动进入复习队列。</EmptyState> : <div className="vocabulary-grid">{data.library_items.map((item) => <article className="vocabulary-card surface-panel" key={item.id}><div className="review-meta"><span>{item.mastery_status}</span><span>{item.difficulty}</span><span>Review {item.next_review_date}</span></div><h2>{item.chunk}</h2><strong>{item.meaning}</strong>{item.example_sentence && <blockquote>{item.example_sentence}</blockquote>}<small>Source · {item.source_title}</small>{item.tags.length > 0 && <div className="tag-list">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>}</article>)}</div>}
          </section>
        )}
      </div>
    </AppShell>
  );
}


function VocabularyForm({ onSubmit, onCancel }: { onSubmit: (payload: VocabularyPayload) => Promise<void>; onCancel: () => void }) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setSaving(true);
    setError("");
    try {
      await onSubmit({
        chunk: String(values.get("chunk") ?? ""),
        meaning: String(values.get("meaning") ?? ""),
        example_sentence: String(values.get("example_sentence") ?? ""),
        personal_note: String(values.get("personal_note") ?? ""),
        difficulty: String(values.get("difficulty") ?? "medium") as VocabularyPayload["difficulty"],
        source_resource_id: null,
        source_context: String(values.get("source_context") ?? ""),
        tags: String(values.get("tags") ?? "").split(",").map((value) => value.trim()).filter(Boolean),
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to add this chunk.");
    } finally {
      setSaving(false);
    }
  }

  return <form className="form-panel" onSubmit={submit}><div className="section-heading compact-heading"><div><p className="eyebrow">New review item</p><h2>保存完整词块</h2></div><button className="icon-button" type="button" onClick={onCancel}>关闭</button></div><div className="form-grid"><label className="field span-2">Word / chunk<input name="chunk" required placeholder="Would it be possible to reschedule…?" /></label><label className="field span-2">Meaning<input name="meaning" required /></label><label className="field span-2">Example sentence<textarea name="example_sentence" rows={2} /></label><label className="field">Difficulty<select name="difficulty" defaultValue="medium"><option>easy</option><option>medium</option><option>hard</option></select></label><label className="field">Source context<input name="source_context" /></label><label className="field span-2">Personal note<textarea name="personal_note" rows={2} /></label><label className="field span-2">Tags<input name="tags" placeholder="appointment, daily life" /></label></div>{error && <p className="mutation-notice error">{error}</p>}<div className="form-actions"><button className="primary-button" disabled={saving}>{saving ? "Saving…" : "Save and schedule review"}</button></div></form>;
}
