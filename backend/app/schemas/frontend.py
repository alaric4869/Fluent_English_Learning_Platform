from datetime import date

from pydantic import BaseModel


class DashboardModuleResponse(BaseModel):
    item_id: int
    skill: str
    code: str
    title: str
    planned_minutes: int
    status: str
    resource_id: int | None
    resource_title: str
    completed: bool


class DashboardStatsResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_study_days: int
    completion_rate: float
    completed_sessions: int
    completed_reviews: int
    tracked_seconds: int
    this_week_completed_planned_minutes: int


class DashboardResponse(BaseModel):
    greeting: str
    display_date: str
    plan_date: date
    plan_status: str
    total_minutes: int
    completed_count: int
    completion_percent: int
    due_review_count: int
    modules: list[DashboardModuleResponse]
    stats: DashboardStatsResponse


class ResourceOptionResponse(BaseModel):
    id: int
    title: str
    difficulty: str | None
    estimated_duration_minutes: int


class ModuleSessionResponse(BaseModel):
    id: int | None
    status: str
    active_duration_seconds: int
    notes: str
    perceived_difficulty: int | None
    confidence: int | None
    completed: bool


class PlanRecommendationResponse(BaseModel):
    id: int
    current_minutes: int
    proposed_minutes: int
    current_resource_title: str
    proposed_resource_title: str
    resource_changed: bool
    minutes_changed: bool
    stale: bool
    reasons: list[str]


class TodayModuleResponse(BaseModel):
    item_id: int
    skill: str
    code: str
    title: str
    instruction: str
    objective: str
    planned_minutes: int
    minimum_minutes: int
    maximum_minutes: int
    status: str
    resource_id: int | None
    resource_title: str
    resource_meta: str
    start_href: str | None
    completed: bool
    reasons: list[str]
    options: list[ResourceOptionResponse]
    session: ModuleSessionResponse
    ai_recommendation: PlanRecommendationResponse | None


class TodayResponse(BaseModel):
    greeting: str
    display_date: str
    plan_id: int
    plan_date: date
    plan_status: str
    total_minutes: int
    explanation: list[str]
    completed_count: int
    completion_percent: int
    due_review_count: int
    agent_available: bool
    agent_unavailable_reason: str
    modules: list[TodayModuleResponse]


class HealthResponse(BaseModel):
    status: str
    api_version: str
