import { getD1 } from "../../db";
import type { LearningResourceDto, StudyPlanItemDto, StudyModule } from "../shared/contracts";
import { mapResourceRow } from "../resources/d1-resource.repository";
import type { GeneratedStudyPlan, ModulePerformance } from "./study-plan-generator";
import type { StudyDayRecord, StudyPlanRepository } from "./study-plan.repository";

interface DayRow { id: string; study_date: string; theme: string; target_minutes: number; adaptation_reasons_json: string }

interface PlanRow {
  id: string;
  module: StudyModule;
  target_minutes: number;
  status: StudyPlanItemDto["status"];
  notes: string;
  difficulty_rating: number | null;
  confidence_rating: number | null;
  instructions_json: string;
  objectives_json: string;
  assignment_source: string;
  resource: string;
}

export class D1StudyPlanRepository implements StudyPlanRepository {
  async getDay(userId: string, date: string): Promise<StudyDayRecord | null> {
    const row = await getD1()
      .prepare("SELECT id, study_date, theme, target_minutes, adaptation_reasons_json FROM study_days WHERE user_id = ? AND study_date = ?")
      .bind(userId, date)
      .first<DayRow>();
    return row ? mapDay(row) : null;
  }

  async createDay(userId: string, date: string, plan: GeneratedStudyPlan): Promise<StudyDayRecord> {
    const d1 = getD1();
    const dayId = crypto.randomUUID();
    const statements = [
      d1.prepare(`INSERT INTO study_days (id, user_id, study_date, theme, target_minutes, adaptation_reasons_json)
        VALUES (?, ?, ?, ?, ?, ?)`)
        .bind(dayId, userId, date, plan.theme, plan.targetMinutes, JSON.stringify(plan.adaptationReasons)),
      ...plan.items.map((item, index) =>
        d1.prepare(`INSERT INTO study_plan_items (
          id, study_day_id, resource_id, module, position, target_minutes, instructions_json,
          objectives_json, resource_snapshot_json, assignment_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'rule_based')`)
          .bind(
            crypto.randomUUID(),
            dayId,
            item.resource.id,
            item.module,
            index,
            item.targetMinutes,
            JSON.stringify(item.instructions),
            JSON.stringify(item.objectives),
            JSON.stringify(item.resource),
          ),
      ),
    ];
    await d1.batch(statements);
    return { id: dayId, date, theme: plan.theme, targetMinutes: plan.targetMinutes, adaptationReasons: plan.adaptationReasons };
  }

  async listItems(userId: string, dayId: string): Promise<StudyPlanItemDto[]> {
    const result = await getD1()
      .prepare(`SELECT p.id, p.module, p.target_minutes, p.status, p.notes, p.difficulty_rating,
        p.confidence_rating, p.instructions_json, p.objectives_json, p.assignment_source,
        json_object(
          'id', r.id, 'type', r.type, 'module', r.module, 'title', r.title, 'source', r.source,
          'url', r.url, 'topic', r.topic, 'difficulty', r.difficulty, 'duration_minutes', r.duration_minutes,
          'priority', r.priority, 'tags_json', r.tags_json, 'content_json', r.content_json,
          'is_favorite', COALESCE(s.is_favorite, 0), 'is_archived', r.is_archived,
          'created_at', r.created_at, 'last_studied_at', r.last_studied_at
        ) AS resource
        FROM study_plan_items p
        JOIN study_days d ON d.id = p.study_day_id
        JOIN learning_resources r ON r.id = p.resource_id
        LEFT JOIN resource_user_states s ON s.resource_id = r.id AND s.user_id = ?
        WHERE p.study_day_id = ? AND d.user_id = ?
        ORDER BY p.position`)
      .bind(userId, dayId, userId)
      .all<PlanRow>();
    return result.results.map(mapPlanRow);
  }

  async getItem(userId: string, planItemId: string): Promise<StudyPlanItemDto | null> {
    const row = await getD1()
      .prepare(`SELECT p.id, p.module, p.target_minutes, p.status, p.notes, p.difficulty_rating,
        p.confidence_rating, p.instructions_json, p.objectives_json, p.assignment_source,
        json_object(
          'id', r.id, 'type', r.type, 'module', r.module, 'title', r.title, 'source', r.source,
          'url', r.url, 'topic', r.topic, 'difficulty', r.difficulty, 'duration_minutes', r.duration_minutes,
          'priority', r.priority, 'tags_json', r.tags_json, 'content_json', r.content_json,
          'is_favorite', COALESCE(s.is_favorite, 0), 'is_archived', r.is_archived,
          'created_at', r.created_at, 'last_studied_at', r.last_studied_at
        ) AS resource
        FROM study_plan_items p
        JOIN study_days d ON d.id = p.study_day_id
        JOIN learning_resources r ON r.id = p.resource_id
        LEFT JOIN resource_user_states s ON s.resource_id = r.id AND s.user_id = ?
        WHERE p.id = ? AND d.user_id = ?`)
      .bind(userId, planItemId, userId)
      .first<PlanRow>();
    return row ? mapPlanRow(row) : null;
  }

  async listRecentResourceIds(userId: string, limit: number): Promise<string[]> {
    const result = await getD1()
      .prepare(`SELECT p.resource_id FROM study_plan_items p
        JOIN study_days d ON d.id = p.study_day_id
        WHERE d.user_id = ? ORDER BY d.study_date DESC, p.position LIMIT ?`)
      .bind(userId, limit)
      .all<{ resource_id: string }>();
    return result.results.map((row) => row.resource_id);
  }

