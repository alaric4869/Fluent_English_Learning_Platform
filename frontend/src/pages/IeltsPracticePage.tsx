import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "../components/AppShell";
import { IeltsContentBlockView } from "../components/ielts/IeltsContentBlock";
import { IeltsQuestionList } from "../components/ielts/IeltsQuestionList";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { ApiRequestError, frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";
import type { IeltsQuestion, IeltsQuestionResult, IeltsSection } from "../types/ielts";


export function IeltsPracticePage({ slug }: { slug: string }) {
  const loader = useCallback((signal: AbortSignal) => frontendApi.ieltsWorkspace(slug, signal), [slug]);
  const { data, error } = useApiQuery(loader);
  const [activeSection, setActiveSection] = useState(1);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [results, setResults] = useState<IeltsQuestionResult[]>([]);
  const [score, setScore] = useState<number | null>(null);
  const [missing, setMissing] = useState<Set<number>>(new Set());
  const [saveStatus, setSaveStatus] = useState("答案会自动保存");
  const [submitting, setSubmitting] = useState(false);
  const answersRef = useRef<Record<number, string>>({});
  const dirtyRef = useRef<Set<number>>(new Set());
  const timersRef = useRef<Map<number, number>>(new Map());
  const saveQueueRef = useRef<Promise<void>>(Promise.resolve());

  useEffect(() => {
    if (!data) return;
    const initial = Object.fromEntries(Object.entries(data.attempt.answers).map(([number, answer]) => [Number(number), answer]));
    answersRef.current = initial;
    setAnswers(initial);
    setResults(data.attempt.results);
    setScore(data.attempt.score);
    setActiveSection(data.sections[0]?.order_index ?? 1);
  }, [data]);

  useEffect(() => () => timersRef.current.forEach((timer) => window.clearTimeout(timer)), []);

  const resultMap = useMemo(() => new Map(results.map((result) => [result.number, result])), [results]);
  const allQuestions = useMemo(() => data?.sections.flatMap((section) => section.questions) ?? [], [data]);
  const answeredCount = allQuestions.filter((question) => Boolean(answers[question.number]?.trim())).length;

  function updateAnswer(number: number, answer: string, immediate = false) {
    const next = { ...answersRef.current, [number]: answer };
    answersRef.current = next;
    dirtyRef.current.add(number);
    setAnswers(next);
    setResults([]);
    setScore(null);
    setMissing((current) => {
      const updated = new Set(current);
      updated.delete(number);
      return updated;
    });
    const previous = timersRef.current.get(number);
    if (previous) window.clearTimeout(previous);
    if (immediate) {
      timersRef.current.delete(number);
      void persistNumbers([number]);
    } else {
      timersRef.current.set(number, window.setTimeout(() => {
        timersRef.current.delete(number);
        void persistNumbers([number]);
      }, 650));
    }
  }

  function updateGroup(questions: IeltsQuestion[], selected: string[]) {
    const next = { ...answersRef.current };
    questions.forEach((question, index) => {
      next[question.number] = selected[index] ?? "";
      dirtyRef.current.add(question.number);
    });
    answersRef.current = next;
    setAnswers(next);
    setResults([]);
    setScore(null);
    setMissing((current) => {
      const updated = new Set(current);
      questions.forEach((question) => updated.delete(question.number));
      return updated;
    });
    void persistNumbers(questions.map((question) => question.number));
  }

  function persistNumbers(numbers: number[]) {
    const snapshots = numbers.map((number) => [number, answersRef.current[number] ?? ""] as const);
    setSaveStatus(`正在保存第 ${numbers.join("、")} 题…`);
    let operation = saveQueueRef.current.catch(() => undefined);
    snapshots.forEach(([number, answer]) => {
      operation = operation.then(async () => {
        await frontendApi.saveIeltsAnswer(slug, number, answer);
        if ((answersRef.current[number] ?? "") === answer) dirtyRef.current.delete(number);
      });
    });
    const completed = operation.then(() => setSaveStatus("已自动保存")).catch(() => {
      setSaveStatus("保存失败，请检查本地服务");
      throw new Error("save failed");
    });
    saveQueueRef.current = completed.catch(() => undefined);
    return completed;
  }

  async function flushAnswers() {
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current.clear();
    const dirty = [...dirtyRef.current];
    if (dirty.length) await persistNumbers(dirty);
    await saveQueueRef.current;
  }

  async function submit() {
    setSubmitting(true);
    setMissing(new Set());
    try {
      await flushAnswers();
      const response = await frontendApi.submitIelts(slug);
      setResults(response.questions);
      setScore(response.score);
      setSaveStatus("评分完成，逐题解析已显示");
      const firstWrong = response.questions.find((item) => !item.is_correct);
      if (firstWrong) jumpTo(firstWrong.number);
    } catch (reason) {
      if (reason instanceof ApiRequestError && typeof reason.body?.detail === "object") {
        const numbers = reason.body.detail.missing_questions ?? [];
        setMissing(new Set(numbers));
        setSaveStatus(`还有 ${numbers.length} 题未完成`);
        if (numbers[0]) jumpTo(numbers[0]);
      } else {
        setSaveStatus(reason instanceof Error ? reason.message : "提交失败，请稍后重试");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function jumpTo(number: number) {
    const section = data?.sections.find((item) => item.questions.some((question) => question.number === number));
    if (section) setActiveSection(section.order_index);
    window.setTimeout(() => document.getElementById(`question-${number}`)?.scrollIntoView({ behavior: "smooth", block: "center" }), 50);
  }

  if (error) return <AppShell activePage="ielts"><ErrorState message={error} /></AppShell>;
  if (!data) return <AppShell activePage="ielts"><LoadingState /></AppShell>;
  const active = data.sections.find((section) => section.order_index === activeSection) ?? data.sections[0];

  return (
    <AppShell activePage="ielts" plannedMinutes={data.duration_minutes}>
      <div className="ielts-practice-page">
        <header className="ielts-workspace-header">
          <div><a href="/ielts" className="back-link">← 返回 IELTS G</a><p className="eyebrow">Practice workspace</p><h1>剑桥 {data.book_number} · Test {data.test_number} · {data.skill === "listening" ? "听力 Listening" : "阅读 Reading"}</h1><p>{data.description}</p></div>
          <ExamTimer minutes={data.duration_minutes} />
        </header>
        <nav className="ielts-section-tabs" aria-label="题目分区">
          {data.sections.map((section) => (
            <button className={section.order_index === activeSection ? "active" : ""} key={section.id} onClick={() => setActiveSection(section.order_index)}>
              <span>{data.skill === "listening" ? "Part" : "Section"} {section.order_index}</span>
              <small>{section.questions[0].number}–{section.questions.at(-1)?.number}</small>
            </button>
          ))}
        </nav>
        <div className="ielts-workspace-grid">
          <main className="ielts-question-stage">
            {active.has_audio && active.audio_url && (
              <div className="ielts-audio-player"><div><strong>{active.title} · 真题音频</strong><span>来自 resources 的本地音频，答案会自动保存。</span></div><audio controls preload="metadata" src={active.audio_url} /></div>
            )}
            <SectionWorkspace
              section={active}
              skill={data.skill}
              answers={answers}
              results={resultMap}
              missing={missing}
              onAnswer={updateAnswer}
              onGroupAnswer={updateGroup}
            />
            <footer className="ielts-section-footer">
              <button className="secondary-button" disabled={activeSection === data.sections[0].order_index} onClick={() => setActiveSection((value) => value - 1)}>← 上一部分</button>
              <button className="primary-button" disabled={activeSection === data.sections.at(-1)?.order_index} onClick={() => setActiveSection((value) => value + 1)}>下一部分 →</button>
            </footer>
          </main>
          <aside className="ielts-answer-overview">
            <div className="ielts-overview-heading"><div><span>INTERACTIVE ANSWER SHEET</span><strong>{data.skill === "listening" ? "Listening" : "Reading"} Test {data.test_number}</strong></div><b>{answeredCount}/{data.question_count}</b></div>
            <div className="ielts-progress-track"><span style={{ width: `${answeredCount / data.question_count * 100}%` }} /></div>
            <p className="ielts-save-status" role="status">{saveStatus}</p>
            <div className="ielts-question-index">
              {data.sections.flatMap((section) => section.questions.map((question) => {
                const result = resultMap.get(question.number);
                const state = result ? (result.is_correct ? "correct" : "wrong") : missing.has(question.number) ? "missing" : answers[question.number]?.trim() ? "answered" : "";
                return <button className={state} key={question.number} onClick={() => jumpTo(question.number)}>{question.number}</button>;
              }))}
            </div>
            <button className="primary-button ielts-submit" disabled={submitting} onClick={submit}>{submitting ? "正在评分…" : "完成全部并提交"}</button>
            {score !== null && <div className="ielts-score-card"><small>本次成绩</small><strong>{score} / {data.question_count}</strong><p>每道错题下方已显示正确答案与中文精解。</p></div>}
          </aside>
        </div>
      </div>
    </AppShell>
  );
}


function SectionWorkspace({ section, skill, ...props }: {
  section: IeltsSection;
  skill: "listening" | "reading";
  answers: Record<number, string>;
  results: Map<number, IeltsQuestionResult>;
  missing: Set<number>;
  onAnswer: (number: number, answer: string, immediate?: boolean) => void;
  onGroupAnswer: (questions: IeltsQuestion[], selected: string[]) => void;
}) {
  const blockProps = { answers: props.answers, results: props.results, missing: props.missing, onAnswer: props.onAnswer };
  const questions = <IeltsQuestionList questions={section.questions} embeddedNumbers={section.embedded_question_numbers} {...props} />;
  if (skill === "reading") {
    return (
      <div className="ielts-reading-split">
        <article className="ielts-reading-pane source"><header><span>READING PASSAGE</span><h2>{section.title}</h2><p>原文区域可独立滚动。</p></header>{section.source_blocks.map((block, index) => <IeltsContentBlockView block={block} key={index} {...blockProps} />)}</article>
        <article className="ielts-reading-pane questions"><header><span>QUESTIONS {section.questions[0].number}–{section.questions.at(-1)?.number}</span><h2>题目与答题区</h2><p>{section.instructions}</p></header>{section.question_blocks.map((block, index) => <IeltsContentBlockView block={block} key={index} {...blockProps} />)}{questions}</article>
      </div>
    );
  }
  return (
    <article className="ielts-exam-paper">
      <header><span>Test</span><strong>LISTENING</strong><h2>{section.title}</h2><p><b>Questions {section.questions[0].number}–{section.questions.at(-1)?.number}</b></p><p>{section.instructions}</p></header>
      {section.content_blocks.map((block, index) => <IeltsContentBlockView block={block} key={index} {...blockProps} />)}
      {questions}
    </article>
  );
}


function ExamTimer({ minutes }: { minutes: number }) {
  const [remaining, setRemaining] = useState(minutes * 60);
  const [running, setRunning] = useState(false);
  useEffect(() => {
    if (!running || remaining <= 0) return;
    const timer = window.setInterval(() => setRemaining((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [running, remaining]);
  const display = `${String(Math.floor(remaining / 60)).padStart(2, "0")}:${String(remaining % 60).padStart(2, "0")}`;
  return <div className="ielts-exam-timer"><span>倒计时</span><strong>{display}</strong><button onClick={() => setRunning((value) => !value)} disabled={remaining === 0}>{remaining === 0 ? "时间到" : running ? "暂停" : remaining === minutes * 60 ? "开始计时" : "继续计时"}</button></div>;
}
