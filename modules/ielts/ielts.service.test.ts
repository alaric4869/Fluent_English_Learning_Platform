import { describe, expect, it, vi } from "vitest";
import type { IeltsAttemptDto } from "../shared/contracts";
import type { IeltsRepository } from "./ielts.repository";
import { IeltsService } from "./ielts.service";

const activeAttempt: IeltsAttemptDto = {
  id: "active-attempt",
  bookNumber: 4,
  testNumber: 3,
  skill: "listening",
  status: "in_progress",
  rawScore: null,
  estimatedBand: null,
  notes: "",
  startedAt: "2026-09-11T05:28:28.908Z",
  completedAt: null,
};

function repositoryWith(attempts: IeltsAttemptDto[]): IeltsRepository {
  return {
    getGoal: vi.fn().mockResolvedValue(null),
    saveGoal: vi.fn().mockResolvedValue(undefined),
    listAttempts: vi.fn().mockResolvedValue(attempts),
    startAttempt: vi.fn().mockResolvedValue("new-attempt"),
    cancelAttempt: vi.fn().mockResolvedValue(undefined),
    listResponses: vi.fn().mockResolvedValue([]),
    saveResponses: vi.fn().mockResolvedValue(undefined),
    saveGradedResponses: vi.fn().mockResolvedValue(undefined),
    completeAttempt: vi.fn().mockResolvedValue(undefined),
  };
}

describe("IeltsService active attempt handling", () => {
  it("reuses the current attempt for an identical start request", async () => {
    const repository = repositoryWith([activeAttempt]);
    const service = new IeltsService(repository);

    await expect(service.startAttempt("learner", 4, 3, "listening")).resolves.toBe("active-attempt");
    expect(repository.startAttempt).not.toHaveBeenCalled();
  });

  it("prevents a second material from replacing an active attempt", async () => {
    const service = new IeltsService(repositoryWith([activeAttempt]));

    await expect(service.startAttempt("learner", 20, 1, "reading")).rejects.toThrow(/current IELTS practice/i);
  });

  it("cancels only the learner's active attempt", async () => {
    const repository = repositoryWith([activeAttempt]);
    const service = new IeltsService(repository);

    await service.cancelAttempt("learner", "active-attempt");
    expect(repository.cancelAttempt).toHaveBeenCalledWith("learner", "active-attempt");
  });

  it("grades a complete objective answer sheet and persists question-level results", async () => {
    const repository = repositoryWith([{ ...activeAttempt, bookNumber: 20, testNumber: 1 }]);
    const service = new IeltsService(repository);
    const answers = Array.from({ length: 40 }, (_, index) => ({
      questionNumber: index + 1,
      sectionNumber: Math.ceil((index + 1) / 10),
      answer: "wrong",
    }));

    const result = await service.submitObjectiveAttempt("learner", "active-attempt", answers, "baseline");

    expect(result.rawScore).toBe(0);
    expect(repository.saveGradedResponses).toHaveBeenCalledWith("learner", "active-attempt", expect.arrayContaining([
      expect.objectContaining({ questionNumber: 1, isCorrect: false, correctAnswer: "fish" }),
    ]));
    expect(repository.completeAttempt).toHaveBeenCalledWith("learner", "active-attempt", expect.objectContaining({ rawScore: 0, notes: "baseline" }));
  });
});
