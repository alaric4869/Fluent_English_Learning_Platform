import type { MasteryStatus, ReviewItemDto, ReviewRating } from "../shared/contracts";

export interface ReviewRepository {
  listDue(userId: string, date: string): Promise<ReviewItemDto[]>;
  get(userId: string, reviewItemId: string): Promise<ReviewItemDto | null>;
  create(input: {
    userId: string;
    targetType: ReviewItemDto["targetType"];
    targetId: string;
    prompt: string;
    answer: string;
    dueDate: string;
  }): Promise<void>;
  recordAttempt(input: {
    userId: string;
    reviewItemId: string;
    rating: ReviewRating;
    previousDueDate: string;
    nextDueDate: string;
    nextStage: number;
    mastery: MasteryStatus;
    lapse: boolean;
  }): Promise<void>;
}
