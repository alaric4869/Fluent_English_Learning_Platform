import { useCallback, useState, type FormEvent } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { EmptyState, MutationNotice, PageIntro } from "../components/PageIntro";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { NotePayload } from "../types/notebook";


type NotebookView = "notes" | "listening" | "speaking";


export function NotebookPage() {
  const [view, setView] = useState<NotebookView>("notes");
  const [filters, setFilters] = useState({ search: "", note_type: "", sentence_status: "" });
  const [showAdd, setShowAdd] = useState(false);
  const [notice, setNotice] = useState("");
  const [mutationError, setMutationError] = useState("");
  const loader = useCallback((signal: AbortSignal) => frontendApi.notebook(filters, signal), [filters]);
  const { data, error, refresh } = useApiQuery(loader);

  async function addNote(payload: NotePayload) {
    await frontendApi.createNote(payload);
    setNotice("笔记已保存到 Mistake Book。");
    setShowAdd(false);
    refresh();
  }

  async function updateSentence(sentenceId: number, practiceStatus: string) {
    setMutationError("");
    try {
      await frontendApi.updateSentenceStatus(sentenceId, practiceStatus);
      setNotice("听力句子状态已更新。");
      refresh();
    } catch (reason) {
      setMutationError(reason instanceof Error ? reason.message : "更新失败。");
    }
  }

  return <AppShell activePage="notebook"><div className="page-container">
    <PageIntro eyebrow="Personal mistake system" title="Notebook" description="把词汇、实用表达、听力问题、发音和口语错误集中在一个可搜索的长期档案中。" actions={<button className="primary-button" onClick={() => setShowAdd((value) => !value)}>＋ Add note</button>} />
    {showAdd && <NoteForm onSubmit={addNote} onCancel={() => setShowAdd(false)} />}
    <MutationNotice message={notice} error={mutationError} />

    <section className="surface-panel notebook-toolbar">
      <div className="segmented-tabs">{(["notes", "listening", "speaking"] as NotebookView[]).map((item) => <button className={view === item ? "active" : ""} key={item} onClick={() => setView(item)}>{item}<span>{data?.counts[item === "listening" ? "sentences" : item === "speaking" ? "retellings" : "notes"] ?? 0}</span></button>)}</div>
      <div className="filter-grid three-columns">
        <label className="field compact-field"><span>Search</span><input value={filters.search} onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder="Search your learning record…" /></label>
        {view === "notes" && <label className="field compact-field"><span>Note type</span><select value={filters.note_type} onChange={(event) => setFilters((current) => ({ ...current, note_type: event.target.value }))}><option value="">All note types</option>{["vocabulary", "useful_expression", "listening_mistake", "pronunciation", "grammar", "speaking_mistake", "sentence"].map((value) => <option key={value}>{value}</option>)}</select></label>}
        {view === "listening" && <label className="field compact-field"><span>Status</span><select value={filters.sentence_status} onChange={(event) => setFilters((current) => ({ ...current, sentence_status: event.target.value }))}><option value="">All statuses</option>{["could_not_hear", "difficult", "understood", "mastered"].map((value) => <option key={value}>{value}</option>)}</select></label>}
      </div>
    </section>

    {error && <ErrorState message={error} />}{!data && !error && <LoadingState />}
    {data && view === "notes" && (data.notes.length ? <div className="notebook-grid">{data.notes.map((item) => <article className="note-card surface-panel" key={item.id}><div className="review-meta"><span>{item.type_label}</span><span>{formatDate(item.created_at)}</span></div><h2>{item.title}</h2><p className="pre-wrap">{item.content}</p>{item.source_context && <small>Source · {item.source_context}</small>}<div className="tag-list">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div></article>)}</div> : <EmptyState title="还没有个人笔记">记录一次真实错误，比收集大量没有上下文的单词更有价值。</EmptyState>)}
    {data && view === "listening" && (data.sentences.length ? <div className="review-stack">{data.sentences.map((item) => <article className="sentence-card surface-panel" key={item.id}><div><div className="review-meta"><span>{item.status_label}</span>{item.next_review_date && <span>Review {item.next_review_date}</span>}</div><h2>{item.sentence}</h2>{item.meaning && <strong>{item.meaning}</strong>}{item.note && <p>{item.note}</p>}<small>Source · {item.source_context || "手动添加"}</small></div><label className="field compact-field sentence-status"><span>Practice status</span><select value={item.practice_status} onChange={(event) => updateSentence(item.id, event.target.value)}>{["could_not_hear", "difficult", "understood", "mastered"].map((value) => <option key={value}>{value}</option>)}</select></label></article>)}</div> : <EmptyState title="还没有听力难句">在精听工作区把听不清或困难的句子保存到这里。</EmptyState>)}
    {data && view === "speaking" && (data.retellings.length ? <div className="review-stack">{data.retellings.map((item) => <article className="retelling-card surface-panel" key={item.id}><div className="review-meta"><span>{item.status_label}</span><span>{formatDate(item.created_at)}</span></div><h2>{item.prompt}</h2>{item.written_outline && <div><p className="eyebrow">Outline</p><p className="pre-wrap">{item.written_outline}</p></div>}{item.retelling_text && <div><p className="eyebrow">Retelling</p><p className="pre-wrap">{item.retelling_text}</p></div>}{item.mistakes && <div className="mistake-block"><p className="eyebrow">Mistakes</p><p className="pre-wrap">{item.mistakes}</p></div>}{item.improved_version && <div className="improved-block"><p className="eyebrow">Improved version</p><p className="pre-wrap">{item.improved_version}</p></div>}</article>)}</div> : <EmptyState title="还没有复述记录">完成 Speaking / Retelling 工作区后，提纲、错误和改进版本会出现在这里。</EmptyState>)}
  </div></AppShell>;
}


function NoteForm({ onSubmit, onCancel }: { onSubmit: (payload: NotePayload) => Promise<void>; onCancel: () => void }) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const values = new FormData(event.currentTarget); setSaving(true); setError("");
    try { await onSubmit({ note_type: String(values.get("note_type") ?? "sentence"), title: String(values.get("title") ?? ""), content: String(values.get("content") ?? ""), source_resource_id: null, source_context: String(values.get("source_context") ?? ""), tags: String(values.get("tags") ?? "").split(",").map((value) => value.trim()).filter(Boolean) }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save note."); }
    finally { setSaving(false); }
  }
  return <form className="form-panel" onSubmit={submit}><div className="section-heading compact-heading"><div><p className="eyebrow">New notebook entry</p><h2>记录值得回看的内容</h2></div><button type="button" className="icon-button" onClick={onCancel}>关闭</button></div><div className="form-grid"><label className="field">Type<select name="note_type">{["vocabulary", "useful_expression", "listening_mistake", "pronunciation", "grammar", "speaking_mistake", "sentence"].map((value) => <option key={value}>{value}</option>)}</select></label><label className="field">Source context<input name="source_context" /></label><label className="field span-2">Title<input name="title" required /></label><label className="field span-2">Content<textarea name="content" required rows={5} /></label><label className="field span-2">Tags<input name="tags" placeholder="pronunciation, phone calls" /></label></div>{error && <p className="mutation-notice error">{error}</p>}<div className="form-actions"><button className="primary-button" disabled={saving}>{saving ? "Saving…" : "Save note"}</button></div></form>;
}


function formatDate(value: string) { return new Date(value).toLocaleDateString("en-AU", { day: "2-digit", month: "short", year: "numeric" }); }
