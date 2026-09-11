import type { IeltsAttemptDto, IeltsGoalDto, IeltsSkill } from "../shared/contracts";

export interface CompleteIeltsAttemptInput {
  rawScore: number | null;
  estimatedBand: number | null;
  notes: string;
}

export interface IeltsRepository {
  getGoal(userId: string): Promise<IeltsGoalDto | null>;
  saveGoal(userId: string, targetBand: number, examDate: string): Promise<void>;
  listAttempts(userId: string): Promise<IeltsAttemptDto[]>;
  startAttempt(userId: string, bookNumber: number, testNumber: number, skill: IeltsSkill): Promise<string>;
  completeAttempt(userId: string, attemptId: string, input: CompleteIeltsAttemptInput): Promise<void>;
}
