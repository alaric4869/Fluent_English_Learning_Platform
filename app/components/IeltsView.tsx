"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import type { IeltsAction, IeltsAttemptDto, IeltsDashboardDto, IeltsSkill } from "../../modules/shared/contracts";
import {
  catalogFromInputFiles,
  chooseResourcesDirectory,
  hasReadPermission,
  requestReadPermission,
  restoreResourcesDirectory,
  scanResourcesDirectory,
  type BrowserDirectoryHandle,
  type LocalIeltsCatalog,
} from "../../modules/ielts/local-resource-access";
import { IeltsPracticeWorkspace, SKILL_META, type PracticeSelection } from "./IeltsPracticeWorkspace";

const BOOKS = Array.from({ length: 17 }, (_, index) => 20 - index);
const SKILLS: IeltsSkill[] = ["listening", "reading", "writing", "speaking"];

export function IeltsView() {
  const [dashboard, setDashboard] = useState<IeltsDashboardDto | null>(null);
  const [catalog, setCatalog] = useState<LocalIeltsCatalog | null>(null);
  const [storedHandle, setStoredHandle] = useState<BrowserDirectoryHandle | null>(null);
  const [selection, setSelection] = useState<PracticeSelection>({ bookNumber: 20, testNumber: 1, skill: "listening" });
  const [activeAttemptId, setActiveAttemptId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingGoal, setEditingGoal] = useState(false);
  const [examDate, setExamDate] = useState("2026-10-31");
  const [targetBand, setTargetBand] = useState("6.5");
  const directoryInput = useRef<HTMLInputElement>(null);

  const loadDashboard = useCallback(async () => {
    const response = await fetch("/api/ielts", { cache: "no-store" });
    const payload = await response.json() as IeltsDashboardDto & { error?: string };
    if (!response.ok) throw new Error(payload.error ?? "无法读取 IELTS 学习记录。");
    setDashboard(payload);
    setExamDate(payload.goal.examDate);
    setTargetBand(String(payload.goal.targetBand));
    const active = payload.attempts.find((attempt) => attempt.status === "in_progress");
    if (active) {
      setActiveAttemptId(active.id);
      setSelection({ bookNumber: active.bookNumber, testNumber: active.testNumber, skill: active.skill });
    }
  }, []);

  useEffect(() => {
    // Initial data arrives asynchronously; state updates happen only after the requests settle.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDashboard().catch((reason) => setError(reason instanceof Error ? reason.message : "IELTS 页面加载失败。"));
    void restoreResourcesDirectory().then(async (handle) => {
      if (!handle) return;
      setStoredHandle(handle);
      if (await hasReadPermission(handle)) await scanHandle(handle);
    }).catch(() => undefined);
  }, [loadDashboard]);

  const activeAttempt = dashboard?.attempts.find((attempt) => attempt.id === activeAttemptId) ?? null;
  const tests = useMemo(() => {
    const found = [...new Set(catalog?.audio.filter((file) => file.bookNumber === selection.bookNumber).map((file) => file.testNumber).filter((value): value is number => value !== null) ?? [])].sort((a, b) => a - b);
    return found.length ? found : selection.bookNumber === 12 ? [5, 6, 7, 8] : [1, 2, 3, 4];
  }, [catalog, selection.bookNumber]);

  async function scanHandle(handle: BrowserDirectoryHandle) {
    setScanning(true);
    setError(null);
    try {
      const next = await scanResourcesDirectory(handle);
      if (!next.pdfs.length) throw new Error("没有找到 G 类 PDF。请直接选择包含 ielts_paper 和 listening 的 resources 文件夹。");
      setCatalog(next);
    } finally {
      setScanning(false);
    }
  }

  async function connectFolder() {
    setError(null);
    try {
      if (storedHandle && await requestReadPermission(storedHandle)) {
        await scanHandle(storedHandle);
        return;
      }
      const handle = await chooseResourcesDirectory();
      setStoredHandle(handle);
      await scanHandle(handle);
    } catch (reason) {
      if (reason instanceof Error && reason.message === "directory_picker_unavailable") {
        directoryInput.current?.click();
        return;
      }
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      setError(reason instanceof Error ? reason.message : "无法读取本地文件夹。");
    }
  }

  function importInput(event: ChangeEvent<HTMLInputElement>) {
    if (!event.target.files?.length) return;
    const next = catalogFromInputFiles(event.target.files);
    if (!next.pdfs.length) { setError("没有找到 G 类 PDF。请选择正确的 resources 文件夹。"); return; }
    setCatalog(next);
    setError(null);
  }

  async function post(action: IeltsAction): Promise<{ attemptId?: string }> {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/ielts", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(action),
      });
      const payload = await response.json() as { error?: string; attemptId?: string };
      if (!response.ok) throw new Error(payload.error ?? "无法保存 IELTS 记录。");
      return payload;
    } finally {
      setBusy(false);
    }
  }

  async function startAttempt() {
    try {
      const result = await post({ type: "start_attempt", ...selection });
      if (result.attemptId) setActiveAttemptId(result.attemptId);
      await loadDashboard();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "无法开始练习。"); }
  }

  async function completeAttempt(result: { rawScore?: number; estimatedBand?: number; notes: string }) {
    if (!activeAttemptId) return;
    try {
      await post({ type: "complete_attempt", attemptId: activeAttemptId, ...result });
      setActiveAttemptId(null);
      await loadDashboard();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "无法保存成绩。"); }
  }

  async function saveGoal() {
    try {
      await post({ type: "save_goal", targetBand: Number(targetBand), examDate });
      await loadDashboard();
      setEditingGoal(false);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "无法保存考试目标。"); }
  }

  function selectBook(bookNumber: number) {
    const foundTests = [...new Set(catalog?.audio.filter((file) => file.bookNumber === bookNumber).map((file) => file.testNumber).filter((value): value is number => value !== null) ?? [])].sort((a, b) => a - b);
    const testNumber = foundTests[0] ?? (bookNumber === 12 ? 5 : 1);
    setSelection((value) => ({ ...value, bookNumber, testNumber }));
  }

  if (!dashboard) return <div className="app-loading"><span /><h2>正在建立你的 G 类备考计划</h2><p>读取目标与真题练习记录…</p></div>;
  const days = daysUntil(dashboard.goal.examDate);

  return (
    <div className="page-wrap ielts-page">
      <section className="ielts-goal-hero">
        <div><p className="eyebrow">IELTS General Training</p><h1>从 5–5.5 到 <em>{dashboard.goal.targetBand}</em></h1><p>你的剑桥真题将成为主训练材料。先做真实题、记录真实错误，再决定第二天练什么。</p></div>
        <div className="exam-countdown"><span>预计考试</span><strong>{Math.max(0, days)}</strong><b>天后</b><small>{formatDate(dashboard.goal.examDate)}</small><button onClick={() => setEditingGoal((value) => !value)}>修改目标</button></div>
      </section>

      {editingGoal && <section className="goal-editor"><label>目标分<select value={targetBand} onChange={(event) => setTargetBand(event.target.value)}>{Array.from({ length: 7 }, (_, index) => 6 + index * .5).map((value) => <option value={value} key={value}>{value.toFixed(1)}</option>)}</select></label><label>考试日期<input type="date" value={examDate} onChange={(event) => setExamDate(event.target.value)} /></label><button className="primary-button" disabled={busy} onClick={() => void saveGoal()}>保存目标</button></section>}
      {error && <div className="inline-error"><span>{error}</span><button onClick={() => setError(null)}>×</button></div>}

      <div className="ielts-overview-grid">
        <section className="local-library-card">
          <div className="local-library-copy"><p className="eyebrow">My authentic library</p><h2>连接你的 G 类真题库</h2><p>原书与音频只从这台电脑读取，不会上传到网站。首次使用请选择 <code>resources</code> 文件夹。</p><button className="primary-button" disabled={scanning} onClick={() => void connectFolder()}>{scanning ? "正在扫描 5.3GB 资料…" : catalog ? "重新连接文件夹" : "连接 resources 文件夹 →"}</button><input ref={directoryInput} className="visually-hidden" type="file" multiple onChange={importInput} {...({ webkitdirectory: "", directory: "" } as Record<string, string>)} /></div>
          <div className={`library-scan-status ${catalog ? "connected" : ""}`}><span>{catalog ? "✓" : "LOCAL"}</span><div><strong>{catalog ? `已连接 ${catalog.folderName}` : "等待连接"}</strong><small>{catalog ? `${catalog.pdfs.length} 本 PDF · ${catalog.totalAudioFiles} 个音频文件 · ${catalog.audio.length} 个唯一 Section` : "检测到本机已有 G4–G20 与配套听力"}</small></div></div>
        </section>
        <section className="ielts-summary-card"><p className="eyebrow">Practice evidence</p><div><strong>{dashboard.summary.completedAttempts}</strong><span>已完成练习</span></div><div><strong>{dashboard.summary.averageBand ?? "—"}</strong><span>目前平均 Band</span></div><div><strong>{dashboard.summary.completedThisWeek}</strong><span>本周完成</span></div></section>
      </div>

      <section className="ielts-plan-card">
        <div><p className="eyebrow">50-day route</p><h2>到 10 月底的备考节奏</h2></div>
        <div className="plan-phase-list">
          <Phase number="01" title="基线定位" copy="先完成一套听力 + 阅读，确定真实起点与主要丢分题型。" active={days > 42} />
          <Phase number="02" title="专项突破" copy="按错题集中训练；写作每周 3 篇，口语每周至少 4 次录音。" active={days <= 42 && days > 21} />
          <Phase number="03" title="整套限时" copy="每周 2 套完整模考，用成绩趋势决定下一套材料。" active={days <= 21 && days > 7} />
          <Phase number="04" title="考前稳定" copy="复盘错题本、维持手感，不在最后一周盲目堆新题。" active={days <= 7} />
        </div>
      </section>

      <section className="ielts-material-picker">
        <div className="section-heading"><div><p className="eyebrow">Choose authentic material</p><h2>选择今天要做的真题</h2></div><span>{catalog ? "绿色圆点表示本地文件已匹配" : "连接文件夹后即可打开原题和音频"}</span></div>
        <div className="ielts-book-strip">{BOOKS.map((book) => {
          const available = catalog?.pdfs.some((file) => file.bookNumber === book) ?? false;
          const completed = dashboard.attempts.filter((attempt) => attempt.bookNumber === book && attempt.status === "completed").length;
          return <button className={`${book === selection.bookNumber ? "active" : ""} ${available ? "available" : ""}`} key={book} disabled={Boolean(activeAttempt)} onClick={() => selectBook(book)}><span>CAMBRIDGE</span><strong>{book}</strong><small>{completed ? `${completed} 次已完成` : "General Training"}</small></button>;
        })}</div>
        <div className="ielts-selection-row">
          <label>Test<select disabled={Boolean(activeAttempt)} value={selection.testNumber} onChange={(event) => setSelection((value) => ({ ...value, testNumber: Number(event.target.value) }))}>{tests.map((test) => <option value={test} key={test}>Test {test}</option>)}</select></label>
          <div className="ielts-skill-tabs">{SKILLS.map((skill) => <button disabled={Boolean(activeAttempt)} className={selection.skill === skill ? "active" : ""} onClick={() => setSelection((value) => ({ ...value, skill }))} key={skill}><span>{SKILL_META[skill].short}</span>{SKILL_META[skill].label}</button>)}</div>
        </div>
      </section>

      <IeltsPracticeWorkspace key={`${selection.bookNumber}-${selection.testNumber}-${selection.skill}`} catalog={catalog} selection={selection} attempt={activeAttempt} busy={busy} onStart={startAttempt} onComplete={completeAttempt} />

      <div className="ielts-bottom-grid">
        <section className="ielts-score-card"><div><p className="eyebrow">Target guide</p><h2>6.5 的阶段目标</h2></div><div className="score-targets"><div><span>听力</span><strong>约 26/40</strong><small>建议练到 28+ 留出波动</small></div><div><span>G 类阅读</span><strong>约 32/40</strong><small>建议练到 33–34</small></div><div><span>写作 / 口语</span><strong>稳定 6–6.5</strong><small>用评分项定位短板</small></div></div><p>听力与阅读换算为预估值；官方说明不同试卷的原始分边界可能略有变化。</p></section>
        <section className="official-links-card"><p className="eyebrow">Official practice</p><h2>官方补充材料</h2><a href="https://ielts.org/take-a-test/preparation-resources/sample-test-questions" target="_blank" rel="noreferrer"><strong>IELTS 官方样题</strong><span>打开 ↗</span></a><a href="https://takeielts.britishcouncil.org/prepare/ielts-free-practice-mock-tests" target="_blank" rel="noreferrer"><strong>British Council 免费模考</strong><span>打开 ↗</span></a></section>
      </div>

      <AttemptHistory attempts={dashboard.attempts} />
    </div>
  );
}

