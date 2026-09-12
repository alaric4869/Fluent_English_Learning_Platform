import { sql } from "drizzle-orm";
import { index, integer, real, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

export const appMeta = sqliteTable("app_meta", {
  key: text("key").primaryKey(),
  value: text("value").notNull(),
});

export const resources = sqliteTable(
  "learning_resources",
  {
    id: text("id").primaryKey(),
    ownerUserId: text("owner_user_id"),
    type: text("type").notNull(),
    module: text("module").notNull(),
    title: text("title").notNull(),
    source: text("source").notNull(),
    url: text("url"),
    topic: text("topic").notNull(),
    difficulty: text("difficulty").notNull(),
    durationMinutes: integer("duration_minutes").notNull(),
    priority: integer("priority").notNull().default(50),
    tagsJson: text("tags_json").notNull().default("[]"),
    contentJson: text("content_json").notNull().default("{}"),
    isFavorite: integer("is_favorite", { mode: "boolean" }).notNull().default(false),
    isArchived: integer("is_archived", { mode: "boolean" }).notNull().default(false),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    lastStudiedAt: text("last_studied_at"),
  },
  (table) => [
    index("idx_resources_module_archived").on(table.module, table.isArchived),
    index("idx_resources_topic").on(table.topic),
  ],
);

export const resourceUserStates = sqliteTable(
  "resource_user_states",
  {
    userId: text("user_id").notNull(),
    resourceId: text("resource_id").notNull().references(() => resources.id),
    isFavorite: integer("is_favorite", { mode: "boolean" }).notNull().default(false),
    savedForLater: integer("saved_for_later", { mode: "boolean" }).notNull().default(false),
  },
  (table) => [uniqueIndex("idx_resource_states_user_resource").on(table.userId, table.resourceId)],
);

export const studyDays = sqliteTable(
  "study_days",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    studyDate: text("study_date").notNull(),
    theme: text("theme").notNull(),
    targetMinutes: integer("target_minutes").notNull(),
    adaptationReasonsJson: text("adaptation_reasons_json").notNull().default("[]"),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    uniqueIndex("idx_study_days_user_date").on(table.userId, table.studyDate),
  ],
);

export const studyPlanItems = sqliteTable(
  "study_plan_items",
  {
    id: text("id").primaryKey(),
    studyDayId: text("study_day_id").notNull().references(() => studyDays.id),
    resourceId: text("resource_id").notNull().references(() => resources.id),
    module: text("module").notNull(),
    position: integer("position").notNull(),
    targetMinutes: integer("target_minutes").notNull(),
    instructionsJson: text("instructions_json").notNull().default("[]"),
    objectivesJson: text("objectives_json").notNull().default("[]"),
    resourceSnapshotJson: text("resource_snapshot_json").notNull(),
    assignmentSource: text("assignment_source").notNull().default("rule_based"),
    status: text("status").notNull().default("not_started"),
    notes: text("notes").notNull().default(""),
    difficultyRating: integer("difficulty_rating"),
    confidenceRating: integer("confidence_rating"),
    completedAt: text("completed_at"),
  },
  (table) => [index("idx_plan_items_study_day").on(table.studyDayId)],
);

export const studySessions = sqliteTable(
  "study_sessions",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    planItemId: text("plan_item_id").notNull().references(() => studyPlanItems.id),
    startedAt: text("started_at").notNull(),
    completedAt: text("completed_at"),
    activeSeconds: integer("active_seconds").notNull().default(0),
  },
  (table) => [index("idx_sessions_user_started").on(table.userId, table.startedAt)],
);

export const vocabularyItems = sqliteTable(
  "vocabulary_items",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    phrase: text("phrase").notNull(),
    meaning: text("meaning").notNull(),
    example: text("example").notNull(),
    sourceResourceId: text("source_resource_id").references(() => resources.id),
    dateLearned: text("date_learned").notNull(),
    personalNote: text("personal_note").notNull().default(""),
    difficulty: text("difficulty").notNull().default("medium"),
    mastery: text("mastery").notNull().default("new"),
    isFavorite: integer("is_favorite", { mode: "boolean" }).notNull().default(false),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [index("idx_vocabulary_user_date").on(table.userId, table.dateLearned)],
);

