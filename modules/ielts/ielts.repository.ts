import type { IeltsAttemptDto, IeltsGoalDto, IeltsQuestionResponseDto, IeltsSkill } from "../shared/contracts";
import type { IeltsGradedAnswer, IeltsSubmittedAnswer } from "./ielts-question-bank";

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
  cancelAttempt(userId: string, attemptId: string): Promise<void>;
  listResponses(userId: string, attemptId: string): Promise<IeltsQuestionResponseDto[]>;
  saveResponses(userId: string, attemptId: string, answers: IeltsSubmittedAnswer[]): Promise<void>;
  saveGradedResponses(userId: string, attemptId: string, answers: IeltsGradedAnswer[]): Promise<void>;
  completeAttempt(userId: string, attemptId: string, input: CompleteIeltsAttemptInput): Promise<void>;
}