function Phase({ number, title, copy, active }: { number: string; title: string; copy: string; active: boolean }) {
  return <div className={active ? "active" : ""}><span>{number}</span><div><strong>{title}</strong><p>{copy}</p></div>{active && <b>现在</b>}</div>;
}

function AttemptHistory({ attempts }: { attempts: IeltsAttemptDto[] }) {
  const visible = attempts.filter((attempt) => attempt.status === "completed").slice(0, 8);
  return <section className="ielts-history-card"><div className="section-heading"><div><p className="eyebrow">Performance history</p><h2>最近真题成绩</h2></div><span>{visible.length ? "每次练习都会永久保留" : "完成第一套后，这里会出现成绩趋势"}</span></div>{visible.length ? <div className="ielts-attempt-table"><div className="table-head"><span>材料</span><span>科目</span><span>成绩</span><span>日期</span><span>记录</span></div>{visible.map((attempt) => <div key={attempt.id}><strong>剑 {attempt.bookNumber} · T{attempt.testNumber}</strong><span>{SKILL_META[attempt.skill].label}</span><b>{attempt.rawScore !== null ? `${attempt.rawScore}/40 · ` : ""}Band {attempt.estimatedBand ?? "—"}</b><time>{new Intl.DateTimeFormat("zh-CN", { month: "short", day: "numeric" }).format(new Date(attempt.completedAt ?? attempt.startedAt))}</time><p>{attempt.notes || "—"}</p></div>)}</div> : <div className="ielts-history-empty">还没有已完成的真题记录。选择 Book、Test 和科目，然后开始第一次基线测试。</div>}</section>;
}

function daysUntil(date: string): number {
  const target = Date.parse(`${date}T00:00:00+10:00`);
  const today = new Date(new Intl.DateTimeFormat("en-CA", { timeZone: "Australia/Sydney", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date()) + "T00:00:00+10:00").getTime();
  return Math.ceil((target - today) / 86_400_000);
}

function formatDate(date: string): string {
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" }).format(new Date(`${date}T00:00:00Z`));
}
