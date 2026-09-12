import { getD1 } from "../../db";
import type { IeltsAttemptDto, IeltsGoalDto, IeltsQuestionResponseDto, IeltsSkill } from "../shared/contracts";
import type { IeltsGradedAnswer, IeltsSubmittedAnswer } from "./ielts-question-bank";
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
interface ResponseRow {
  question_number: number;
  section_number: number;
  answer: string;
  is_correct: number | null;
  correct_answer: string | null;
  explanation_page: number | null;
  saved_at: string;
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

  async cancelAttempt(userId: string, attemptId: string): Promise<void> {
    const result = await getD1().prepare(`UPDATE ielts_attempts SET
      status = 'cancelled', updated_at = CURRENT_TIMESTAMP
      WHERE id = ? AND user_id = ? AND status = 'in_progress'`)
      .bind(attemptId, userId).run();
    if (!result.meta.changes) throw new Error("Active IELTS attempt not found.");
  }

  async listResponses(userId: string, attemptId: string): Promise<IeltsQuestionResponseDto[]> {
    const result = await getD1().prepare(`SELECT question_number, section_number, answer, is_correct,
      correct_answer, explanation_page, saved_at
      FROM ielts_question_responses WHERE user_id = ? AND attempt_id = ? ORDER BY question_number`)
      .bind(userId, attemptId).all<ResponseRow>();
    return result.results.map((row) => ({
      questionNumber: row.question_number,
      sectionNumber: row.section_number,
      answer: row.answer,
      isCorrect: row.is_correct === null ? null : row.is_correct === 1,
      correctAnswer: row.correct_answer,
      explanationPage: row.explanation_page,
      savedAt: row.saved_at,
    }));
  }

  async saveResponses(userId: string, attemptId: string, answers: IeltsSubmittedAnswer[]): Promise<void> {
    await this.assertActiveAttempt(userId, attemptId);
    if (!answers.length) return;
    const statements = answers.map((item) => getD1().prepare(`INSERT INTO ielts_question_responses (
      id, attempt_id, user_id, section_number, question_number, answer, is_correct,
      correct_answer, explanation_page, saved_at, graded_at
    ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, NULL)
    ON CONFLICT(attempt_id, question_number) DO UPDATE SET
      section_number = excluded.section_number, answer = excluded.answer,
      is_correct = NULL, correct_answer = NULL, explanation_page = NULL,
      saved_at = excluded.saved_at, graded_at = NULL`)
      .bind(crypto.randomUUID(), attemptId, userId, item.sectionNumber, item.questionNumber, item.answer, new Date().toISOString()));
    await getD1().batch(statements);
  }

  async saveGradedResponses(userId: string, attemptId: string, answers: IeltsGradedAnswer[]): Promise<void> {
    await this.assertActiveAttempt(userId, attemptId);
    const savedAt = new Date().toISOString();
    const statements = answers.map((item) => getD1().prepare(`INSERT INTO ielts_question_responses (
      id, attempt_id, user_id, section_number, question_number, answer, is_correct,
      correct_answer, explanation_page, saved_at, graded_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(attempt_id, question_number) DO UPDATE SET
      section_number = excluded.section_number, answer = excluded.answer,
      is_correct = excluded.is_correct, correct_answer = excluded.correct_answer,
      explanation_page = excluded.explanation_page, saved_at = excluded.saved_at,
      graded_at = excluded.graded_at`)
      .bind(
        crypto.randomUUID(), attemptId, userId, item.sectionNumber, item.questionNumber,
        item.answer, item.isCorrect ? 1 : 0, item.correctAnswer, item.explanationPage, savedAt, savedAt,
      ));
    await getD1().batch(statements);
  }

  async completeAttempt(userId: string, attemptId: string, input: CompleteIeltsAttemptInput): Promise<void> {
    const result = await getD1().prepare(`UPDATE ielts_attempts SET
      status = 'completed', raw_score = ?, estimated_band = ?, notes = ?,
      completed_at = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ? AND user_id = ?`)
      .bind(input.rawScore, input.estimatedBand, input.notes, new Date().toISOString(), attemptId, userId).run();
    if (!result.meta.changes) throw new Error("IELTS practice attempt not found.");
  }

  private async assertActiveAttempt(userId: string, attemptId: string): Promise<void> {
    const row = await getD1().prepare(
      "SELECT id FROM ielts_attempts WHERE id = ? AND user_id = ? AND status = 'in_progress'",
    ).bind(attemptId, userId).first<{ id: string }>();
    if (!row) throw new Error("Active IELTS attempt not found.");
  }
}
