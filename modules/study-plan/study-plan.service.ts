import type { ResourceRepository } from "../resources/resource.repository";
import type { StudyModule } from "../shared/contracts";
import type { StudyPlanGenerator } from "./study-plan-generator";
import type { StudyPlanRepository } from "./study-plan.repository";
import { STUDY_PLAN_CONFIG } from "./study-plan.config";

export class StudyPlanService {
  constructor(
    private readonly plans: StudyPlanRepository,
    private readonly resources: ResourceRepository,
    private readonly generator: StudyPlanGenerator,
  ) {}

  async getOrCreateToday(userId: string, date: string) {
    let day = await this.plans.getDay(userId, date);
    if (!day) {
      const [resources, recentResourceIds, performance] = await Promise.all([
        this.resources.list(userId),
        this.plans.listRecentResourceIds(userId, STUDY_PLAN_CONFIG.recentResourceCooldown * 4),
        this.plans.getPerformance(userId),
      ]);
      day = await this.plans.createDay(userId, date, this.generator.generate({ date, resources, recentResourceIds, performance }));
    }
    return { ...day, planItems: await this.plans.listItems(userId, day.id) };
  }

  start(userId: string, planItemId: string) {
    return this.plans.startSession(userId, planItemId);
  }

  complete(userId: string, planItemId: string, activeSeconds = 0) {
    return this.plans.completeItem(userId, planItemId, activeSeconds);
  }

  saveNotes(userId: string, planItemId: string, notes: string) {
    return this.plans.saveNotes(userId, planItemId, notes);
  }

  async rate(userId: string, planItemId: string, difficulty: number, confidence: number) {
    if (![difficulty, confidence].every((value) => Number.isInteger(value) && value >= 1 && value <= 5)) {
      throw new Error("Ratings must be whole numbers from 1 to 5.");
    }
    const item = await this.plans.getItem(userId, planItemId);
    if (!item) throw new Error("Study item not found.");
    return this.plans.rateItem(userId, planItemId, item.module, difficulty, confidence);
  }

  async replace(userId: string, planItemId: string) {
    const [item, resources, recent] = await Promise.all([
      this.plans.getItem(userId, planItemId),
      this.resources.list(userId),
      this.plans.listRecentResourceIds(userId, 20),
    ]);
    if (!item) throw new Error("Study item not found.");
    const alternatives = resources
      .filter((resource) => resource.module === item.module && resource.id !== item.resource.id && !resource.isArchived)
      .sort((a, b) => scoreAlternative(b, item.module, recent) - scoreAlternative(a, item.module, recent));
    if (!alternatives[0]) throw new Error("No alternative resource is available yet.");
    return this.plans.replaceResource(userId, planItemId, alternatives[0]);
  }
}

function scoreAlternative(resource: { id: string; priority: number; lastStudiedAt: string | null }, _module: StudyModule, recent: string[]) {
  return resource.priority + (resource.lastStudiedAt ? 0 : 30) - (recent.includes(resource.id) ? 60 : 0);
}
