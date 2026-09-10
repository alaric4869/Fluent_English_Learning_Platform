import { getD1 } from "./index";
import { SEED_RESOURCES } from "./seed";

const SCHEMA_VERSION = "1";
let bootstrapPromise: Promise<void> | null = null;

const schemaStatements = [
  `CREATE TABLE IF NOT EXISTS app_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS learning_resources (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT,
    type TEXT NOT NULL,
    module TEXT NOT NULL,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    priority INTEGER NOT NULL DEFAULT 50,
    tags_json TEXT NOT NULL DEFAULT '[]',
    content_json TEXT NOT NULL DEFAULT '{}',
    is_favorite INTEGER NOT NULL DEFAULT 0,
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_studied_at TEXT
  )`,
  `CREATE INDEX IF NOT EXISTS idx_resources_module_archived ON learning_resources(module, is_archived)`,
  `CREATE INDEX IF NOT EXISTS idx_resources_topic ON learning_resources(topic)`,
  `CREATE TABLE IF NOT EXISTS resource_user_states (
    user_id TEXT NOT NULL,
    resource_id TEXT NOT NULL REFERENCES learning_resources(id),
    is_favorite INTEGER NOT NULL DEFAULT 0,
    saved_for_later INTEGER NOT NULL DEFAULT 0
  )`,
  `CREATE UNIQUE INDEX IF NOT EXISTS idx_resource_states_user_resource ON resource_user_states(user_id, resource_id)`,
  `CREATE TABLE IF NOT EXISTS study_days (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    study_date TEXT NOT NULL,
    theme TEXT NOT NULL,
    target_minutes INTEGER NOT NULL,
    adaptation_reasons_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE UNIQUE INDEX IF NOT EXISTS idx_study_days_user_date ON study_days(user_id, study_date)`,
  `CREATE TABLE IF NOT EXISTS study_plan_items (
    id TEXT PRIMARY KEY,
    study_day_id TEXT NOT NULL REFERENCES study_days(id),
    resource_id TEXT NOT NULL REFERENCES learning_resources(id),
    module TEXT NOT NULL,
    position INTEGER NOT NULL,
    target_minutes INTEGER NOT NULL,
    instructions_json TEXT NOT NULL DEFAULT '[]',
    objectives_json TEXT NOT NULL DEFAULT '[]',
    resource_snapshot_json TEXT NOT NULL,
    assignment_source TEXT NOT NULL DEFAULT 'rule_based',
    status TEXT NOT NULL DEFAULT 'not_started',
    notes TEXT NOT NULL DEFAULT '',
    difficulty_rating INTEGER,
    confidence_rating INTEGER,
    completed_at TEXT
  )`,
  `CREATE INDEX IF NOT EXISTS idx_plan_items_study_day ON study_plan_items(study_day_id)`,
  `CREATE TABLE IF NOT EXISTS study_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_item_id TEXT NOT NULL REFERENCES study_plan_items(id),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    active_seconds INTEGER NOT NULL DEFAULT 0
  )`,
  `CREATE INDEX IF NOT EXISTS idx_sessions_user_started ON study_sessions(user_id, started_at)`,
  `CREATE TABLE IF NOT EXISTS vocabulary_items (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    phrase TEXT NOT NULL,
    meaning TEXT NOT NULL,
    example TEXT NOT NULL,
    source_resource_id TEXT REFERENCES learning_resources(id),
    date_learned TEXT NOT NULL,
    personal_note TEXT NOT NULL DEFAULT '',
    difficulty TEXT NOT NULL DEFAULT 'medium',
    mastery TEXT NOT NULL DEFAULT 'new',
    is_favorite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE INDEX IF NOT EXISTS idx_vocabulary_user_date ON vocabulary_items(user_id, date_learned)`,
  `CREATE TABLE IF NOT EXISTS saved_sentences (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    resource_id TEXT NOT NULL REFERENCES learning_resources(id),
    sentence_index INTEGER NOT NULL,
    sentence TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE INDEX IF NOT EXISTS idx_saved_sentences_user ON saved_sentences(user_id)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_sentences_user_resource_index ON saved_sentences(user_id, resource_id, sentence_index)`,
  `CREATE TABLE IF NOT EXISTS review_items (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    answer TEXT NOT NULL,
    stage INTEGER NOT NULL DEFAULT 0,
    due_date TEXT NOT NULL,
    mastery TEXT NOT NULL DEFAULT 'new',
    lapse_count INTEGER NOT NULL DEFAULT 0,
    scheduler_version TEXT NOT NULL DEFAULT 'fixed-v1',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE INDEX IF NOT EXISTS idx_review_items_user_due ON review_items(user_id, due_date)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS idx_review_items_user_target ON review_items(user_id, target_type, target_id)`,
  `CREATE TABLE IF NOT EXISTS review_attempts (
    id TEXT PRIMARY KEY,
    review_item_id TEXT NOT NULL REFERENCES review_items(id),
    user_id TEXT NOT NULL,
    rating TEXT NOT NULL,
    previous_due_date TEXT NOT NULL,
    next_due_date TEXT NOT NULL,
    attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE INDEX IF NOT EXISTS idx_review_attempts_user_date ON review_attempts(user_id, attempted_at)`,
  `CREATE TABLE IF NOT EXISTS notebook_entries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_resource_id TEXT REFERENCES learning_resources(id),
    is_favorite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE INDEX IF NOT EXISTS idx_notebook_user_created ON notebook_entries(user_id, created_at)`,
  `CREATE TABLE IF NOT EXISTS performance_signals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    module TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    numeric_value INTEGER NOT NULL,
    plan_item_id TEXT REFERENCES study_plan_items(id),
    observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE INDEX IF NOT EXISTS idx_performance_user_module ON performance_signals(user_id, module)`,
];

