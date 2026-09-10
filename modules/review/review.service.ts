import type { ReviewRating } from "../shared/contracts";
import type { ReviewRepository } from "./review.repository";
import type { ReviewScheduler } from "./review-scheduler";

export class ReviewService {
  constructor(
    private readonly reviews: ReviewRepository,
    private readonly scheduler: ReviewScheduler,
  ) {}

  listDue(userId: string, date: string) {
    return this.reviews.listDue(userId, date);
  }

  async rate(userId: string, reviewItemId: string, rating: ReviewRating, date: string) {
    const item = await this.reviews.get(userId, reviewItemId);
    if (!item) throw new Error("Review item not found.");
    const schedule = this.scheduler.schedule({ currentStage: item.stage, rating, reviewDate: date });
    return this.reviews.recordAttempt({
      userId,
      reviewItemId,
      rating,
      previousDueDate: item.dueDate,
      ...schedule,
    });
  }
}
