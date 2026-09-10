"use client";

import { useMemo, useState } from "react";
import type { AppAction, AppStateDto, NotebookEntryDto } from "../../modules/shared/contracts";
import { Modal } from "./ui";

const TYPES = ["all", "vocabulary", "expression", "listening", "pronunciation", "grammar", "speaking", "sentence"] as const;

export function NotebookView({ state, onAction }: { state: AppStateDto; onAction: (action: AppAction) => Promise<boolean> }) {
  const [type, setType] = useState<(typeof TYPES)[number]>("all");
  const [search, setSearch] = useState("");
  const [adding, setAdding] = useState(false);
  const vocabularyEntries: NotebookEntryDto[] = state.vocabulary.map((item) => ({
    id: item.id, type: "vocabulary", title: item.phrase, content: `${item.meaning}\n${item.example}`,
    sourceResourceId: item.sourceResourceId, sourceTitle: null, isFavorite: item.isFavorite, createdAt: item.dateLearned,
  }));
  const entries = useMemo(() => [...state.notebook, ...vocabularyEntries]
    .filter((entry) => type === "all" || entry.type === type)
    .filter((entry) => !search || `${entry.title} ${entry.content}`.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt)), [state.notebook, state.vocabulary, type, search]);

  return (
    <div className="page-wrap">
      <section className="page-title-row"><div><p className="eyebrow">Your personal language memory</p><h1>Notebook & mistake book</h1><p>Useful chunks, unclear sentences and corrections—always linked back to learning.</p></div><button className="primary-button" onClick={() => setAdding(true)}>＋ Add note</button></section>
      <div className="library-toolbar notebook-toolbar"><label className="search-box"><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search everything you saved…" /></label><span>{entries.length} saved items</span></div>
      <div className="filter-tabs">{TYPES.map((value) => <button className={type === value ? "active" : ""} key={value} onClick={() => setType(value)}>{value === "all" ? "All notes" : value}</button>)}</div>
      <div className="notebook-grid">{entries.map((entry) => <article className="note-card" key={`${entry.type}-${entry.id}`}><div className="note-card-top"><span>{entry.type}</span>{entry.isFavorite && <b>♡</b>}</div><h3>{entry.title}</h3><p>{entry.content}</p><div>{entry.sourceTitle ? `From ${entry.sourceTitle}` : entry.type === "vocabulary" ? "Vocabulary library" : "Personal note"}<small>{entry.createdAt.slice(0, 10)}</small></div></article>)}</div>
      {adding && <AddNoteModal resources={state.resources.map((resource) => ({ id: resource.id, title: resource.title }))} onAction={onAction} onClose={() => setAdding(false)} />}
    </div>
  );
}

function AddNoteModal({ resources, onAction, onClose }: { resources: Array<{ id: string; title: string }>; onAction: (action: AppAction) => Promise<boolean>; onClose: () => void }) {
  const [type, setType] = useState<NotebookEntryDto["type"]>("expression");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [sourceResourceId, setSourceResourceId] = useState("");
  const submit = async (event: React.FormEvent) => { event.preventDefault(); if (await onAction({ type: "add_notebook_entry", entryType: type, title, content, sourceResourceId: sourceResourceId || undefined })) onClose(); };
  return <Modal title="Add to your notebook" eyebrow="Capture it while it is useful" onClose={onClose}><form className="resource-form" onSubmit={submit}><div className="form-grid"><label>Note type<select value={type} onChange={(event) => setType(event.target.value as NotebookEntryDto["type"])}>{TYPES.filter((value) => value !== "all" && value !== "vocabulary").map((value) => <option key={value}>{value}</option>)}</select></label><label>Title<input required value={title} onChange={(event) => setTitle(event.target.value)} placeholder="What do you want to remember?" /></label><label>Source lesson<select value={sourceResourceId} onChange={(event) => setSourceResourceId(event.target.value)}><option value="">No linked lesson</option>{resources.map((resource) => <option key={resource.id} value={resource.id}>{resource.title}</option>)}</select></label><label>Note<textarea required className="large-textarea" value={content} onChange={(event) => setContent(event.target.value)} placeholder="Mistake, correction, example or explanation…" /></label></div><div className="form-actions"><button type="button" className="text-button" onClick={onClose}>Cancel</button><button className="primary-button">Save note</button></div></form></Modal>;
}
