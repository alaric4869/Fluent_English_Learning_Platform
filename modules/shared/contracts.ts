export type StudyModule = "listening" | "speaking" | "reading" | "vocabulary";
export type ResourceType =
  | StudyModule
  | "pronunciation"
  | "grammar"
  | "ielts_pte"
  | "australian_english";
export type Difficulty = "foundation" | "comfortable" | "stretch";
export type PlanItemStatus = "not_started" | "in_progress" | "completed";
export type ReviewRating = "again" | "hard" | "good" | "easy";
export type MasteryStatus = "new" | "learning" | "familiar" | "mastered";
export type SentenceStatus = "couldnt_hear" | "difficult" | "understood" | "mastered" | "need_practice" | "good";
export type IeltsSkill = "listening" | "reading" | "writing" | "speaking";
export type IeltsAttemptStatus = "in_progress" | "completed" | "cancelled";

export interface ResourceContent {
  summary: string;
  transcript?: string;
  transcriptMode?: "provided" | "source_captions";
  sentences?: string[];
  article?: string;
  chunks?: Array<{ phrase: string; meaning: string; example: string }>;
  questions?: string[];
  prompts?: string[];
  pronunciationNotes?: string[];
  connectedSpeechNotes?: string[];
}

export interface LearningResourceDto {
  id: string;
  type: ResourceType;
  module: StudyModule;
  title: string;
  source: string;
  url: string | null;
  topic: string;
  difficulty: Difficulty;
  durationMinutes: number;
  priority: number;
  tags: string[];
  content: ResourceContent;
  isFavorite: boolean;
  isArchived: boolean;
  createdAt: string;
  lastStudiedAt: string | null;
}

export interface StudyPlanItemDto {
  id: string;
  module: StudyModule;
  targetMinutes: number;
  status: PlanItemStatus;
  notes: string;
  difficultyRating: number | null;
  confidenceRating: number | null;
  instructions: string[];
  objectives: string[];
  assignmentSource: string;
  resource: LearningResourceDto;
}

export interface ReviewItemDto {
  id: string;
  targetType: "vocabulary" | "sentence" | "expression" | "lesson";
  targetId: string;
  prompt: string;
  answer: string;
  stage: number;
  dueDate: string;
  mastery: MasteryStatus;
}

export interface VocabularyItemDto {
  id: string;
  phrase: string;
  meaning: string;
  example: string;
  sourceResourceId: string | null;
  dateLearned: string;
  personalNote: string;
  difficulty: string;
  mastery: MasteryStatus;
  isFavorite: boolean;
}

export interface SavedSentenceDto {
  id: string;
  resourceId: string;
  sentenceIndex: number;
  sentence: string;
  status: SentenceStatus;
}

export interface NotebookEntryDto {
  id: string;
  type: "vocabulary" | "expression" | "listening" | "pronunciation" | "grammar" | "speaking" | "sentence";
  title: string;
  content: string;
  sourceResourceId: string | null;
  sourceTitle: string | null;
  isFavorite: boolean;
  createdAt: string;
}

export interface HistoryDayDto {
  date: string;
  theme: string;
  completedModules: StudyModule[];
  totalModules: number;
  studyMinutes: number;
  planItems: Array<Pick<StudyPlanItemDto, "id" | "module" | "status" | "targetMinutes"> & { title: string }>;
}

export interface ProgressDto {
  currentStreak: number;
  longestStreak: number;
  totalStudyDays: number;
  totalStudyMinutes: number;
  thisWeekMinutes: number;
  completionRate: number;
  vocabularyLearned: number;
  vocabularyMastered: number;
  reviewsCompleted: number;
  moduleCompletions: Record<StudyModule, number>;
  weeklyActivity: Array<{ date: string; minutes: number }>;
  skillScores: Array<{ module: StudyModule; score: number; label: string; sampleCount: number }>;
}

export interface AppStateDto {
  today: {
    date: string;
    theme: string;
    targetMinutes: number;
    adaptationReasons: string[];
    planItems: StudyPlanItemDto[];
  };
  dueReviews: ReviewItemDto[];
  resources: LearningResourceDto[];
  vocabulary: VocabularyItemDto[];
  savedSentences: SavedSentenceDto[];
  notebook: NotebookEntryDto[];
  history: HistoryDayDto[];
  progress: ProgressDto;
}

export interface IeltsGoalDto {
  testType: "general";
  targetBand: number;
  examDate: string;
  updatedAt: string;
}

export interface IeltsAttemptDto {
  id: string;
  bookNumber: number;
  testNumber: number;
  skill: IeltsSkill;
  status: IeltsAttemptStatus;
  rawScore: number | null;
  estimatedBand: number | null;
  notes: string;
  startedAt: string;
  completedAt: string | null;
}

export interface IeltsDashboardDto {
  goal: IeltsGoalDto;
  attempts: IeltsAttemptDto[];
  summary: {
    completedAttempts: number;
    completedThisWeek: number;
    averageBand: number | null;
    skillAverages: Array<{ skill: IeltsSkill; averageBand: number | null; attempts: number }>;
  };
}

export type IeltsAction =
  | { type: "save_goal"; targetBand: number; examDate: string }
  | { type: "start_attempt"; bookNumber: number; testNumber: number; skill: IeltsSkill }
  | { type: "cancel_attempt"; attemptId: string }
  | {
      type: "complete_attempt";
      attemptId: string;
      rawScore?: number;
      estimatedBand?: number;
      notes: string;
    };

export type AppAction =
  | { type: "start_session"; planItemId: string }
  | { type: "complete_plan_item"; planItemId: string; activeSeconds?: number }
  | { type: "save_plan_notes"; planItemId: string; notes: string }
  | { type: "rate_plan_item"; planItemId: string; difficulty: number; confidence: number }
  | { type: "replace_resource"; planItemId: string }
  | { type: "toggle_resource_favorite"; resourceId: string }
  | { type: "archive_resource"; resourceId: string }
  | {
      type: "add_resource";
      resource: Omit<LearningResourceDto, "id" | "createdAt" | "lastStudiedAt" | "isArchived" | "priority">;
    }
  | {
      type: "update_resource";
      resourceId: string;
      changes: Pick<LearningResourceDto, "title" | "source" | "url" | "topic" | "difficulty" | "durationMinutes" | "tags" | "content">;
    }
  | {
      type: "add_vocabulary";
      phrase: string;
      meaning: string;
      example: string;
      sourceResourceId?: string;
      personalNote?: string;
      date: string;
    }
  | {
      type: "save_sentence";
      resourceId: string;
      sentenceIndex: number;
      sentence: string;
      status: SentenceStatus;
      date: string;
    }
  | { type: "rate_review"; reviewItemId: string; rating: ReviewRating; date: string }
  | {
      type: "add_notebook_entry";
      entryType: NotebookEntryDto["type"];
      title: string;
      content: string;
      sourceResourceId?: string;
    };
