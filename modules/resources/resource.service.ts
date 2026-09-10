import type { LearningResourceDto } from "../shared/contracts";
import type { NewResourceInput, ResourceRepository } from "./resource.repository";

export class ResourceService {
  constructor(private readonly resources: ResourceRepository) {}

  list(userId: string) {
    return this.resources.list(userId);
  }

  create(userId: string, input: NewResourceInput) {
    if (!input.title.trim()) throw new Error("Resource title is required.");
    if (!input.topic.trim()) throw new Error("Resource topic is required.");
    if (input.durationMinutes < 5 || input.durationMinutes > 180) {
      throw new Error("Duration must be between 5 and 180 minutes.");
    }
    return this.resources.create(userId, input);
  }

  toggleFavorite(userId: string, resourceId: string) {
    return this.resources.toggleFavorite(userId, resourceId);
  }

  update(userId: string, resourceId: string, changes: Pick<LearningResourceDto, "title" | "source" | "url" | "topic" | "difficulty" | "durationMinutes" | "tags" | "content">) {
    if (!changes.title.trim() || !changes.topic.trim()) throw new Error("Title and topic are required.");
    if (changes.durationMinutes < 5 || changes.durationMinutes > 180) throw new Error("Duration must be between 5 and 180 minutes.");
    return this.resources.update(userId, resourceId, changes);
  }

  archive(userId: string, resourceId: string) {
    return this.resources.archive(userId, resourceId);
  }
}
