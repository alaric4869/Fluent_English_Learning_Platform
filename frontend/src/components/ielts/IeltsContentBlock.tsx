import type {
  ContentPart,
  IeltsContentBlock,
  IeltsQuestionResult,
} from "../../types/ielts";


interface BlockProps {
  block: IeltsContentBlock;
  answers: Record<number, string>;
  results: Map<number, IeltsQuestionResult>;
  missing: Set<number>;
  onAnswer: (number: number, answer: string, immediate?: boolean) => void;
}


export function IeltsContentBlockView(props: BlockProps) {
  const { block } = props;
  if (block.kind === "table") {
    return (
      <section className="ielts-source-block ielts-table-block">
        {block.title && <h3>{block.title}</h3>}
        <div className="ielts-table-scroll" tabIndex={0} aria-label="可横向滚动的题目表格">
          <table className="ielts-question-table">
            <thead><tr>{block.headers.map((header) => <th key={header}>{header}</th>)}</tr></thead>
            <tbody>
              {block.rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.cells.map((cell, cellIndex) => (
                    <td key={cellIndex}><Parts parts={cell} {...props} /></td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    );
  }
  if (block.kind === "flowchart") {
    return (
      <section className="ielts-source-block ielts-flowchart-block">
        {block.title && <h3>{block.title}</h3>}
        <div className="ielts-flowchart">
          {block.nodes.map((node, index) => (
            <div className="ielts-flow-step-wrap" key={index}>
              <div className="ielts-flow-step"><Parts parts={node.parts} {...props} /></div>
              {index < block.nodes.length - 1 && <span className="ielts-flow-arrow">↓</span>}
            </div>
          ))}
        </div>
      </section>
    );
  }
  if (block.kind === "notes") {
    return (
      <section className="ielts-source-block ielts-notes-block">
        {block.title && <h3>{block.title}</h3>}
        {block.lead.length > 0 && <p><Parts parts={block.lead} {...props} /></p>}
        {block.sections.map((section) => (
          <section className="ielts-note-section" key={section.heading}>
            <h4>{section.heading}</h4>
            <ul>
              {section.items.map((item, index) => (
                <li className={item.level ? "nested" : ""} key={index}>
                  <Parts parts={item.parts} {...props} />
                </li>
              ))}
            </ul>
          </section>
        ))}
      </section>
    );
  }
  if (block.kind === "figure") {
    return (
      <section className="ielts-source-block ielts-figure-block">
        {block.title && <h3>{block.title}</h3>}
        <figure>
          <img src={`/media/ielts-assets/${block.asset_path}`} alt={block.alt || block.title} />
          {block.caption && <figcaption>{block.caption}</figcaption>}
        </figure>
        <div className="ielts-figure-answers">
          {block.answer_numbers.map((number) => <InlineAnswer key={number} number={number} {...props} />)}
        </div>
      </section>
    );
  }
  return (
    <section className={`ielts-source-block ${block.kind === "notice" ? "ielts-notice-block" : ""}`}>
      {block.title && <h3>{block.title}</h3>}
      {block.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}
    </section>
  );
}


function Parts({ parts, ...props }: BlockProps & { parts: ContentPart[] }) {
  return <>{parts.map((part, index) => (
    part.answer !== null
      ? <InlineAnswer key={`${part.answer}-${index}`} number={part.answer} {...props} />
      : <span className="ielts-copy" key={index}>{part.text}</span>
  ))}</>;
}


function InlineAnswer({ number, answers, results, missing, onAnswer }: Omit<BlockProps, "block"> & { number: number }) {
  const result = results.get(number);
  const state = result ? (result.is_correct ? "correct" : "wrong") : missing.has(number) ? "missing" : "";
  return (
    <span className={`ielts-inline-answer ${state}`} id={`question-${number}`}>
      <label>
        <b>{number}</b>
        <span className="sr-only">Question {number} answer</span>
        <input
          value={answers[number] ?? ""}
          onChange={(event) => onAnswer(number, event.target.value)}
          onBlur={(event) => onAnswer(number, event.target.value, true)}
          autoComplete="off"
        />
      </label>
      <QuestionFeedback result={result} />
    </span>
  );
}


export function QuestionFeedback({ result }: { result?: IeltsQuestionResult }) {
  if (!result) return null;
  if (result.is_correct) return <span className="ielts-feedback correct">✓ Correct</span>;
  return (
    <span className="ielts-feedback wrong">
      <strong>回答错误 · 你的答案：{result.submitted_answer || "未作答"}</strong>
      <span>正确答案：{result.correct_answers.join(" / ")}</span>
      <span>{result.explanation}</span>
    </span>
  );
}
