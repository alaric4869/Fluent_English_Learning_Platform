import type { MasteryStatus, ReviewRating } from "../shared/contracts";

export const REVIEW_INTERVALS = [1, 3, 7, 14, 30] as const;

export interface ReviewScheduleResult {
  nextStage: number;
  nextDueDate: string;
  mastery: MasteryStatus;
  lapse: boolean;
}

export interface ReviewScheduler {
  schedule(input: { currentStage: number; rating: ReviewRating; reviewDate: string }): ReviewScheduleResult;
}

export class FixedIntervalReviewScheduler implements ReviewScheduler {
  schedule(input: { currentStage: number; rating: ReviewRating; reviewDate: string }): ReviewScheduleResult {
    const { currentStage, rating, reviewDate } = input;
    if (rating === "again") {
      return { nextStage: 0, nextDueDate: shiftReviewDate(reviewDate, 1), mastery: "learning", lapse: true };
    }

    const step = rating === "easy" ? 2 : rating === "good" ? 1 : 0;
    const nextStage = Math.min(currentStage + step, REVIEW_INTERVALS.length);
    const intervalIndex = Math.min(nextStage, REVIEW_INTERVALS.length - 1);
    const interval = nextStage >= REVIEW_INTERVALS.length
      ? REVIEW_INTERVALS[REVIEW_INTERVALS.length - 1] * 2
      : REVIEW_INTERVALS[intervalIndex];
    const mastery: MasteryStatus = nextStage >= REVIEW_INTERVALS.length
      ? "mastered"
      : nextStage >= 3
        ? "familiar"
        : "learning";
    return { nextStage, nextDueDate: shiftReviewDate(reviewDate, interval), mastery, lapse: false };
  }
}

function shiftReviewDate(date: string, days: number): string {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day + days)).toISOString().slice(0, 10);
}
