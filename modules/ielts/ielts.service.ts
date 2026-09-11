import type { IeltsAttemptDto, IeltsDashboardDto, IeltsSkill } from "../shared/contracts";
import { estimateIeltsBand } from "./ielts-score";
import type { IeltsRepository } from "./ielts.repository";

const IELTS_SKILLS: IeltsSkill[] = ["listening", "reading", "writing", "speaking"];
const DEFAULT_EXAM_DATE = "2026-10-31";

export class IeltsService {
  constructor(private readonly repository: IeltsRepository) {}

  async getDashboard(userId: string): Promise<IeltsDashboardDto> {
    let goal = await this.repository.getGoal(userId);
    if (!goal) {
      await this.repository.saveGoal(userId, 6.5, DEFAULT_EXAM_DATE);
      goal = await this.repository.getGoal(userId);
    }
    if (!goal) throw new Error("Unable to prepare IELTS goal.");
    const attempts = await this.repository.listAttempts(userId);
    return { goal, attempts, summary: summarizeAttempts(attempts) };
  }

  async saveGoal(userId: string, targetBand: number, examDate: string): Promise<void> {
    if (!Number.isFinite(targetBand) || targetBand < 4 || targetBand > 9 || targetBand * 2 % 1 !== 0) {
      throw new Error("Target band must be between 4.0 and 9.0 in half-band steps.");
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(examDate) || Number.isNaN(Date.parse(`${examDate}T00:00:00Z`))) {
      throw new Error("A valid exam date is required.");
    }
    await this.repository.saveGoal(userId, targetBand, examDate);
  }

  startAttempt(userId: string, bookNumber: number, testNumber: number, skill: IeltsSkill): Promise<string> {
    if (!Number.isInteger(bookNumber) || bookNumber < 4 || bookNumber > 20) throw new Error("Book must be between 4 and 20.");
    if (!Number.isInteger(testNumber) || testNumber < 1 || testNumber > 8) throw new Error("Test must be between 1 and 8.");
    if (!IELTS_SKILLS.includes(skill)) throw new Error("Unknown IELTS skill.");
    return this.repository.startAttempt(userId, bookNumber, testNumber, skill);
  }

  async completeAttempt(userId: string, attemptId: string, rawScore: number | undefined, estimatedBand: number | undefined, notes: string): Promise<void> {
    const attempts = await this.repository.listAttempts(userId);
    const attempt = attempts.find((candidate) => candidate.id === attemptId);
    if (!attempt || attempt.status !== "in_progress") throw new Error("Active IELTS attempt not found.");
    const objectiveSkill = attempt.skill === "listening" || attempt.skill === "reading";
    let normalizedRaw: number | null = null;
    let normalizedBand: number | null = null;
    if (objectiveSkill) {
      if (rawScore === undefined) throw new Error("Enter the number of correct answers.");
      normalizedRaw = rawScore;
      normalizedBand = estimateIeltsBand(attempt.skill, rawScore);
    } else {
      if (estimatedBand === undefined || estimatedBand < 0 || estimatedBand > 9 || estimatedBand * 2 % 1 !== 0) {
        throw new Error("Enter an estimated band in half-band steps.");
      }
      normalizedBand = estimatedBand;
    }
    await this.repository.completeAttempt(userId, attemptId, {
      rawScore: normalizedRaw,
      estimatedBand: normalizedBand,
      notes: notes.trim().slice(0, 4000),
    });
  }
}

function summarizeAttempts(attempts: IeltsAttemptDto[]): IeltsDashboardDto["summary"] {
  const completed = attempts.filter((attempt) => attempt.status === "completed");
  const weekAgo = Date.now() - 7 * 86_400_000;
  const scored = completed.filter((attempt) => attempt.estimatedBand !== null);
  const averageBand = average(scored.map((attempt) => attempt.estimatedBand as number));
  return {
    completedAttempts: completed.length,
    completedThisWeek: completed.filter((attempt) => Date.parse(attempt.completedAt ?? "") >= weekAgo).length,
    averageBand,
    skillAverages: IELTS_SKILLS.map((skill) => {
      const values = scored.filter((attempt) => attempt.skill === skill).map((attempt) => attempt.estimatedBand as number);
      return { skill, averageBand: average(values), attempts: values.length };
    }),
  };
}

function average(values: number[]): number | null {
  if (!values.length) return null;
  return Math.round((values.reduce((total, value) => total + value, 0) / values.length) * 10) / 10;
}
