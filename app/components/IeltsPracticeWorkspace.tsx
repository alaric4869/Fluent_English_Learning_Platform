"use client";

import { useEffect, useMemo, useState } from "react";
import type { IeltsAttemptDto, IeltsSkill } from "../../modules/shared/contracts";
import type { LocalIeltsCatalog, LocalIeltsFile } from "../../modules/ielts/local-resource-access";
import { estimateIeltsBand } from "../../modules/ielts/ielts-score";
import { IeltsTimer } from "./IeltsTimer";

const SKILL_META: Record<IeltsSkill, { label: string; short: string; minutes: number; instruction: string }> = {
  listening: { label: "听力 Listening", short: "LI", minutes: 30, instruction: "按正式考试连续完成 4 个 Part，共 40 题。做完后再核对答案，把错题按原因分类。" },
  reading: { label: "阅读 Reading", short: "RE", minutes: 60, instruction: "G 类阅读 3 个 Section、40 题、60 分钟。不要边做边查词，先完成整套再精读。" },
  writing: { label: "写作 Writing", short: "WR", minutes: 60, instruction: "Task 1 信件建议 20 分钟、至少 150 词；Task 2 议论文建议 40 分钟、至少 250 词。" },
  speaking: { label: "口语 Speaking", short: "SP", minutes: 14, instruction: "按 Part 1、Part 2、Part 3 完成。建议录音；结束后记录停顿、重复和想说却没说出的表达。" },
};

export interface PracticeSelection { bookNumber: number; testNumber: number; skill: IeltsSkill }

export function IeltsPracticeWorkspace({ catalog, selection, attempt, busy, onStart, onComplete }: {
  catalog: LocalIeltsCatalog | null;
  selection: PracticeSelection;
  attempt: IeltsAttemptDto | null;
  busy: boolean;
  onStart: () => Promise<void>;
  onComplete: (result: { rawScore?: number; estimatedBand?: number; notes: string }) => Promise<void>;
}) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState(1);
  const [rawScore, setRawScore] = useState("");
  const [band, setBand] = useState("6.0");
  const [notes, setNotes] = useState("");
  const meta = SKILL_META[selection.skill];
  const pdf = catalog?.pdfs.find((file) => file.bookNumber === selection.bookNumber) ?? null;
  const audio = useMemo(() => catalog?.audio.filter((file) =>
    file.bookNumber === selection.bookNumber && file.testNumber === selection.testNumber,
  ) ?? [], [catalog, selection.bookNumber, selection.testNumber]);
  const selectedAudio = audio.find((file) => file.sectionNumber === activeSection) ?? null;
  const resetKey = `${selection.bookNumber}-${selection.testNumber}-${selection.skill}`;

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    void fileUrl(pdf).then((url) => {
      if (!active) { if (url) URL.revokeObjectURL(url); return; }
      objectUrl = url;
      setPdfUrl(url);
    });
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); setPdfUrl(null); };
  }, [pdf]);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    void fileUrl(selectedAudio).then((url) => {
      if (!active) { if (url) URL.revokeObjectURL(url); return; }
      objectUrl = url;
      setAudioUrl(url);
    });
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); setAudioUrl(null); };
  }, [selectedAudio]);

  const numericRaw = rawScore === "" ? null : Number(rawScore);
  const estimated = numericRaw !== null && Number.isInteger(numericRaw) && numericRaw >= 0 && numericRaw <= 40
    ? estimateIeltsBand(selection.skill, numericRaw)
    : null;
  const canStart = Boolean(pdf && (selection.skill !== "listening" || audio.length === 4));

  return (
    <section className="ielts-workspace-card">
      <header className="ielts-workspace-head">
        <div><p className="eyebrow">Practice workspace</p><h2>剑桥 {selection.bookNumber} · Test {selection.testNumber} · {meta.label}</h2><p>{meta.instruction}</p></div>
        <IeltsTimer key={resetKey} minutes={meta.minutes} />
      </header>

      {selection.skill === "listening" && (
        <div className="ielts-audio-panel">
          <div className="audio-part-tabs">
            {[1, 2, 3, 4].map((section) => {
              const available = audio.some((file) => file.sectionNumber === section);
              return <button className={section === activeSection ? "active" : ""} disabled={!available} key={section} onClick={() => setActiveSection(section)}>Part {section}{available ? "" : " · 缺失"}</button>;
            })}
          </div>
          {/* Timed captions are unavailable in the supplied source files; the book contains the transcript. */}
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          {audioUrl ? <audio className="ielts-native-audio" controls preload="metadata" src={audioUrl} /> : <p className="ielts-media-empty">连接 resources 文件夹后，这里会播放对应 Test 的真实录音。</p>}
          <p className="local-file-name">{selectedAudio?.path ?? `${audio.length}/4 个音频已匹配`}</p>
        </div>
      )}

      <div className="ielts-document-panel">
        {pdfUrl ? <iframe title={`Cambridge IELTS General Training ${selection.bookNumber}`} src={pdfUrl} /> : (
          <div className="ielts-document-empty"><span>PDF</span><h3>试题书尚未连接</h3><p>点击页面上方“连接 resources 文件夹”，选择你已上传资料所在的文件夹。</p></div>
        )}
      </div>

      <footer className="ielts-result-panel">
        {!attempt ? (
          <div><div><strong>准备好后记录这次练习</strong><p>系统会保存 Book、Test、科目、开始时间、成绩和错题笔记。</p></div><button className="primary-button" disabled={!canStart || busy} onClick={() => void onStart()}>{busy ? "正在记录…" : "开始并记录本次练习 →"}</button></div>
        ) : (
          <form onSubmit={(event) => {
            event.preventDefault();
            const objective = selection.skill === "listening" || selection.skill === "reading";
            void onComplete({
              rawScore: objective ? Number(rawScore) : undefined,
              estimatedBand: objective ? undefined : Number(band),
              notes,
            });
          }}>
            <div className="result-fields">
              {(selection.skill === "listening" || selection.skill === "reading") ? (
                <label><span>答对题数</span><div className="score-input"><input type="number" min="0" max="40" step="1" required value={rawScore} onChange={(event) => setRawScore(event.target.value)} /><b>/ 40</b></div><small>预估 Band：{estimated ?? "—"}（不同场次边界可能略有变化）</small></label>
              ) : (
                <label><span>自评 Band</span><select value={band} onChange={(event) => setBand(event.target.value)}>{Array.from({ length: 11 }, (_, index) => 4 + index * .5).map((value) => <option key={value} value={value}>{value.toFixed(1)}</option>)}</select><small>初版先自评；后续可接入 AI 批改与语音评估。</small></label>
              )}
              <label className="result-notes"><span>错题 / 问题记录</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="例如：Section 3 地图题丢分；拼写错误；Task 2 论点展开不足……" /></label>
            </div>
            <button className="primary-button" disabled={busy}>{busy ? "保存中…" : "完成练习并保存成绩"}</button>
          </form>
        )}
      </footer>
    </section>
  );
}

async function fileUrl(file: LocalIeltsFile | null): Promise<string | null> {
  if (!file) return null;
  return URL.createObjectURL(await file.getFile());
}

export { SKILL_META };