  async getPerformance(userId: string): Promise<ModulePerformance[]> {
    const result = await getD1()
      .prepare(`SELECT module,
        AVG(CASE WHEN signal_type = 'difficulty' THEN numeric_value END) AS average_difficulty,
        AVG(CASE WHEN signal_type = 'confidence' THEN numeric_value END) AS average_confidence,
        COUNT(DISTINCT plan_item_id) AS sample_count
        FROM performance_signals
        WHERE user_id = ? AND observed_at >= datetime('now', '-28 days')
        GROUP BY module`)
      .bind(userId)
      .all<{ module: StudyModule; average_difficulty: number | null; average_confidence: number | null; sample_count: number }>();
    return result.results.map((row) => ({
      module: row.module,
      averageDifficulty: row.average_difficulty,
      averageConfidence: row.average_confidence,
      sampleCount: row.sample_count,
    }));
  }

  async startSession(userId: string, planItemId: string): Promise<void> {
    const d1 = getD1();
    const open = await d1.prepare("SELECT id FROM study_sessions WHERE user_id = ? AND plan_item_id = ? AND completed_at IS NULL")
      .bind(userId, planItemId).first<{ id: string }>();
    if (!open) {
      await d1.batch([
        d1.prepare("INSERT INTO study_sessions (id, user_id, plan_item_id, started_at) VALUES (?, ?, ?, ?)")
          .bind(crypto.randomUUID(), userId, planItemId, new Date().toISOString()),
        d1.prepare("UPDATE study_plan_items SET status = 'in_progress' WHERE id = ? AND status = 'not_started'").bind(planItemId),
      ]);
    }
  }

  async completeItem(userId: string, planItemId: string, activeSeconds: number): Promise<void> {
    const d1 = getD1();
    const now = new Date().toISOString();
    const item = await this.getItem(userId, planItemId);
    if (!item) throw new Error("Study item not found.");
    const session = await d1.prepare("SELECT id FROM study_sessions WHERE user_id = ? AND plan_item_id = ? AND completed_at IS NULL")
      .bind(userId, planItemId).first<{ id: string }>();
    const statements = [
      d1.prepare("UPDATE study_plan_items SET status = 'completed', completed_at = ? WHERE id = ?").bind(now, planItemId),
      d1.prepare("UPDATE learning_resources SET last_studied_at = ?, updated_at = ? WHERE id = ?").bind(now, now, item.resource.id),
    ];
    if (session) {
      statements.push(d1.prepare("UPDATE study_sessions SET completed_at = ?, active_seconds = ? WHERE id = ?")
        .bind(now, Math.max(activeSeconds, 60), session.id));
    } else {
      statements.push(d1.prepare("INSERT INTO study_sessions (id, user_id, plan_item_id, started_at, completed_at, active_seconds) VALUES (?, ?, ?, ?, ?, ?)")
        .bind(crypto.randomUUID(), userId, planItemId, now, now, Math.max(activeSeconds, item.targetMinutes * 60)));
    }
    await d1.batch(statements);
  }

  async saveNotes(userId: string, planItemId: string, notes: string): Promise<void> {
    await getD1().prepare(`UPDATE study_plan_items SET notes = ? WHERE id = ? AND study_day_id IN
      (SELECT id FROM study_days WHERE user_id = ?)`)
      .bind(notes.slice(0, 4000), planItemId, userId).run();
  }

  async rateItem(userId: string, planItemId: string, module: StudyModule, difficulty: number, confidence: number): Promise<void> {
    const d1 = getD1();
    await d1.batch([
      d1.prepare(`UPDATE study_plan_items SET difficulty_rating = ?, confidence_rating = ?
        WHERE id = ? AND study_day_id IN (SELECT id FROM study_days WHERE user_id = ?)`)
        .bind(difficulty, confidence, planItemId, userId),
      d1.prepare("INSERT INTO performance_signals (id, user_id, module, signal_type, numeric_value, plan_item_id) VALUES (?, ?, ?, 'difficulty', ?, ?)")
        .bind(crypto.randomUUID(), userId, module, difficulty, planItemId),
      d1.prepare("INSERT INTO performance_signals (id, user_id, module, signal_type, numeric_value, plan_item_id) VALUES (?, ?, ?, 'confidence', ?, ?)")
        .bind(crypto.randomUUID(), userId, module, confidence, planItemId),
    ]);
  }

  async replaceResource(userId: string, planItemId: string, resource: LearningResourceDto): Promise<void> {
    await getD1().prepare(`UPDATE study_plan_items
      SET resource_id = ?, resource_snapshot_json = ?, assignment_source = 'manual_override'
      WHERE id = ? AND status != 'completed' AND study_day_id IN (SELECT id FROM study_days WHERE user_id = ?)`)
      .bind(resource.id, JSON.stringify(resource), planItemId, userId).run();
  }
}

function mapDay(row: DayRow): StudyDayRecord {
  return {
    id: row.id,
    date: row.study_date,
    theme: row.theme,
    targetMinutes: row.target_minutes,
    adaptationReasons: parseJson<string[]>(row.adaptation_reasons_json, []),
  };
}

function mapPlanRow(row: PlanRow): StudyPlanItemDto {
  const resourceRow = parseJson<Record<string, unknown>>(row.resource, {});
  return {
    id: row.id,
    module: row.module,
    targetMinutes: row.target_minutes,
    status: row.status,
    notes: row.notes,
    difficultyRating: row.difficulty_rating,
    confidenceRating: row.confidence_rating,
    instructions: parseJson<string[]>(row.instructions_json, []),
    objectives: parseJson<string[]>(row.objectives_json, []),
    assignmentSource: row.assignment_source,
    resource: mapResourceRow(resourceRow as never),
  };
}

function parseJson<T>(value: string, fallback: T): T {
  try { return JSON.parse(value) as T; } catch { return fallback; }
}
