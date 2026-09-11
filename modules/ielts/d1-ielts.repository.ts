import { getD1 } from "../../db";
import type { IeltsAttemptDto, IeltsGoalDto, IeltsSkill } from "../shared/contracts";
import type { CompleteIeltsAttemptInput, IeltsRepository } from "./ielts.repository";

interface GoalRow { test_type: "general"; target_band: number; exam_date: string; updated_at: string }
interface AttemptRow {
  id: string;
  book_number: number;
  test_number: number;
  skill: IeltsSkill;
  status: IeltsAttemptDto["status"];
  raw_score: number | null;
  estimated_band: number | null;
  notes: string;
  started_at: string;
  completed_at: string | null;
}

export class D1IeltsRepository implements IeltsRepository {
  async getGoal(userId: string): Promise<IeltsGoalDto | null> {
    const row = await getD1().prepare(
      "SELECT test_type, target_band, exam_date, updated_at FROM ielts_goals WHERE user_id = ?",
    ).bind(userId).first<GoalRow>();
    return row ? {
      testType: row.test_type,
      targetBand: row.target_band,
      examDate: row.exam_date,
      updatedAt: row.updated_at,
    } : null;
  }

  async saveGoal(userId: string, targetBand: number, examDate: string): Promise<void> {
    await getD1().prepare(`INSERT INTO ielts_goals (
      user_id, test_type, target_band, exam_date, created_at, updated_at
    ) VALUES (?, 'general', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id) DO UPDATE SET
      test_type = 'general', target_band = excluded.target_band,
      exam_date = excluded.exam_date, updated_at = CURRENT_TIMESTAMP`)
      .bind(userId, targetBand, examDate).run();
  }

  async listAttempts(userId: string): Promise<IeltsAttemptDto[]> {
    const result = await getD1().prepare(`SELECT id, book_number, test_number, skill, status,
      raw_score, estimated_band, notes, started_at, completed_at
      FROM ielts_attempts WHERE user_id = ? ORDER BY started_at DESC LIMIT 200`)
      .bind(userId).all<AttemptRow>();
    return result.results.map((row) => ({
      id: row.id,
      bookNumber: row.book_number,
      testNumber: row.test_number,
      skill: row.skill,
      status: row.status,
      rawScore: row.raw_score,
      estimatedBand: row.estimated_band,
      notes: row.notes,
      startedAt: row.started_at,
      completedAt: row.completed_at,
    }));
  }

  async startAttempt(userId: string, bookNumber: number, testNumber: number, skill: IeltsSkill): Promise<string> {
    const id = crypto.randomUUID();
    await getD1().prepare(`INSERT INTO ielts_attempts (
      id, user_id, book_number, test_number, skill, status, started_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, 'in_progress', ?, CURRENT_TIMESTAMP)`)
      .bind(id, userId, bookNumber, testNumber, skill, new Date().toISOString()).run();
    return id;
  }

  async completeAttempt(userId: string, attemptId: string, input: CompleteIeltsAttemptInput): Promise<void> {
    const result = await getD1().prepare(`UPDATE ielts_attempts SET
      status = 'completed', raw_score = ?, estimated_band = ?, notes = ?,
      completed_at = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ? AND user_id = ?`)
      .bind(input.rawScore, input.estimatedBand, input.notes, new Date().toISOString(), attemptId, userId).run();
    if (!result.meta.changes) throw new Error("IELTS practice attempt not found.");
  }
}
