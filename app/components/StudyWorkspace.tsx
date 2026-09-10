"use client";

import { useEffect, useMemo, useState } from "react";
import type { AppAction, ReviewItemDto, SavedSentenceDto, SentenceStatus, StudyPlanItemDto } from "../../modules/shared/contracts";
import { Modal, ModuleMark, StatusPill } from "./ui";

export function StudyWorkspace({ item, date, dueReviews, savedSentences = [], busy, onAction, onClose }: {
  item: StudyPlanItemDto;
  date: string;
  dueReviews: ReviewItemDto[];
  savedSentences?: SavedSentenceDto[];
  busy: boolean;
  onAction: (action: AppAction, refresh?: boolean) => Promise<boolean>;
  onClose: () => void;
}) {
  const [elapsed, setElapsed] = useState(0);
  const [transcriptVisible, setTranscriptVisible] = useState(false);
  const [steps, setSteps] = useState<boolean[]>(item.instructions.map(() => false));
  const [notes, setNotes] = useState(item.notes);
  const [difficulty, setDifficulty] = useState(item.difficultyRating ?? 3);
  const [confidence, setConfidence] = useState(item.confidenceRating ?? 3);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [outline, setOutline] = useState("");
  const [mistakes, setMistakes] = useState("");
  const [improved, setImproved] = useState("");
  const content = item.resource.content;

  const initialStatuses = useMemo(() => Object.fromEntries(
    savedSentences.filter((sentence) => sentence.resourceId === item.resource.id).map((sentence) => [sentence.sentenceIndex, sentence.status]),
  ) as Record<number, SentenceStatus>, [savedSentences, item.resource.id]);
  const [sentenceStatuses, setSentenceStatuses] = useState<Record<number, SentenceStatus>>(initialStatuses);

  useEffect(() => {
    if (item.status === "completed") return;
    const timer = window.setInterval(() => setElapsed((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [item.status]);

  const saveSentence = async (sentence: string, sentenceIndex: number, status: SentenceStatus) => {
    setSentenceStatuses((current) => ({ ...current, [sentenceIndex]: status }));
    await onAction({ type: "save_sentence", resourceId: item.resource.id, sentenceIndex, sentence, status, date }, false);
  };

  const saveChunk = async (chunk: { phrase: string; meaning: string; example: string }) => {
    const ok = await onAction({
      type: "add_vocabulary",
      phrase: chunk.phrase,
      meaning: chunk.meaning,
      example: chunk.example,
      sourceResourceId: item.resource.id,
      date,
    }, false);
    if (ok) {
      setSavedMessage(`“${chunk.phrase}” added to your chunk library.`);
      window.setTimeout(() => setSavedMessage(null), 2400);
    }
  };

  const complete = async () => {
    await onAction({ type: "save_plan_notes", planItemId: item.id, notes }, false);
    await onAction({ type: "rate_plan_item", planItemId: item.id, difficulty, confidence }, false);
    if (outline || mistakes || improved) {
      await onAction({
        type: "add_notebook_entry",
        entryType: "speaking",
        title: `Retelling — ${item.resource.title}`,
        content: `Outline: ${outline || "—"}\nMistakes: ${mistakes || "—"}\nImproved version: ${improved || "—"}`,
        sourceResourceId: item.resource.id,
      }, false);
    }
    const ok = await onAction({ type: "complete_plan_item", planItemId: item.id, activeSeconds: elapsed });
    if (ok) onClose();
  };

  return (
    <Modal title={item.resource.title} eyebrow={`${item.module} · ${item.targetMinutes} minutes`} onClose={onClose} wide>
      <div className="workspace-layout">
        <div className="workspace-main">
          <div className="workspace-toolbar">
            <div><ModuleMark module={item.module} /><StatusPill status={item.status} /></div>
            <div className="study-clock"><span className="pulse-dot" />{formatTimer(elapsed)}</div>
          </div>

          {item.module === "listening" && (
            <>
              <div className="media-placeholder">
                <span>LISTENING PLAYER</span><button aria-label="Play listening audio">▶</button>
                <div><strong>{item.resource.title}</strong><small>Short real-world English · replay as often as needed</small></div>
              </div>
              <div className="content-section transcript-section">
                <div className="content-section-title"><div><p className="eyebrow">Transcript</p><h3>Listen first. Reveal when ready.</h3></div><button className="secondary-button compact" onClick={() => setTranscriptVisible((value) => !value)}>{transcriptVisible ? "Hide transcript" : "Reveal transcript"}</button></div>
                <div className={transcriptVisible ? "transcript-copy visible" : "transcript-copy hidden"}>{content.transcript}</div>
              </div>
              <SentencePractice sentences={content.sentences ?? []} module="listening" statuses={sentenceStatuses} onStatus={saveSentence} />
            </>
          )}

          {item.module === "speaking" && (
            <>
              <div className="speaking-callout"><span>Listen → Pause → Repeat → Imitate → Hide → Retell</span><p>Keep the rhythm. Perfect grammar is not the goal during the first retell.</p></div>
              <SentencePractice sentences={content.sentences ?? []} module="speaking" statuses={sentenceStatuses} onStatus={saveSentence} />
              {(content.pronunciationNotes?.length || content.connectedSpeechNotes?.length) && (
                <div className="notes-pair">
                  <div><p className="eyebrow">Pronunciation</p>{content.pronunciationNotes?.map((note) => <p key={note}>{note}</p>)}</div>
                  <div><p className="eyebrow">Connected speech</p>{content.connectedSpeechNotes?.map((note) => <p key={note}>{note}</p>)}</div>
                </div>
              )}
              <div className="content-section">
                <p className="eyebrow">Retelling workspace</p><h3>Say it in your own English</h3>
                <div className="form-grid two-columns">
                  <label>My outline<textarea value={outline} onChange={(event) => setOutline(event.target.value)} placeholder="First… then… finally…" /></label>
                  <label>Mistakes I noticed<textarea value={mistakes} onChange={(event) => setMistakes(event.target.value)} placeholder="Words I missed or grammar to improve" /></label>
                  <label className="span-two">Improved version<textarea value={improved} onChange={(event) => setImproved(event.target.value)} placeholder="Write a clearer version after speaking" /></label>
                </div>
              </div>
            </>
          )}

          {item.module === "reading" && (
            <>
              <article className="reading-paper"><p className="eyebrow">Reading text</p><h3>{item.resource.title}</h3><p>{content.article}</p>{item.resource.url && <a href={item.resource.url} target="_blank" rel="noreferrer">Open original source ↗</a>}</article>
              <div className="content-section"><p className="eyebrow">Comprehension check</p><h3>Answer briefly in your own words</h3><div className="question-list">{content.questions?.map((question, index) => <label key={question}><span>{index + 1}</span><div><strong>{question}</strong><textarea placeholder="Your answer…" /></div></label>)}</div></div>
            </>
          )}

          {item.module === "vocabulary" && (
            <>
              <div className="speaking-callout"><span>{dueReviews.length} reviews are due today</span><p>Recall the meaning before revealing the answer. New chunks come second.</p></div>
              <div className="content-section"><p className="eyebrow">Today’s chunk set</p><h3>Learn the whole expression</h3><p>Say each example aloud, then replace one detail to make it personal.</p></div>
            </>
          )}

          {content.chunks && content.chunks.length > 0 && (
            <div className="chunk-list">
              {content.chunks.map((chunk) => (
                <div className="chunk-row" key={chunk.phrase}><div><strong>{chunk.phrase}</strong><span>{chunk.meaning}</span><p>{chunk.example}</p></div><button className="save-chip" onClick={() => void saveChunk(chunk)}>＋ Save chunk</button></div>
              ))}
            </div>
          )}
          {savedMessage && <div className="toast-message">✓ {savedMessage}</div>}
        </div>

        <aside className="workspace-sidebar">
          <div><p className="eyebrow">Today’s workflow</p><h3>One pass at a time</h3></div>
          <div className="workflow-list">
            {item.instructions.map((instruction, index) => (
              <button className={steps[index] ? "done" : ""} key={instruction} onClick={() => setSteps((current) => current.map((value, stepIndex) => stepIndex === index ? !value : value))}>
                <span>{steps[index] ? "✓" : index + 1}</span><p>{instruction}</p>
              </button>
            ))}
          </div>
          <div className="objectives-box"><p className="eyebrow">Learning objectives</p>{item.objectives.map((objective) => <span key={objective}>✓ {objective}</span>)}</div>
          <label className="notes-label">Personal notes<textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="What did you notice today?" /></label>
          <Rating label="Difficulty" value={difficulty} onChange={setDifficulty} low="Easy" high="Hard" />
          <Rating label="Confidence" value={confidence} onChange={setConfidence} low="Low" high="High" />
          <button className="primary-button full" disabled={busy} onClick={() => void complete()}>{busy ? "Saving…" : item.status === "completed" ? "Save reflection" : "Complete module"} <span>✓</span></button>
        </aside>
      </div>
    </Modal>
  );
}

function SentencePractice({ sentences, module, statuses, onStatus }: {
  sentences: string[];
  module: "listening" | "speaking";
  statuses: Record<number, SentenceStatus>;
  onStatus: (sentence: string, sentenceIndex: number, status: SentenceStatus) => Promise<void>;
}) {
  const choices: Array<{ value: SentenceStatus; label: string }> = module === "listening"
    ? [{ value: "couldnt_hear", label: "Couldn’t hear" }, { value: "difficult", label: "Difficult" }, { value: "understood", label: "Understood" }, { value: "mastered", label: "Mastered" }]
    : [{ value: "need_practice", label: "Need practice" }, { value: "good", label: "Good" }, { value: "mastered", label: "Mastered" }];
  return (
    <div className="content-section"><p className="eyebrow">Sentence practice</p><h3>{module === "listening" ? "What could your ears catch?" : "Repeat, then hide and reproduce"}</h3>
      <div className="sentence-list">{sentences.map((sentence, index) => (
        <div className="sentence-row" key={`${sentence}-${index}`}><span className="sentence-number">{String(index + 1).padStart(2, "0")}</span><div><p>{sentence}</p><div className="sentence-ratings">{choices.map((choice) => <button className={statuses[index] === choice.value ? "active" : ""} key={choice.value} onClick={() => void onStatus(sentence, index, choice.value)}>{choice.label}</button>)}</div></div></div>
      ))}</div>
    </div>
  );
}

function Rating({ label, value, onChange, low, high }: { label: string; value: number; onChange: (value: number) => void; low: string; high: string }) {
  return <div className="rating-block"><div><strong>{label}</strong><span>{low} → {high}</span></div><div>{[1, 2, 3, 4, 5].map((rating) => <button className={rating === value ? "active" : ""} key={rating} onClick={() => onChange(rating)}>{rating}</button>)}</div></div>;
}

function formatTimer(seconds: number) {
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}
