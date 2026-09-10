import { getD1 } from "../../db";
import type { LearningResourceDto, ResourceContent } from "../shared/contracts";
import type { NewResourceInput, ResourceRepository } from "./resource.repository";

interface ResourceRow {
  id: string;
  type: LearningResourceDto["type"];
  module: LearningResourceDto["module"];
  title: string;
  source: string;
  url: string | null;
  topic: string;
  difficulty: LearningResourceDto["difficulty"];
  duration_minutes: number;
  priority: number;
  tags_json: string;
  content_json: string;
  is_favorite: number;
  is_archived: number;
  created_at: string;
  last_studied_at: string | null;
}

export class D1ResourceRepository implements ResourceRepository {
  async list(userId: string, includeArchived = false): Promise<LearningResourceDto[]> {
    const result = await getD1()
      .prepare(`SELECT r.*, COALESCE(s.is_favorite, 0) AS is_favorite
        FROM learning_resources r
        LEFT JOIN resource_user_states s
          ON s.resource_id = r.id AND s.user_id = ?
        WHERE (? = 1 OR r.is_archived = 0)
          AND (r.owner_user_id IS NULL OR r.owner_user_id = ?)
        ORDER BY r.created_at DESC, r.priority DESC`)
      .bind(userId, includeArchived ? 1 : 0, userId)
      .all<ResourceRow>();
    return result.results.map(mapResourceRow);
  }

  async get(userId: string, resourceId: string): Promise<LearningResourceDto | null> {
    const row = await getD1()
      .prepare(`SELECT r.*, COALESCE(s.is_favorite, 0) AS is_favorite
        FROM learning_resources r
        LEFT JOIN resource_user_states s
          ON s.resource_id = r.id AND s.user_id = ?
        WHERE r.id = ? AND (r.owner_user_id IS NULL OR r.owner_user_id = ?)`)
      .bind(userId, resourceId, userId)
      .first<ResourceRow>();
    return row ? mapResourceRow(row) : null;
  }

  async create(userId: string, input: NewResourceInput): Promise<string> {
    const id = crypto.randomUUID();
    await getD1()
      .prepare(`INSERT INTO learning_resources (
        id, owner_user_id, type, module, title, source, url, topic, difficulty,
        duration_minutes, priority, tags_json, content_json, is_archived
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 50, ?, ?, 0)`)
      .bind(
        id,
        userId,
        input.type,
        input.module,
        input.title,
        input.source,
        input.url,
        input.topic,
        input.difficulty,
        input.durationMinutes,
        JSON.stringify(input.tags),
        JSON.stringify(input.content),
      )
      .run();
    return id;
  }

  async update(userId: string, resourceId: string, changes: Pick<LearningResourceDto, "title" | "source" | "url" | "topic" | "difficulty" | "durationMinutes" | "tags" | "content">): Promise<void> {
    await getD1().prepare(`UPDATE learning_resources SET
      title = ?, source = ?, url = ?, topic = ?, difficulty = ?, duration_minutes = ?,
      tags_json = ?, content_json = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ? AND owner_user_id = ?`)
      .bind(
        changes.title,
        changes.source,
        changes.url,
        changes.topic,
        changes.difficulty,
        changes.durationMinutes,
        JSON.stringify(changes.tags),
        JSON.stringify(changes.content),
        resourceId,
        userId,
      )
      .run();
  }

  async toggleFavorite(userId: string, resourceId: string): Promise<void> {
    await getD1()
      .prepare(`INSERT INTO resource_user_states (user_id, resource_id, is_favorite, saved_for_later)
        VALUES (?, ?, 1, 0)
        ON CONFLICT(user_id, resource_id)
        DO UPDATE SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END`)
      .bind(userId, resourceId)
      .run();
  }

  async archive(userId: string, resourceId: string): Promise<void> {
    await getD1()
      .prepare("UPDATE learning_resources SET is_archived = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND owner_user_id = ?")
      .bind(resourceId, userId)
      .run();
  }

  async markStudied(resourceId: string, studiedAt: string): Promise<void> {
    await getD1()
      .prepare("UPDATE learning_resources SET last_studied_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?")
      .bind(studiedAt, resourceId)
      .run();
  }
}

export function mapResourceRow(row: ResourceRow): LearningResourceDto {
  return {
    id: row.id,
    type: row.type,
    module: row.module,
    title: row.title,
    source: row.source,
    url: row.url,
    topic: row.topic,
    difficulty: row.difficulty,
    durationMinutes: row.duration_minutes,
    priority: row.priority,
    tags: safeJson<string[]>(row.tags_json, []),
    content: safeJson<ResourceContent>(row.content_json, { summary: "" }),
    isFavorite: Boolean(row.is_favorite),
    isArchived: Boolean(row.is_archived),
    createdAt: row.created_at,
    lastStudiedAt: row.last_studied_at,
  };
}

function safeJson<T>(value: string, fallback: T): T {
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}
