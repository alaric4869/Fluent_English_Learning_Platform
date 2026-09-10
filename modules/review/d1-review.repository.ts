import { getD1 } from "../../db";
import type { MasteryStatus, ReviewItemDto, ReviewRating } from "../shared/contracts";
import type { ReviewRepository } from "./review.repository";

interface ReviewRow {
  id: string;
  target_type: ReviewItemDto["targetType"];
  target_id: string;
  prompt: string;
  answer: string;
  stage: number;
  due_date: string;
  mastery: MasteryStatus;
}

export class D1ReviewRepository implements ReviewRepository {
  async listDue(userId: string, date: string): Promise<ReviewItemDto[]> {
    const result = await getD1().prepare(`SELECT id, target_type, target_id, prompt, answer, stage, due_date, mastery
      FROM review_items WHERE user_id = ? AND due_date <= ?
      ORDER BY due_date, lapse_count DESC, created_at LIMIT 40`)
      .bind(userId, date).all<ReviewRow>();
    return result.results.map(mapReview);
  }

  async get(userId: string, reviewItemId: string): Promise<ReviewItemDto | null> {
    const row = await getD1().prepare(`SELECT id, target_type, target_id, prompt, answer, stage, due_date, mastery
      FROM review_items WHERE id = ? AND user_id = ?`)
      .bind(reviewItemId, userId).first<ReviewRow>();
    return row ? mapReview(row) : null;
  }

  async create(input: {
    userId: string;
    targetType: ReviewItemDto["targetType"];
    targetId: string;
    prompt: string;
    answer: string;
    dueDate: string;
  }): Promise<void> {
    await getD1().prepare(`INSERT OR IGNORE INTO review_items (
      id, user_id, target_type, target_id, prompt, answer, stage, due_date, mastery
    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'new')`)
      .bind(crypto.randomUUID(), input.userId, input.targetType, input.targetId, input.prompt, input.answer, input.dueDate).run();
  }

  async recordAttempt(input: {
    userId: string;
    reviewItemId: string;
    rating: ReviewRating;
    previousDueDate: string;
    nextDueDate: string;
    nextStage: number;
    mastery: MasteryStatus;
    lapse: boolean;
  }): Promise<void> {
    const d1 = getD1();
    await d1.batch([
      d1.prepare(`UPDATE review_items SET stage = ?, due_date = ?, mastery = ?,
        lapse_count = lapse_count + ? WHERE id = ? AND user_id = ?`)
        .bind(input.nextStage, input.nextDueDate, input.mastery, input.lapse ? 1 : 0, input.reviewItemId, input.userId),
      d1.prepare(`INSERT INTO review_attempts (
        id, review_item_id, user_id, rating, previous_due_date, next_due_date
      ) VALUES (?, ?, ?, ?, ?, ?)`)
        .bind(crypto.randomUUID(), input.reviewItemId, input.userId, input.rating, input.previousDueDate, input.nextDueDate),
    ]);
  }
}

function mapReview(row: ReviewRow): ReviewItemDto {
  return {
    id: row.id,
    targetType: row.target_type,
    targetId: row.target_id,
    prompt: row.prompt,
    answer: row.answer,
    stage: row.stage,
    dueDate: row.due_date,
    mastery: row.mastery,
  };
}
