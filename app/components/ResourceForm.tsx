"use client";

import { useState } from "react";
import type { AppAction, Difficulty, LearningResourceDto, ResourceType, StudyModule } from "../../modules/shared/contracts";
import { Modal } from "./ui";

export function ResourceForm({ resource, busy, onAction, onClose }: {
  resource: LearningResourceDto | null;
  busy: boolean;
  onAction: (action: AppAction) => Promise<boolean>;
  onClose: () => void;
}) {
  const [title, setTitle] = useState(resource?.title ?? "");
  const [type, setType] = useState<ResourceType>(resource?.type ?? "listening");
  const [module, setModule] = useState<StudyModule>(resource?.module ?? "listening");
  const [source, setSource] = useState(resource?.source ?? "My resource");
  const [url, setUrl] = useState(resource?.url ?? "");
  const [topic, setTopic] = useState(resource?.topic ?? "Daily life");
  const [difficulty, setDifficulty] = useState<Difficulty>(resource?.difficulty ?? "comfortable");
  const [duration, setDuration] = useState(resource?.durationMinutes ?? 25);
  const [tags, setTags] = useState(resource?.tags.join(", ") ?? "");
  const [summary, setSummary] = useState(resource?.content.summary ?? "");
  const [text, setText] = useState(resource?.content.transcript ?? resource?.content.article ?? "");

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const content = {
      ...resource?.content,
      summary,
      ...(module === "listening" ? { transcript: text, sentences: text.split(/[.!?]\s+/).filter(Boolean).slice(0, 8) } : {}),
      ...(module === "reading" ? { article: text } : {}),
    };
    const common = { title, source, url: url || null, topic, difficulty, durationMinutes: duration, tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean), content };
    const action: AppAction = resource
      ? { type: "update_resource", resourceId: resource.id, changes: common }
      : { type: "add_resource", resource: { ...common, type, module, isFavorite: false } };
    if (await onAction(action)) onClose();
  };

  return (
    <Modal title={resource ? "Edit learning resource" : "Add learning resource"} eyebrow="Resource library" onClose={onClose} wide>
      <form className="resource-form" onSubmit={submit}>
        <div className="form-grid two-columns">
          <label className="span-two">Title<input required value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Calling a medical clinic" /></label>
          <label>Resource type<select value={type} disabled={Boolean(resource)} onChange={(event) => setType(event.target.value as ResourceType)}>{["listening", "speaking", "reading", "vocabulary", "pronunciation", "grammar", "ielts_pte", "australian_english"].map((value) => <option key={value} value={value}>{value.replace("_", " / ")}</option>)}</select></label>
          <label>Plan module<select value={module} disabled={Boolean(resource)} onChange={(event) => setModule(event.target.value as StudyModule)}>{["listening", "speaking", "reading", "vocabulary"].map((value) => <option key={value}>{value}</option>)}</select></label>
          <label>Source<input value={source} onChange={(event) => setSource(event.target.value)} /></label>
          <label>URL (optional)<input type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://…" /></label>
          <label>Topic<input required value={topic} onChange={(event) => setTopic(event.target.value)} /></label>
          <label>Difficulty<select value={difficulty} onChange={(event) => setDifficulty(event.target.value as Difficulty)}><option value="foundation">Foundation</option><option value="comfortable">Comfortable</option><option value="stretch">Stretch</option></select></label>
          <label>Duration (minutes)<input type="number" min="5" max="180" value={duration} onChange={(event) => setDuration(Number(event.target.value))} /></label>
          <label>Tags<input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="Australia, phone call" /></label>
          <label className="span-two">Short summary<textarea required value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="What will this lesson help you practise?" /></label>
          <label className="span-two">Transcript or article text<textarea className="large-textarea" value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste the English transcript or reading text here…" /></label>
        </div>
        <div className="form-actions"><button type="button" className="text-button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={busy}>{busy ? "Saving…" : resource ? "Save changes" : "Add to library"}</button></div>
      </form>
    </Modal>
  );
}
