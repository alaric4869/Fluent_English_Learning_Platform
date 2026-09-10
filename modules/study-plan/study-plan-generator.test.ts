import { describe, expect, it } from "vitest";
import type { LearningResourceDto, StudyModule } from "../shared/contracts";
import { RuleBasedStudyPlanGenerator } from "./study-plan-generator";

const modules: StudyModule[] = ["listening", "speaking", "reading", "vocabulary"];

function resource(module: StudyModule, suffix: string, topic: string, priority = 80): LearningResourceDto {
  return {
    id: `${module}-${suffix}`,
    type: module,
    module,
    title: `${module} ${suffix}`,
    source: "test",
    url: null,
    topic,
    difficulty: "comfortable",
    durationMinutes: 25,
    priority,
    tags: [],
    content: { summary: "test" },
    isFavorite: false,
    isArchived: false,
    createdAt: "2026-09-01",
    lastStudiedAt: null,
  };
}

describe("RuleBasedStudyPlanGenerator", () => {
  const generator = new RuleBasedStudyPlanGenerator();
  const resources = modules.flatMap((module) => [
    resource(module, "coffee", "Ordering food and coffee", 70),
    resource(module, "appointments", "Making and changing appointments", 70),
    resource(module, "general", "Daily life", 90),
  ]);

  it("always creates one item per module and preserves the baseline budget", () => {
    const plan = generator.generate({ date: "2026-09-11", resources, recentResourceIds: [], performance: [] });
    expect(plan.items.map((item) => item.module)).toEqual(modules);
    expect(plan.targetMinutes).toBe(110);
    expect(plan.adaptationReasons).toEqual([]);
  });

  it("penalizes recently assigned resources", () => {
    const first = generator.generate({ date: "2026-09-11", resources, recentResourceIds: [], performance: [] });
    const second = generator.generate({ date: "2026-09-11", resources, recentResourceIds: first.items.map((item) => item.resource.id), performance: [] });
    expect(second.items.every((item, index) => item.resource.id !== first.items[index].resource.id)).toBe(true);
  });

  it("moves only five minutes from the strongest to the weakest skill", () => {
    const plan = generator.generate({
      date: "2026-09-11",
      resources,
      recentResourceIds: [],
      performance: [
        { module: "listening", averageDifficulty: 4.5, averageConfidence: 2, sampleCount: 4 },
        { module: "reading", averageDifficulty: 2, averageConfidence: 4.5, sampleCount: 4 },
      ],
    });
    expect(plan.items.find((item) => item.module === "listening")?.targetMinutes).toBe(35);
    expect(plan.items.find((item) => item.module === "reading")?.targetMinutes).toBe(25);
    expect(plan.targetMinutes).toBe(110);
    expect(plan.adaptationReasons).toHaveLength(2);
  });
});
