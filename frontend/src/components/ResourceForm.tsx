import { useState, type FormEvent } from "react";
import type { ResourceDetail, ResourcePayload } from "../types/resources";


const SKILLS = ["listening", "speaking", "reading", "writing", "vocabulary"];
const RESOURCE_TYPES = ["video", "audio", "podcast", "article", "exercise", "pronunciation", "grammar", "ielts", "ielts_writing", "pte", "other"];


export function ResourceForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial?: ResourceDetail;
  submitLabel: string;
  onSubmit: (payload: ResourcePayload) => Promise<void>;
  onCancel?: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const optional = (name: string) => String(values.get(name) ?? "").trim() || null;
    const payload: ResourcePayload = {
      title: String(values.get("title") ?? ""),
      resource_type: String(values.get("resource_type") ?? "other"),
      skill: String(values.get("skill") ?? "listening"),
      topic: String(values.get("topic") ?? ""),
      difficulty: optional("difficulty"),
      estimated_duration_minutes: Number(values.get("estimated_duration_minutes") ?? 20),
      source_url: optional("source_url"),
      description: String(values.get("description") ?? ""),
      content_text: String(values.get("content_text") ?? ""),
      transcript: String(values.get("transcript") ?? ""),
      notes: String(values.get("notes") ?? ""),
      tags: String(values.get("tags") ?? "").split(",").map((value) => value.trim()).filter(Boolean),
      priority: Number(values.get("priority") ?? 50),
    };
    setSaving(true);
    setError(null);
    try {
      await onSubmit(payload);
      if (!initial) form.reset();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save this resource.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form-panel" onSubmit={handleSubmit}>
      <div className="section-heading compact-heading">
        <div><p className="eyebrow">Resource editor</p><h2>{initial ? "编辑学习材料" : "添加自己的材料"}</h2></div>
        {onCancel && <button className="icon-button" type="button" onClick={onCancel}>关闭</button>}
      </div>
      <div className="form-grid">
        <label className="field span-2">标题<input name="title" required maxLength={240} defaultValue={initial?.title} /></label>
        <label className="field">技能<select name="skill" defaultValue={initial?.skill ?? "listening"}>{SKILLS.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label className="field">类型<select name="resource_type" defaultValue={initial?.resource_type ?? "video"}>{RESOURCE_TYPES.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label className="field">主题<input name="topic" required maxLength={120} defaultValue={initial?.topic} /></label>
        <label className="field">难度<input name="difficulty" maxLength={40} placeholder="intermediate" defaultValue={initial?.difficulty ?? ""} /></label>
        <label className="field">预计分钟<input name="estimated_duration_minutes" type="number" min="1" max="300" required defaultValue={initial?.estimated_duration_minutes ?? 20} /></label>
        <label className="field">优先级<input name="priority" type="number" min="0" max="100" required defaultValue={initial?.priority ?? 50} /></label>
        <label className="field span-2">URL<input name="source_url" type="url" maxLength={500} placeholder="https://…" defaultValue={initial?.source_url ?? ""} /></label>
        <label className="field span-2">简介<textarea name="description" rows={3} defaultValue={initial?.description} /></label>
        <label className="field span-2">标签（逗号分隔）<input name="tags" defaultValue={initial?.tags.join(", ")} /></label>
      </div>
      <details className="advanced-fields">
        <summary>正文、Transcript 与个人笔记</summary>
        <label className="field">正文<textarea name="content_text" rows={6} defaultValue={initial?.content_text} /></label>
        <label className="field">Transcript<textarea name="transcript" rows={6} defaultValue={initial?.transcript} /></label>
        <label className="field">个人笔记<textarea name="notes" rows={4} defaultValue={initial?.notes} /></label>
      </details>
      {error && <p className="mutation-notice error">{error}</p>}
      <div className="form-actions"><button className="primary-button" disabled={saving}>{saving ? "保存中…" : submitLabel}</button></div>
    </form>
  );
}
