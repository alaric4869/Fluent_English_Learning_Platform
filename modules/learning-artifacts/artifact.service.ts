import { getD1 } from "../../db";
import { shiftDate } from "../../db/bootstrap";
import type { ReviewRepository } from "../review/review.repository";
import type { SavedSentenceDto, SentenceStatus, VocabularyItemDto } from "../shared/contracts";

export class LearningArtifactService {
  constructor(private readonly reviews: ReviewRepository) {}

  async listVocabulary(userId: string): Promise<VocabularyItemDto[]> {
    const result = await getD1().prepare(`SELECT id, phrase, meaning, example, source_resource_id, date_learned,
      personal_note, difficulty, mastery, is_favorite FROM vocabulary_items
      WHERE user_id = ? ORDER BY created_at DESC`)
      .bind(userId).all<{
        id: string; phrase: string; meaning: string; example: string; source_resource_id: string | null;
        date_learned: string; personal_note: string; difficulty: string; mastery: VocabularyItemDto["mastery"]; is_favorite: number;
      }>();
    return result.results.map((row) => ({
      id: row.id,
      phrase: row.phrase,
      meaning: row.meaning,
      example: row.example,
      sourceResourceId: row.source_resource_id,
      dateLearned: row.date_learned,
      personalNote: row.personal_note,
      difficulty: row.difficulty,
      mastery: row.mastery,
      isFavorite: Boolean(row.is_favorite),
    }));
  }

  async listSavedSentences(userId: string): Promise<SavedSentenceDto[]> {
    const result = await getD1().prepare(`SELECT id, resource_id, sentence_index, sentence, status
      FROM saved_sentences WHERE user_id = ? ORDER BY created_at DESC`)
      .bind(userId).all<{ id: string; resource_id: string; sentence_index: number; sentence: string; status: SentenceStatus }>();
    return result.results.map((row) => ({
      id: row.id,
      resourceId: row.resource_id,
      sentenceIndex: row.sentence_index,
      sentence: row.sentence,
      status: row.status,
    }));
  }

  async addVocabulary(input: {
    userId: string; phrase: string; meaning: string; example: string; sourceResourceId?: string;
    personalNote?: string; date: string;
  }) {
    if (!input.phrase.trim() || !input.meaning.trim()) throw new Error("Phrase and meaning are required.");
    const id = crypto.randomUUID();
    await getD1().prepare(`INSERT INTO vocabulary_items (
      id, user_id, phrase, meaning, example, source_resource_id, date_learned, personal_note
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, input.userId, input.phrase.trim(), input.meaning.trim(), input.example.trim(), input.sourceResourceId ?? null, input.date, input.personalNote?.trim() ?? "").run();
    await this.reviews.create({
      userId: input.userId,
      targetType: "vocabulary",
      targetId: id,
      prompt: input.phrase.trim(),
      answer: `${input.meaning.trim()} — ${input.example.trim()}`,
      dueDate: shiftDate(input.date, 1),
    });
  }

  async saveSentence(input: {
    userId: string; resourceId: string; sentenceIndex: number; sentence: string; status: SentenceStatus; date: string;
  }) {
    const existing = await getD1().prepare(`SELECT id FROM saved_sentences
      WHERE user_id = ? AND resource_id = ? AND sentence_index = ?`)
      .bind(input.userId, input.resourceId, input.sentenceIndex).first<{ id: string }>();
    const id = existing?.id ?? crypto.randomUUID();
    await getD1().prepare(`INSERT INTO saved_sentences (
      id, user_id, resource_id, sentence_index, sentence, status
    ) VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(user_id, resource_id, sentence_index)
      DO UPDATE SET sentence = excluded.sentence, status = excluded.status`)
      .bind(id, input.userId, input.resourceId, input.sentenceIndex, input.sentence, input.status).run();
    if (["couldnt_hear", "difficult", "need_practice"].includes(input.status)) {
      await this.reviews.create({
        userId: input.userId,
        targetType: "sentence",
        targetId: id,
        prompt: "Listen or read, then reproduce this sentence:",
        answer: input.sentence,
        dueDate: shiftDate(input.date, 1),
      });
    }
  }
}