export const savedSentences = sqliteTable(
  "saved_sentences",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    resourceId: text("resource_id").notNull().references(() => resources.id),
    sentenceIndex: integer("sentence_index").notNull(),
    sentence: text("sentence").notNull(),
    status: text("status").notNull(),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index("idx_saved_sentences_user").on(table.userId),
    uniqueIndex("idx_saved_sentences_user_resource_index").on(table.userId, table.resourceId, table.sentenceIndex),
  ],
);

export const reviewItems = sqliteTable(
  "review_items",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    targetType: text("target_type").notNull(),
    targetId: text("target_id").notNull(),
    prompt: text("prompt").notNull(),
    answer: text("answer").notNull(),
    stage: integer("stage").notNull().default(0),
    dueDate: text("due_date").notNull(),
    mastery: text("mastery").notNull().default("new"),
    lapseCount: integer("lapse_count").notNull().default(0),
    schedulerVersion: text("scheduler_version").notNull().default("fixed-v1"),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index("idx_review_items_user_due").on(table.userId, table.dueDate),
    uniqueIndex("idx_review_items_user_target").on(table.userId, table.targetType, table.targetId),
  ],
);

export const reviewAttempts = sqliteTable(
  "review_attempts",
  {
    id: text("id").primaryKey(),
    reviewItemId: text("review_item_id").notNull().references(() => reviewItems.id),
    userId: text("user_id").notNull(),
    rating: text("rating").notNull(),
    previousDueDate: text("previous_due_date").notNull(),
    nextDueDate: text("next_due_date").notNull(),
    attemptedAt: text("attempted_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [index("idx_review_attempts_user_date").on(table.userId, table.attemptedAt)],
);

export const notebookEntries = sqliteTable(
  "notebook_entries",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    type: text("type").notNull(),
    title: text("title").notNull(),
    content: text("content").notNull(),
    sourceResourceId: text("source_resource_id").references(() => resources.id),
    isFavorite: integer("is_favorite", { mode: "boolean" }).notNull().default(false),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [index("idx_notebook_user_created").on(table.userId, table.createdAt)],
);

export const performanceSignals = sqliteTable(
  "performance_signals",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    module: text("module").notNull(),
    signalType: text("signal_type").notNull(),
    numericValue: integer("numeric_value").notNull(),
    planItemId: text("plan_item_id").references(() => studyPlanItems.id),
    observedAt: text("observed_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [index("idx_performance_user_module").on(table.userId, table.module)],
);

export const ieltsGoals = sqliteTable("ielts_goals", {
  userId: text("user_id").primaryKey(),
  testType: text("test_type").notNull().default("general"),
  targetBand: real("target_band").notNull().default(6.5),
  examDate: text("exam_date").notNull(),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

export const ieltsAttempts = sqliteTable(
  "ielts_attempts",
  {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull(),
    bookNumber: integer("book_number").notNull(),
    testNumber: integer("test_number").notNull(),
    skill: text("skill").notNull(),
    status: text("status").notNull().default("in_progress"),
    rawScore: integer("raw_score"),
    estimatedBand: real("estimated_band"),
    notes: text("notes").notNull().default(""),
    startedAt: text("started_at").notNull(),
    completedAt: text("completed_at"),
    updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index("idx_ielts_attempts_user_started").on(table.userId, table.startedAt),
    index("idx_ielts_attempts_material").on(table.userId, table.bookNumber, table.testNumber, table.skill),
  ],
);

export const ieltsQuestionResponses = sqliteTable(
  "ielts_question_responses",
  {
    id: text("id").primaryKey(),
    attemptId: text("attempt_id").notNull().references(() => ieltsAttempts.id),
    userId: text("user_id").notNull(),
    sectionNumber: integer("section_number").notNull(),
    questionNumber: integer("question_number").notNull(),
    answer: text("answer").notNull().default(""),
    isCorrect: integer("is_correct", { mode: "boolean" }),
    correctAnswer: text("correct_answer"),
    explanationPage: integer("explanation_page"),
    savedAt: text("saved_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    gradedAt: text("graded_at"),
  },
  (table) => [
    uniqueIndex("idx_ielts_responses_attempt_question").on(table.attemptId, table.questionNumber),
    index("idx_ielts_responses_user_saved").on(table.userId, table.savedAt),
  ],
);
