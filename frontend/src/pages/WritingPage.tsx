import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { ApiRequestError, frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { WritingDraftPayload } from "../types/practice";


const EMPTY_DRAFT: WritingDraftPayload = { response_text: "", outline: "", active_duration_seconds: 0, perceived_difficulty: null, confidence: null };


export function WritingPage({ resourceId }: { resourceId: number }) {
  const loader = useCallback((signal: AbortSignal) => frontendApi.writingWorkspace(resourceId, signal), [resourceId]);
  const { data, error } = useApiQuery(loader);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);
  const [saveState, setSaveState] = useState("尚未保存");
  const [notice, setNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const draftRef = useRef(draft);
  const secondsRef = useRef(0);
  const saveTimer = useRef<number | null>(null);
  const saveQueue = useRef<Promise<void>>(Promise.resolve());

  useEffect(() => {
    if (!data) return;
    const initial = { response_text: data.draft.response_text, outline: data.draft.outline, active_duration_seconds: data.draft.active_duration_seconds, perceived_difficulty: data.draft.perceived_difficulty, confidence: data.draft.confidence };
    draftRef.current = initial;
    secondsRef.current = initial.active_duration_seconds;
    setDraft(initial);
    setSeconds(initial.active_duration_seconds);
    setSaveState(data.draft.id ? (data.draft.status === "submitted" ? `第 ${data.draft.submission_revision} 版已提交` : "草稿已保存") : "尚未保存");
  }, [data]);

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => setSeconds((value) => {
      secondsRef.current = value + 1;
      return value + 1;
    }), 1000);
    return () => window.clearInterval(timer);
  }, [running]);
  useEffect(() => () => { if (saveTimer.current) window.clearTimeout(saveTimer.current); }, []);

  const wordCount = useMemo(() => countWords(draft.response_text), [draft.response_text]);

  function change(patch: Partial<WritingDraftPayload>) {
    const next = { ...draftRef.current, ...patch };
    draftRef.current = next;
    setDraft(next);
    setSaveState("等待自动保存…");
    setNotice("");
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => void persist().catch(() => undefined), 700);
  }

  function persist() {
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = null;
    const snapshot = { ...draftRef.current, active_duration_seconds: secondsRef.current };
    setSaveState("正在保存…");
    const operation = saveQueue.current.catch(() => undefined).then(async () => {
      await frontendApi.saveWritingDraft(resourceId, snapshot);
      setSaveState("草稿已保存");
    });
    saveQueue.current = operation.catch(() => setSaveState("保存失败"));
    return operation;
  }

  async function submit() {
    setSubmitting(true);
    setRunning(false);
    setNotice("");
    try {
      await persist();
      await saveQueue.current;
      const result = await frontendApi.submitWriting(resourceId);
      setSaveState(`第 ${result.submission_revision} 版已提交`);
      setNotice(`写作已提交：${result.word_count} 词，学习记录已更新。`);
    } catch (reason) {
      setNotice(reason instanceof ApiRequestError ? reason.message : "提交失败，请检查后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  if (error) return <AppShell activePage="ielts"><ErrorState message={error} /></AppShell>;
  if (!data) return <AppShell activePage="ielts"><LoadingState /></AppShell>;
  return (
    <AppShell activePage="ielts" plannedMinutes={data.recommended_minutes}>
      <div className="page-container practice-form-page">
        <header className="practice-form-header surface-panel">
          <div><a className="back-link" href="/ielts">← 返回 IELTS G</a><p className="eyebrow">Cambridge 20 · Test {data.test_number}</p><h1>{data.task_type}</h1><p>{data.instructions} · 至少 {data.minimum_words} 词</p></div>
          <ActiveTimer seconds={seconds} running={running} targetMinutes={data.recommended_minutes} onToggle={() => { setRunning((value) => !value); if (running) void persist(); }} />
        </header>
        <div className="writing-react-grid">
          <article className="writing-task-card surface-panel">
            <p className="eyebrow">Official task · Web text</p>
            {data.situation && <p className="writing-situation">{data.situation}</p>}
            <p className="writing-prompt">{data.prompt}</p>
            {data.bullet_points.length > 0 && <ul>{data.bullet_points.map((point) => <li key={point}>{point}</li>)}</ul>}
            {data.closing_instruction && <p>{data.closing_instruction}</p>}
            <div className="writing-requirement"><span>WORD REQUIREMENT</span><strong>Write at least {data.minimum_words} words.</strong></div>
          </article>
          <section className="writing-editor-card-react surface-panel">
            <header><div><p className="eyebrow">Your response</p><h2>Plan, write, revise.</h2></div><div className="writing-count"><strong>{wordCount}</strong><span>/ {data.minimum_words} words</span></div></header>
            <div className="writing-progress"><span style={{ width: `${Math.min(100, wordCount / data.minimum_words * 100)}%` }} /></div>
            <label className="practice-text-field"><span>OUTLINE / KEY IDEAS</span><textarea rows={5} maxLength={12000} value={draft.outline} onChange={(event) => change({ outline: event.target.value })} placeholder="先写要点、段落结构和想使用的词块…" /></label>
            <label className="practice-text-field"><span>FINAL RESPONSE</span><textarea rows={20} maxLength={30000} value={draft.response_text} onChange={(event) => change({ response_text: event.target.value })} placeholder="Write your answer here…" spellCheck /></label>
            <div className="practice-rating-grid"><Rating label="难度 Difficulty" value={draft.perceived_difficulty} onChange={(value) => change({ perceived_difficulty: value })} /><Rating label="信心 Confidence" value={draft.confidence} onChange={(value) => change({ confidence: value })} /></div>
            <footer className="practice-submit-row"><div><strong>{saveState}</strong><small>输入内容会自动保存；提交会生成不可变的学习记录版本。</small></div><button className="primary-button" disabled={submitting} onClick={submit}>{submitting ? "正在提交…" : "完整提交"}</button></footer>
            {notice && <p className="practice-notice" role="status">{notice}</p>}
            <aside className="ai-migration-note"><strong>AI feedback</strong><p>写作 AI 结构化反馈将在 M23 接入 React；当前草稿、字数、计时、提交和学习证据已经完整可用。</p></aside>
          </section>
        </div>
      </div>
    </AppShell>
  );
}


export function ActiveTimer({ seconds, running, targetMinutes, onToggle }: { seconds: number; running: boolean; targetMinutes: number; onToggle: () => void }) {
  return <div className="active-timer"><small>ACTIVE TIME · TARGET {targetMinutes} MIN</small><strong>{formatSeconds(seconds)}</strong><button className="secondary-button" onClick={onToggle}>{running ? "暂停计时" : seconds ? "继续计时" : "开始计时"}</button></div>;
}


export function Rating({ label, value, onChange }: { label: string; value: number | null; onChange: (value: number | null) => void }) {
  return <label><span>{label}</span><select value={value ?? ""} onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)}><option value="">暂不评分</option>{[1,2,3,4,5].map((item) => <option value={item} key={item}>{item} / 5</option>)}</select></label>;
}


function countWords(value: string) { return value.trim().match(/\b[\p{L}\p{N}_]+(?:['’-][\p{L}\p{N}_]+)*\b/gu)?.length ?? 0; }
function formatSeconds(value: number) { return `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`; }
