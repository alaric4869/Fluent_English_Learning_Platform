import { QuestionFeedback } from "./IeltsContentBlock";
import type { IeltsQuestion, IeltsQuestionResult } from "../../types/ielts";


interface QuestionListProps {
  questions: IeltsQuestion[];
  embeddedNumbers: number[];
  answers: Record<number, string>;
  results: Map<number, IeltsQuestionResult>;
  missing: Set<number>;
  onAnswer: (number: number, answer: string, immediate?: boolean) => void;
  onGroupAnswer: (questions: IeltsQuestion[], selected: string[]) => void;
}


export function IeltsQuestionList(props: QuestionListProps) {
  const embedded = new Set(props.embeddedNumbers);
  const grouped = new Set<string>();
  return (
    <div className="ielts-question-list">
      {props.questions.map((question) => {
        if (embedded.has(question.number)) return null;
        if (question.answer_group) {
          if (grouped.has(question.answer_group)) return null;
          grouped.add(question.answer_group);
          const members = props.questions.filter((item) => item.answer_group === question.answer_group);
          return <QuestionGroup key={question.answer_group} {...props} questions={members} />;
        }
        return <QuestionCard key={question.number} question={question} {...props} />;
      })}
    </div>
  );
}


function QuestionGroup({ questions, answers, results, missing, onGroupAnswer }: QuestionListProps & { questions: IeltsQuestion[] }) {
  const first = questions[0];
  const selected = questions.map((question) => answers[question.number]).filter(Boolean);
  const groupResults = questions.map((question) => results.get(question.number)).filter((item) => item !== undefined);
  const wrong = groupResults.filter((item) => !item.is_correct);
  const hasMissing = questions.some((question) => missing.has(question.number));
  function toggle(key: string) {
    const next = selected.includes(key)
      ? selected.filter((item) => item !== key)
      : selected.length < questions.length ? [...selected, key] : selected;
    onGroupAnswer(questions, next);
  }
  return (
    <section className={`ielts-question-card ${wrong.length ? "wrong" : groupResults.length ? "correct" : hasMissing ? "missing" : ""}`} id={`question-${first.number}`}>
      <div className="ielts-question-heading">
        <span>{first.number}–{questions.at(-1)?.number}</span>
        <div><p>{first.prompt}</p><small>Choose {questions.length} answers.</small></div>
      </div>
      <div className="ielts-choice-list">
        {first.options.map((option) => (
          <label key={option.key}>
            <input type="checkbox" checked={selected.includes(option.key)} onChange={() => toggle(option.key)} />
            <b>{option.key}</b><span>{option.text}</span>
          </label>
        ))}
      </div>
      <p className="ielts-selection-hint">已选择 {selected.length}/{questions.length} 项。每组可以选择多个答案。</p>
      {wrong.length > 0 && (
        <div className="ielts-group-feedback">
          {wrong.map((result) => <QuestionFeedback key={result.number} result={result} />)}
        </div>
      )}
      {groupResults.length > 0 && wrong.length === 0 && <span className="ielts-feedback correct">✓ All correct</span>}
    </section>
  );
}


function QuestionCard({ question, answers, results, missing, onAnswer }: QuestionListProps & { question: IeltsQuestion }) {
  const result = results.get(question.number);
  const state = result ? (result.is_correct ? "correct" : "wrong") : missing.has(question.number) ? "missing" : "";
  return (
    <section className={`ielts-question-card ${state}`} id={`question-${question.number}`}>
      <div className="ielts-question-heading"><span>{question.number}</span><p>{question.prompt}</p></div>
      {question.question_type === "text" ? (
        <input
          className="ielts-text-answer"
          value={answers[question.number] ?? ""}
          onChange={(event) => onAnswer(question.number, event.target.value)}
          onBlur={(event) => onAnswer(question.number, event.target.value, true)}
          placeholder="输入答案"
          maxLength={500}
          autoComplete="off"
        />
      ) : (
        <div className="ielts-choice-list">
          {question.options.map((option) => (
            <label key={option.key}>
              <input
                type="radio"
                name={`question-${question.number}`}
                value={option.key}
                checked={answers[question.number] === option.key}
                onChange={() => onAnswer(question.number, option.key, true)}
              />
              <b>{option.key}</b><span>{option.text}</span>
            </label>
          ))}
        </div>
      )}
      <QuestionFeedback result={result} />
    </section>
  );
}
