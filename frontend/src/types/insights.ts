export interface HistoryModule {
  item_id: number;
  skill: string;
  code: string;
  title: string;
  resource_id: number | null;
  resource_title: string;
  planned_minutes: number;
  status: string;
  completed: boolean;
  started_at: string | null;
  completed_at: string | null;
}

export interface HistorySession {
  id: number;
  resource_id: number;
  resource_title: string;
  skill: string;
  skill_label: string;
  status: string;
  completed_at: string;
  actual_duration_seconds: number | null;
  accuracy_percent: number | null;
  attempt_count: number;
  incorrect_item_count: number;
  notes: string;
}

export interface HistoryDay {
  study_date: string;
  display_date: string;
  completed_module_count: number;
  assigned_module_count: number;
  modules: HistoryModule[];
  sessions: HistorySession[];
}

export interface HistoryResponse {
  today: string;
  selected_month: string;
  month_label: string;
  previous_month: string;
  next_month: string;
  saved_day_count: number;
  completed_module_count: number;
  session_count: number;
  days: HistoryDay[];
}

export interface ProgressResponse {
  current_streak: number;
  longest_streak: number;
  total_study_days: number;
  assigned_modules: number;
  completed_modules: number;
  completion_rate: number;
  completed_planned_minutes: number;
  tracked_seconds: number;
  this_week_completed_planned_minutes: number;
  completed_sessions: number;
  completed_reviews: number;
  skills: Array<{
    skill: string;
    code: string;
    label: string;
    completed_modules: number;
    completed_sessions: number;
    score: number | null;
    evidence_status: string;
    evidence_label: string;
    classification: string;
    classification_label: string;
  }>;
  recent_activity: Array<{
    activity_date: string;
    assigned_modules: number;
    completed_modules: number;
    completed_planned_minutes: number;
    completed_sessions: number;
    tracked_seconds: number;
    activity_score: number;
  }>;
}

export interface WeeklyReviewResponse {
  week_start: string;
  week_end: string;
  date_range: string;
  study_days: number;
  assigned_modules: number;
  completed_modules: number;
  completion_rate: number;
  completed_planned_minutes: number;
  completed_sessions: number;
  tracked_seconds: number;
  vocabulary_learned: number;
  difficult_sentences_collected: number;
  next_week_review_count: number;
  strongest_skill: string | null;
  strongest_label: string;
  weakest_skill: string | null;
  weakest_label: string;
  review_attempts: {
    again_count: number;
    hard_count: number;
    good_count: number;
    easy_count: number;
    total_count: number;
    retention_rate: number | null;
  };
  skills: Array<{
    skill: string;
    code: string;
    label: string;
    completed_modules: number;
    completed_sessions: number;
    average_accuracy_percent: number | null;
    incorrect_item_count: number;
    tracked_seconds: number;
  }>;
  recommendations: Array<{ title: string; reason: string; href: string }>;
}