export async function ensureDatabase(): Promise<void> {
  if (!bootstrapPromise) bootstrapPromise = bootstrap();
  return bootstrapPromise;
}

async function bootstrap(): Promise<void> {
  const d1 = getD1();
  await d1.batch(schemaStatements.map((statement) => d1.prepare(statement)));

  const current = await d1.prepare("SELECT value FROM app_meta WHERE key = ?").bind("schema_version").first<{ value: string }>();
  if (current?.value === SCHEMA_VERSION) return;

  const seedStatements = SEED_RESOURCES.map((resource) =>
    d1
      .prepare(`INSERT OR IGNORE INTO learning_resources (
        id, owner_user_id, type, module, title, source, url, topic, difficulty,
        duration_minutes, priority, tags_json, content_json, is_favorite, is_archived
      ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)`)
      .bind(
        resource.id,
        resource.type,
        resource.module,
        resource.title,
        resource.source,
        resource.url,
        resource.topic,
        resource.difficulty,
        resource.durationMinutes,
        resource.priority,
        JSON.stringify(resource.tags),
        JSON.stringify(resource.content),
      ),
  );

  await d1.batch(seedStatements);
  await d1
    .prepare("INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)")
    .bind("schema_version", SCHEMA_VERSION)
    .run();
  await d1.prepare("PRAGMA optimize").run();
}

export async function ensureUserSeed(userId: string, today: string): Promise<void> {
  await ensureDatabase();
  const d1 = getD1();
  const existing = await d1
    .prepare("SELECT COUNT(*) AS count FROM vocabulary_items WHERE user_id = ?")
    .bind(userId)
    .first<{ count: number }>();
  if ((existing?.count ?? 0) > 0) return;

  const learnedDate = shiftDate(today, -7);
  const starterVocabulary = [
    ["vocab-seed-1", "make an appointment", "预约", "I'd like to make an appointment for Friday.", "listen-clinic-call", "learning"],
    ["vocab-seed-2", "That works for me", "那个时间适合我", "Ten past three? That works for me.", "listen-clinic-call", "familiar"],
    ["vocab-seed-3", "for here or takeaway", "堂食还是外带", "Is that for here or takeaway?", "listen-coffee-order", "learning"],
  ] as const;

  const statements = starterVocabulary.flatMap(([id, phrase, meaning, example, resourceId, mastery], index) => {
    const reviewId = `review-seed-${index + 1}-${userId}`;
    return [
      d1.prepare(`INSERT OR IGNORE INTO vocabulary_items (
        id, user_id, phrase, meaning, example, source_resource_id, date_learned, mastery
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
        .bind(`${id}-${userId}`, userId, phrase, meaning, example, resourceId, learnedDate, mastery),
      d1.prepare(`INSERT OR IGNORE INTO review_items (
        id, user_id, target_type, target_id, prompt, answer, stage, due_date, mastery
      ) VALUES (?, ?, 'vocabulary', ?, ?, ?, ?, ?, ?)`)
        .bind(reviewId, userId, `${id}-${userId}`, phrase, `${meaning} — ${example}`, index + 1, today, mastery),
    ];
  });

  statements.push(
    d1.prepare(`INSERT OR IGNORE INTO notebook_entries (
      id, user_id, type, title, content, source_resource_id, is_favorite
    ) VALUES (?, ?, 'pronunciation', ?, ?, ?, 1)`)
      .bind(
        `note-seed-${userId}`,
        userId,
        "Could I — keep it connected",
        "不要逐词重读。把 could I 连起来，再把重音放在想要的物品上。",
        "listen-coffee-order",
      ),
  );

  await d1.batch(statements);
}

export function shiftDate(date: string, days: number): string {
  const [year, month, day] = date.split("-").map(Number);
  const value = new Date(Date.UTC(year, month - 1, day + days));
  return value.toISOString().slice(0, 10);
}
