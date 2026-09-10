import type { LearningResourceDto, StudyModule } from "../shared/contracts";
import { MODULE_COPY, STUDY_PLAN_CONFIG } from "./study-plan.config";

export interface ModulePerformance {
  module: StudyModule;
  averageDifficulty: number | null;
  averageConfidence: number | null;
  sampleCount: number;
}

export interface GeneratedPlanItem {
  module: StudyModule;
  targetMinutes: number;
  resource: LearningResourceDto;
  instructions: string[];
  objectives: string[];
}

export interface GeneratedStudyPlan {
  theme: string;
  targetMinutes: number;
  adaptationReasons: string[];
  items: GeneratedPlanItem[];
}

export interface StudyPlanGenerator {
  generate(input: {
    date: string;
    resources: LearningResourceDto[];
    recentResourceIds: string[];
    performance: ModulePerformance[];
  }): GeneratedStudyPlan;
}

export class RuleBasedStudyPlanGenerator implements StudyPlanGenerator {
  generate(input: {
    date: string;
    resources: LearningResourceDto[];
    recentResourceIds: string[];
    performance: ModulePerformance[];
  }): GeneratedStudyPlan {
    const dateIndex = dateToIndex(input.date);
    const theme = STUDY_PLAN_CONFIG.themes[dateIndex % STUDY_PLAN_CONFIG.themes.length];
    const { minutes, reasons } = calculateAdaptiveMinutes(input.performance);
    const modules: StudyModule[] = ["listening", "speaking", "reading", "vocabulary"];

    const items = modules.map((module, moduleIndex) => {
      const candidates = input.resources.filter((resource) => resource.module === module && !resource.isArchived);
      if (candidates.length === 0) throw new Error(`No active ${module} resources are available.`);
      const resource = [...candidates].sort((a, b) => {
        const scoreDifference = scoreResource(b, theme, input.recentResourceIds) - scoreResource(a, theme, input.recentResourceIds);
        if (scoreDifference !== 0) return scoreDifference;
        return stableHash(`${input.date}-${moduleIndex}-${a.id}`) - stableHash(`${input.date}-${moduleIndex}-${b.id}`);
      })[0];

      return {
        module,
        targetMinutes: minutes[module],
        resource,
        instructions: MODULE_COPY[module].instructions,
        objectives: MODULE_COPY[module].objectives,
      };
    });

    return {
      theme,
      targetMinutes: Object.values(minutes).reduce((total, value) => total + value, 0),
      adaptationReasons: reasons,
      items,
    };
  }
}

function calculateAdaptiveMinutes(performance: ModulePerformance[]) {
  const minutes = { ...STUDY_PLAN_CONFIG.baseMinutes };
  const eligible = performance.filter((item) => item.sampleCount >= 2);
  if (eligible.length < 2) {
    return { minutes, reasons: [] as string[] };
  }

  const weaknessScore = (item: ModulePerformance) =>
    (item.averageDifficulty ?? 3) * 12 + (6 - (item.averageConfidence ?? 3)) * 10;
  const weakest = [...eligible].sort((a, b) => weaknessScore(b) - weaknessScore(a))[0];
  const strongest = [...eligible].sort((a, b) => weaknessScore(a) - weaknessScore(b))[0];
  if (weakest.module === strongest.module || weaknessScore(weakest) - weaknessScore(strongest) < 12) {
    return { minutes, reasons: [] as string[] };
  }

  const adjustment = STUDY_PLAN_CONFIG.maximumDailyAdjustment;
  minutes[weakest.module] = Math.min(STUDY_PLAN_CONFIG.maximumMinutes[weakest.module], minutes[weakest.module] + adjustment);
  minutes[strongest.module] = Math.max(STUDY_PLAN_CONFIG.minimumMinutes[strongest.module], minutes[strongest.module] - adjustment);
  return {
    minutes,
    reasons: [
      `${label(weakest.module)} received ${adjustment} extra minutes because recent difficulty averaged ${format(weakest.averageDifficulty)}/5 and confidence averaged ${format(weakest.averageConfidence)}/5.`,
      `${label(strongest.module)} was reduced by ${adjustment} minutes to keep today's total study time stable.`,
    ],
  };
}

function scoreResource(resource: LearningResourceDto, theme: string, recentResourceIds: string[]): number {
  let score = resource.priority;
  if (resource.topic === theme) score += 80;
  if (!resource.lastStudiedAt) score += 25;
  const recentIndex = recentResourceIds.indexOf(resource.id);
  if (recentIndex >= 0) score -= 90 - recentIndex * 8;
  if (resource.isFavorite) score += 5;
  return score;
}

function dateToIndex(date: string): number {
  const [year, month, day] = date.split("-").map(Number);
  return Math.floor(Date.UTC(year, month - 1, day) / 86_400_000);
}

function stableHash(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  return hash;
}

function label(module: StudyModule): string {
  return module.charAt(0).toUpperCase() + module.slice(1);
}

function format(value: number | null): string {
  return value === null ? "—" : value.toFixed(1);
}
