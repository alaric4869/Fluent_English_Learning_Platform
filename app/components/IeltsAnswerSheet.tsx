"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { IeltsAttemptDto, IeltsQuestionResponseDto, IeltsSubmissionResultDto } from "../../modules/shared/contracts";
import { getIeltsExplanationRange } from "../../modules/ielts/ielts-explanation-manifest";
import { questionNumbersForSection, sectionForQuestion, type IeltsSubmittedAnswer } from "../../modules/ielts/ielts-question-bank";
import type { PracticeSelection } from "./IeltsPracticeWorkspace";
import type { LocalIeltsFile } from "../../modules/ielts/local-resource-access";
import { IeltsPdfViewer } from "./IeltsPdfViewer";

export function IeltsAnswerSheet({
  selection,
  activeSection,
  attempt,
  initialResponses,
  answerPdf,
  answerKeyAvailable,
  sourceReady,
  busy,
  onStart,
  onSave,
  onSubmit,
}: {
  selection: PracticeSelection & { skill: "listening" | "reading" };
  activeSection: number;
  attempt: IeltsAttemptDto | null;
  initialResponses: IeltsQuestionResponseDto[];
  answerPdf: LocalIeltsFile | null;
  answerKeyAvailable: boolean;
  sourceReady: boolean;
  busy: boolean;
  onStart: () => Promise<void>;
  onSave: (answers: IeltsSubmittedAnswer[]) => Promise<void>;
  onSubmit: (answers: IeltsSubmittedAnswer[], notes: string) => Promise<IeltsSubmissionResultDto>;
}) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [notes, setNotes] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const [submission, setSubmission] = useState<IeltsSubmissionResultDto | null>(null);
  const [expandedQuestion, setExpandedQuestion] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loadedAttemptId = useRef<string | null>(null);

  useEffect(() => {
    if (!attempt || loadedAttemptId.current === attempt.id) return;
    loadedAttemptId.current = attempt.id;
    setAnswers(Object.fromEntries(initialResponses.map((item) => [item.questionNumber, item.answer])));
    setSubmission(null);
    setSaveState("idle");
  }, [attempt, initialResponses]);

  const visibleQuestions = useMemo(
    () => questionNumbersForSection(selection.skill, activeSection),
    [activeSection, selection.skill],
  );
  const answeredCount = Object.values(answers).filter((answer) => answer.trim()).length;
  const unanswered = Array.from({ length: 40 }, (_, index) => index + 1).filter((number) => !answers[number]?.trim());
  const gradedByQuestion = new Map(submission?.answers.map((answer) => [answer.questionNumber, answer]) ?? []);

  function currentAnswers(numbers: number[]): IeltsSubmittedAnswer[] {
    return numbers.map((questionNumber) => ({
      questionNumber,
      sectionNumber: sectionForQuestion(selection.skill, questionNumber),
      answer: answers[questionNumber] ?? "",
    }));
  }

  async function persistQuestions(numbers: number[]) {
    setSaveState("saving");
    setError(null);
    try {
      await onSave(currentAnswers(numbers));
      setSaveState("saved");
    } catch (reason) {
      setSaveState("idle");
      setError(reason instanceof Error ? reason.message : "答案保存失败，请重试。");
    }
  }

  async function saveSection() {
    await persistQuestions(visibleQuestions);
  }

  async function submitTest() {
    setError(null);
    try {
      const result = await onSubmit(currentAnswers(Array.from({ length: 40 }, (_, index) => index + 1)), notes);
      setSubmission(result);
      setSaveState("saved");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "提交失败，请保留答案后重试。");
    }
  }

  if (!attempt && !submission) {
    const startMessage = !answerKeyAvailable
      ? "这一套的标准答案仍在校验中，暂时不能开启自动判分，避免 OCR 错字导致误判。"
      : !sourceReady
        ? "请先连接 resources 文件夹中的原题 PDF。连接后会在左侧显示题目，右侧可直接填写并保存答案。"
        : "开始后直接在这里填写答案。系统会按 Section 保存，40 题全部完成后统一判分。";
    const startLabel = !answerKeyAvailable
      ? "答案校验中"
      : !sourceReady
        ? "请先连接原题 PDF"
        : busy
          ? "正在建立答题卡…"
          : "开始在线作答 →";
    return (
      <aside className="ielts-answer-sheet answer-sheet-empty">
        <div><p className="eyebrow">Interactive answer sheet</p><h3>网页答题卡</h3><p>{startMessage}</p></div>
        <button className="primary-button" disabled={busy || !answerKeyAvailable || !sourceReady} onClick={() => void onStart()}>{startLabel}</button>
      </aside>
    );
  }

  return (
    <aside className="ielts-answer-sheet">
      <header className="answer-sheet-head">
        <div><p className="eyebrow">Interactive answer sheet</p><h3>{selection.skill === "listening" ? "Listening Part" : "Reading Section"} {activeSection}</h3></div>
        <div className="answer-progress"><strong>{submission ? `${submission.rawScore}/40` : `${answeredCount}/40`}</strong><span>{submission ? `Band ${submission.estimatedBand ?? "—"}` : "已作答"}</span></div>
      </header>

      {submission && <div className="submission-summary"><div><strong>已完成自动判分</strong><span>{submission.rawScore} 题正确 · {40 - submission.rawScore} 题需要复盘。错题精解已放在对应题目下方。</span></div><button className="secondary-button" disabled={busy} onClick={() => void onStart()}>重新练习</button></div>}
      {error && <div className="answer-sheet-error">{error}</div>}

      <div className="ielts-question-list">
        {visibleQuestions.map((questionNumber) => {
          const graded = gradedByQuestion.get(questionNumber);
          const explanationRange = getIeltsExplanationRange(selection.bookNumber, selection.testNumber, selection.skill, activeSection);
          return (
            <div className={`ielts-answer-row ${graded ? graded.isCorrect ? "correct" : "incorrect" : ""}`} key={questionNumber}>
              <label>
                <span>{questionNumber}</span>
                <input
                  aria-label={`第 ${questionNumber} 题答案`}
                  autoComplete="off"
                  disabled={Boolean(submission)}
                  placeholder="输入答案"
                  value={answers[questionNumber] ?? ""}
                  onChange={(event) => {
                    setAnswers((current) => ({ ...current, [questionNumber]: event.target.value }));
                    setSaveState("idle");
                  }}
                  onBlur={() => { if (attempt && !submission) void persistQuestions([questionNumber]); }}
                />
                {graded && <b>{graded.isCorrect ? "正确" : "错误"}</b>}
              </label>
              {graded && !graded.isCorrect && (
                <div className="wrong-answer-explanation">
                  <div><span>你的答案</span><strong>{graded.answer || "未作答"}</strong></div>
                  <div><span>正确答案</span><strong>{graded.correctAnswer}</strong></div>
                  {answerPdf && explanationRange ? (
                    <button className="explanation-toggle" onClick={() => setExpandedQuestion((current) => current === questionNumber ? null : questionNumber)}>
                      {expandedQuestion === questionNumber ? "收起 resources 精解" : `查看第 ${questionNumber} 题 resources 精解`}
                    </button>
                  ) : answerPdf ? (
                    <p>这道题的精讲页码仍在校验，请先参考正确答案。</p>
                  ) : (
                    <p>当前册精讲 PDF 尚未连接；重新选择完整 resources 文件夹后可查看原书精解。</p>
                  )}
                  {expandedQuestion === questionNumber && answerPdf && explanationRange && (
                    <div className="inline-explanation-pdf">
                      <IeltsPdfViewer file={answerPdf} pageRange={explanationRange} title={`第 ${questionNumber} 题精讲 · ${selection.skill === "listening" ? "Part" : "Section"} ${activeSection}`} compact />
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {!submission && (
        <footer className="answer-sheet-actions">
          <div className="answer-save-line"><button className="secondary-button" disabled={busy || saveState === "saving"} onClick={() => void saveSection()}>{saveState === "saving" ? "保存中…" : "保存本 Section"}</button><span>{saveState === "saved" ? "已保存" : "切换 Section 前建议保存"}</span></div>
          <label><span>错题 / 过程备注</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="可选：记录题型、拼写或时间问题" /></label>
          <button className="primary-button submit-answer-sheet" disabled={busy || unanswered.length > 0} onClick={() => void submitTest()}>{unanswered.length ? `还差 ${unanswered.length} 题` : busy ? "正在判分…" : "提交整套并自动判分"}</button>
        </footer>
      )}
    </aside>
  );
}
