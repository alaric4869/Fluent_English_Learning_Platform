from datetime import date, datetime

from pydantic import BaseModel


class HistoryModuleResponse(BaseModel):
    item_id: int
    skill: str
    code: str
    title: str
    resource_id: int | None
    resource_title: str
    planned_minutes: int
    status: str
    completed: bool
    started_at: datetime | None
    completed_at: datetime | None


class HistorySessionResponse(BaseModel):
    id: int
    resource_id: int
    resource_title: str
    skill: str
    skill_label: str
    status: str
    completed_at: datetime
    actual_duration_seconds: int | None
    accuracy_percent: int | None
    attempt_count: int
    incorrect_item_count: int
    notes: str


class HistoryDayResponse(BaseModel):
    study_date: date
    display_date: str
    completed_module_count: int
    assigned_module_count: int
    modules: list[HistoryModuleResponse]
    sessions: list[HistorySessionResponse]


class HistoryResponse(BaseModel):
    today: date
    selected_month: date
    month_label: str
    previous_month: str
    next_month: str
    saved_day_count: int
    completed_module_count: int
    session_count: int
    days: list[HistoryDayResponse]


class SkillProgressResponse(BaseModel):
    skill: str
    code: str
    label: str
    completed_modules: int
    completed_sessions: int
    score: int | None
    evidence_status: str
    evidence_label: str
    classification: str
    classification_label: str


class DailyActivityResponse(BaseModel):
    activity_date: date
    assigned_modules: int
    completed_modules: int
    completed_planned_minutes: int
    completed_sessions: int
    tracked_seconds: int
    activity_score: int


class ProgressResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_study_days: int
    assigned_modules: int
    completed_modules: int
    completion_rate: float
    completed_planned_minutes: int
    tracked_seconds: int
    this_week_completed_planned_minutes: int
    completed_sessions: int
    completed_reviews: int
    skills: list[SkillProgressResponse]
    recent_activity: list[DailyActivityResponse]


class WeeklyAttemptSummaryResponse(BaseModel):
    again_count: int
    hard_count: int
    good_count: int
    easy_count: int
    total_count: int
    retention_rate: float | None


class WeeklySkillResponse(BaseModel):
    skill: str
    code: str
    label: str
    completed_modules: int
    completed_sessions: int
    average_accuracy_percent: int | None
    incorrect_item_count: int
    tracked_seconds: int


class WeeklyRecommendationResponse(BaseModel):
    title: str
    reason: str
    href: str


class WeeklyReviewResponse(BaseModel):
    week_start: date
    week_end: date
    date_range: str
    study_days: int
    assigned_modules: int
    completed_modules: int
    completion_rate: float
    completed_planned_minutes: int
    completed_sessions: int
    tracked_seconds: int
    vocabulary_learned: int
    difficult_sentences_collected: int
    next_week_review_count: int
    strongest_skill: str | None
    strongest_label: str
    weakest_skill: str | None
    weakest_label: str
    review_attempts: WeeklyAttemptSummaryResponse
    skills: list[WeeklySkillResponse]
    recommendations: list[WeeklyRecommendationResponse]
