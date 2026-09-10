import { getD1 } from "../../db";
import { shiftDate } from "../../db/bootstrap";
import type { HistoryDayDto, ProgressDto, StudyModule } from "../shared/contracts";

const MODULES: StudyModule[] = ["listening", "speaking", "reading", "vocabulary"];

export class ProgressService {
  async getHistory(userId: string): Promise<HistoryDayDto[]> {
    const days = await getD1().prepare(`SELECT id, study_date, theme FROM study_days
      WHERE user_id = ? ORDER BY study_date DESC LIMIT 120`)
      .bind(userId).all<{ id: string; study_date: string; theme: string }>();

    return Promise.all(days.results.map(async (day) => {
      const items = await getD1().prepare(`SELECT p.id, p.module, p.status, p.target_minutes, r.title,
        COALESCE((SELECT SUM(active_seconds) FROM study_sessions s WHERE s.plan_item_id = p.id), 0) AS active_seconds
        FROM study_plan_items p JOIN learning_resources r ON r.id = p.resource_id
        WHERE p.study_day_id = ? ORDER BY p.position`)
        .bind(day.id).all<{
          id: string; module: StudyModule; status: "not_started" | "in_progress" | "completed";
          target_minutes: number; title: string; active_seconds: number;
        }>();
      return {
        date: day.study_date,
        theme: day.theme,
        completedModules: items.results.filter((item) => item.status === "completed").map((item) => item.module),
        totalModules: items.results.length,
        studyMinutes: Math.round(items.results.reduce((sum, item) => sum + item.active_seconds, 0) / 60),
        planItems: items.results.map((item) => ({
          id: item.id,
          module: item.module,
          status: item.status,
          targetMinutes: item.target_minutes,
          title: item.title,
        })),
      } satisfies HistoryDayDto;
    }));
  }

  async getProgress(userId: string, today: string, history?: HistoryDayDto[]): Promise<ProgressDto> {
    const days = history ?? await this.getHistory(userId);
    const completedDays = days.filter((day) => day.completedModules.length > 0).map((day) => day.date).sort();
    const streaks = calculateStreaks(completedDays, today);
    const weekStart = shiftDate(today, -6);
    const recentDays = Array.from({ length: 7 }, (_, index) => shiftDate(today, index - 6));
    const dayMap = new Map(days.map((day) => [day.date, day.studyMinutes]));

    const [vocabulary, reviewAttempts, signals] = await Promise.all([
      getD1().prepare(`SELECT COUNT(*) AS total,
        SUM(CASE WHEN mastery = 'mastered' THEN 1 ELSE 0 END) AS mastered
        FROM vocabulary_items WHERE user_id = ?`).bind(userId).first<{ total: number; mastered: number | null }>(),
      getD1().prepare("SELECT COUNT(*) AS total FROM review_attempts WHERE user_id = ?")
        .bind(userId).first<{ total: number }>(),
      getD1().prepare(`SELECT module,
        AVG(CASE WHEN signal_type = 'difficulty' THEN numeric_value END) AS difficulty,
        AVG(CASE WHEN signal_type = 'confidence' THEN numeric_value END) AS confidence,
        COUNT(DISTINCT plan_item_id) AS samples
        FROM performance_signals WHERE user_id = ? GROUP BY module`)
        .bind(userId).all<{ module: StudyModule; difficulty: number | null; confidence: number | null; samples: number }>(),
    ]);

    const allItems = days.flatMap((day) => day.planItems);
    const completedItems = allItems.filter((item) => item.status === "completed");
    const moduleCompletions = Object.fromEntries(MODULES.map((module) => [module, completedItems.filter((item) => item.module === module).length])) as Record<StudyModule, number>;
    const totalStudyMinutes = days.reduce((sum, day) => sum + day.studyMinutes, 0);

    return {
      currentStreak: streaks.current,
      longestStreak: streaks.longest,
      totalStudyDays: completedDays.length,
      totalStudyMinutes,
      thisWeekMinutes: days.filter((day) => day.date >= weekStart && day.date <= today).reduce((sum, day) => sum + day.studyMinutes, 0),
      completionRate: allItems.length ? Math.round((completedItems.length / allItems.length) * 100) : 0,
      vocabularyLearned: vocabulary?.total ?? 0,
      vocabularyMastered: vocabulary?.mastered ?? 0,
      reviewsCompleted: reviewAttempts?.total ?? 0,
      moduleCompletions,
      weeklyActivity: recentDays.map((date) => ({ date, minutes: dayMap.get(date) ?? 0 })),
      skillScores: MODULES.map((module) => {
        const signal = signals.results.find((item) => item.module === module);
        const score = signal
          ? Math.round((((6 - (signal.difficulty ?? 3)) + (signal.confidence ?? 3)) / 10) * 100)
          : 50;
        return { module, score, label: signal ? scoreLabel(score) : "Building baseline", sampleCount: signal?.samples ?? 0 };
      }),
    };
  }
}

function calculateStreaks(dates: string[], today: string) {
  if (!dates.length) return { current: 0, longest: 0 };
  const unique = [...new Set(dates)].sort();
  let longest = 1;
  let run = 1;
  for (let index = 1; index < unique.length; index += 1) {
    if (shiftDate(unique[index - 1], 1) === unique[index]) run += 1;
    else run = 1;
    longest = Math.max(longest, run);
  }
  let current = 0;
  let cursor = unique.includes(today) ? today : shiftDate(today, -1);
  while (unique.includes(cursor)) {
    current += 1;
    cursor = shiftDate(cursor, -1);
  }
  return { current, longest };
}

function scoreLabel(score: number): string {
  if (score >= 72) return "Strong";
  if (score >= 58) return "Developing";
  return "Needs attention";
}
