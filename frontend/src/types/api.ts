export interface DashboardModule {
  item_id: number;
  skill: string;
  code: string;
  title: string;
  planned_minutes: number;
  status: string;
  resource_id: number | null;
  resource_title: string;
  completed: boolean;
}

export interface DashboardResponse {
  greeting: string;
  display_date: string;
  plan_date: string;
  plan_status: string;
  total_minutes: number;
  completed_count: number;
  completion_percent: number;
  due_review_count: number;
  modules: DashboardModule[];
  stats: {
    current_streak: number;
    longest_streak: number;
    total_study_days: number;
    completion_rate: number;
    completed_sessions: number;
    completed_reviews: number;
    tracked_seconds: number;
    this_week_completed_planned_minutes: number;
  };
}

export interface ResourceOption {
  id: number;
  title: string;
  difficulty: string | null;
  estimated_duration_minutes: number;
}

export interface TodayModule {
  item_id: number;
  skill: string;
  code: string;
  title: string;
  instruction: string;
  objective: string;
  planned_minutes: number;
  minimum_minutes: number;
  maximum_minutes: number;
  status: string;
  resource_id: number | null;
  resource_title: string;
  resource_meta: string;
  start_href: string | null;
  completed: boolean;
  reasons: string[];
  options: ResourceOption[];
  session: {
    id: number | null;
    status: string;
    active_duration_seconds: number;
    notes: string;
    perceived_difficulty: number | null;
    confidence: number | null;
    completed: boolean;
  };
  ai_recommendation: {
    id: number;
    current_minutes: number;
    proposed_minutes: number;
    current_resource_title: string;
    proposed_resource_title: string;
    resource_changed: boolean;
    minutes_changed: boolean;
    stale: boolean;
    reasons: string[];
  } | null;
}

export interface TodayResponse {
  greeting: string;
  display_date: string;
  plan_id: number;
  plan_date: string;
  plan_status: string;
  total_minutes: number;
  explanation: string[];
  completed_count: number;
  completion_percent: number;
  due_review_count: number;
  agent_available: boolean;
  agent_unavailable_reason: string;
  modules: TodayModule[];
}
