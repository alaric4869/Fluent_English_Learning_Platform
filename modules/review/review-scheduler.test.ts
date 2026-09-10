import { describe, expect, it } from "vitest";
import { FixedIntervalReviewScheduler } from "./review-scheduler";

describe("FixedIntervalReviewScheduler", () => {
  const scheduler = new FixedIntervalReviewScheduler();

  it("resets a lapse and schedules it for tomorrow", () => {
    expect(scheduler.schedule({ currentStage: 3, rating: "again", reviewDate: "2026-09-11" })).toEqual({
      nextStage: 0,
      nextDueDate: "2026-09-12",
      mastery: "learning",
      lapse: true,
    });
  });

  it("advances one stage for a good recall", () => {
    expect(scheduler.schedule({ currentStage: 1, rating: "good", reviewDate: "2026-09-11" })).toMatchObject({
      nextStage: 2,
      nextDueDate: "2026-09-18",
      mastery: "learning",
    });
  });

  it("skips a stage for easy and eventually marks mastery", () => {
    expect(scheduler.schedule({ currentStage: 4, rating: "easy", reviewDate: "2026-09-11" })).toMatchObject({
      nextStage: 5,
      nextDueDate: "2026-11-10",
      mastery: "mastered",
    });
  });
});
