"use client";

import { useState } from "react";
import type { AppAction, AppStateDto, ReviewRating } from "../../modules/shared/contracts";
import { EmptyState } from "./ui";

const RATINGS: Array<{ value: ReviewRating; label: string; hint: string }> = [
  { value: "again", label: "Again", hint: "Tomorrow" },
  { value: "hard", label: "Hard", hint: "Keep stage" },
  { value: "good", label: "Good", hint: "Next stage" },
  { value: "easy", label: "Easy", hint: "Skip ahead" },
];

export function ReviewView({ state, onAction }: { state: AppStateDto; onAction: (action: AppAction) => Promise<boolean> }) {
  const [activeId, setActiveId] = useState(state.dueReviews[0]?.id ?? null);
  const [revealed, setRevealed] = useState(false);
  const [completed, setCompleted] = useState(0);
  const item = state.dueReviews.find((review) => review.id === activeId) ?? state.dueReviews[0];

  const rate = async (rating: ReviewRating) => {
    if (!item) return;
    const currentIndex = state.dueReviews.findIndex((review) => review.id === item.id);
    const next = state.dueReviews[currentIndex + 1];
    if (await onAction({ type: "rate_review", reviewItemId: item.id, rating, date: state.today.date })) {
      setCompleted((value) => value + 1);
      setActiveId(next?.id ?? null);
      setRevealed(false);
    }
  };

  return (
    <div className="page-wrap review-page">
      <section className="page-title-row"><div><p className="eyebrow">Spaced repetition</p><h1>Review what matters</h1><p>Recall first, reveal second. A short honest review is more valuable than rereading.</p></div><div className="review-total"><strong>{state.dueReviews.length}</strong><span>items due</span></div></section>
      {state.dueReviews.length === 0 ? <EmptyState title="You’re caught up" copy="New chunks and difficult sentences will appear here when they become due." /> : (
        <div className="review-layout">
          <aside className="review-queue"><p className="eyebrow">Today’s queue</p>{state.dueReviews.map((review, index) => <button className={review.id === item?.id ? "active" : ""} key={review.id} onClick={() => { setActiveId(review.id); setRevealed(false); }}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{review.targetType}</strong><small>{review.mastery} · stage {review.stage + 1}</small></div></button>)}</aside>
          {item && <section className="review-card-main">
            <div className="review-card-progress"><span style={{ width: `${Math.round((completed / Math.max(1, state.dueReviews.length + completed)) * 100)}%` }} /></div>
            <p className="eyebrow">{item.targetType} · due {item.dueDate}</p><h2>{item.prompt}</h2>
            <p className="recall-instruction">Say the meaning and one complete example sentence before revealing the answer.</p>
            <button className="reveal-zone" onClick={() => setRevealed(true)}>{revealed ? <><span>Answer</span><strong>{item.answer}</strong></> : <><span>Think first</span><strong>Click to reveal the answer</strong></>}</button>
            <div className={`rating-actions ${revealed ? "visible" : ""}`}>{RATINGS.map((rating) => <button key={rating.value} onClick={() => void rate(rating.value)}><strong>{rating.label}</strong><span>{rating.hint}</span></button>)}</div>
          </section>}
          <aside className="review-guidance"><p className="eyebrow">How to rate</p><div><strong>Again</strong><p>I could not recall it.</p></div><div><strong>Hard</strong><p>I recalled it slowly or with mistakes.</p></div><div><strong>Good</strong><p>I recalled it with a little effort.</p></div><div><strong>Easy</strong><p>It was immediate and natural.</p></div></aside>
        </div>
      )}
    </div>
  );
}
