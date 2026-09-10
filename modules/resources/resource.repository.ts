import type { LearningResourceDto } from "../shared/contracts";

export interface NewResourceInput extends Omit<LearningResourceDto, "id" | "createdAt" | "lastStudiedAt" | "isArchived" | "priority"> {}

export interface ResourceRepository {
  list(userId: string, includeArchived?: boolean): Promise<LearningResourceDto[]>;
  get(userId: string, resourceId: string): Promise<LearningResourceDto | null>;
  create(userId: string, input: NewResourceInput): Promise<string>;
  update(userId: string, resourceId: string, changes: Pick<LearningResourceDto, "title" | "source" | "url" | "topic" | "difficulty" | "durationMinutes" | "tags" | "content">): Promise<void>;
  toggleFavorite(userId: string, resourceId: string): Promise<void>;
  archive(userId: string, resourceId: string): Promise<void>;
  markStudied(resourceId: string, studiedAt: string): Promise<void>;
}
