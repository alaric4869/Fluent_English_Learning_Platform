import type { LearningResourceDto, StudyPlanItemDto, StudyModule } from "../shared/contracts";
import type { GeneratedStudyPlan, ModulePerformance } from "./study-plan-generator";

export interface StudyDayRecord {
  id: string;
  date: string;
  theme: string;
  targetMinutes: number;
  adaptationReasons: string[];
}

export interface StudyPlanRepository {
  getDay(userId: string, date: string): Promise<StudyDayRecord | null>;
  createDay(userId: string, date: string, plan: GeneratedStudyPlan): Promise<StudyDayRecord>;
  listItems(userId: string, dayId: string): Promise<StudyPlanItemDto[]>;
  getItem(userId: string, planItemId: string): Promise<StudyPlanItemDto | null>;
  listRecentResourceIds(userId: string, limit: number): Promise<string[]>;
  getPerformance(userId: string): Promise<ModulePerformance[]>;
  startSession(userId: string, planItemId: string): Promise<void>;
  completeItem(userId: string, planItemId: string, activeSeconds: number): Promise<void>;
  saveNotes(userId: string, planItemId: string, notes: string): Promise<void>;
  rateItem(userId: string, planItemId: string, module: StudyModule, difficulty: number, confidence: number): Promise<void>;
  replaceResource(userId: string, planItemId: string, resource: LearningResourceDto): Promise<void>;
}
