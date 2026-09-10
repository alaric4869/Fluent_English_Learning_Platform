import { getD1 } from "../../db";
import type { NotebookEntryDto } from "../shared/contracts";

export class NotebookService {
  async list(userId: string): Promise<NotebookEntryDto[]> {
    const result = await getD1().prepare(`SELECT n.id, n.type, n.title, n.content, n.source_resource_id,
      n.is_favorite, n.created_at, r.title AS source_title
      FROM notebook_entries n LEFT JOIN learning_resources r ON r.id = n.source_resource_id
      WHERE n.user_id = ? ORDER BY n.created_at DESC`)
      .bind(userId).all<{
        id: string; type: NotebookEntryDto["type"]; title: string; content: string;
        source_resource_id: string | null; source_title: string | null; is_favorite: number; created_at: string;
      }>();
    return result.results.map((row) => ({
      id: row.id,
      type: row.type,
      title: row.title,
      content: row.content,
      sourceResourceId: row.source_resource_id,
      sourceTitle: row.source_title,
      isFavorite: Boolean(row.is_favorite),
      createdAt: row.created_at,
    }));
  }

  async add(input: {
    userId: string; type: NotebookEntryDto["type"]; title: string; content: string; sourceResourceId?: string;
  }) {
    if (!input.title.trim() || !input.content.trim()) throw new Error("Title and note content are required.");
    await getD1().prepare(`INSERT INTO notebook_entries (
      id, user_id, type, title, content, source_resource_id
    ) VALUES (?, ?, ?, ?, ?, ?)`)
      .bind(crypto.randomUUID(), input.userId, input.type, input.title.trim(), input.content.trim(), input.sourceResourceId ?? null).run();
  }
}
