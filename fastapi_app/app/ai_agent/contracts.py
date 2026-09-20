from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import CompletionFilter, ResourceSort
from app.domain.weakness_detection.entities import SkillClassification


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AgentPermission(StrEnum):
    READ_LEARNING_DATA = "read_learning_data"
    CHANGE_STUDY_PLAN = "change_study_plan"
    SAVE_AI_RECOMMENDATION = "save_ai_recommendation"


class AgentToolName(StrEnum):
    GET_TODAY_PLAN = "get_today_plan"
    GET_RECENT_STUDY_HISTORY = "get_recent_study_history"
    GET_SKILL_PROFILE = "get_skill_profile"
    GET_DUE_REVIEWS = "get_due_reviews"
    GET_WEAK_SKILLS = "get_weak_skills"
    SEARCH_LEARNING_RESOURCES = "search_learning_resources"
    GET_RESOURCE = "get_resource"
    RECOMMEND_RESOURCES = "recommend_resources"
    GENERATE_WEEKLY_REPORT = "generate_weekly_report"


class AgentPrincipal(StrictContract):
    user_key: str = Field(min_length=1, max_length=200)
    permissions: frozenset[AgentPermission] = Field(
        default_factory=lambda: frozenset({AgentPermission.READ_LEARNING_DATA})
    )
    allowed_tools: frozenset[AgentToolName] | None = None


class AgentToolDefinition(StrictContract):
    name: AgentToolName
    description: str
    input_schema: dict[str, object]
    required_permission: AgentPermission


class EmptyToolArguments(StrictContract):
    pass


class DatedToolArguments(StrictContract):
    on_date: date | None = None


class RecentHistoryArguments(StrictContract):
    days: int = Field(default=14, ge=1, le=90)
    through_date: date | None = None


class DueReviewsArguments(StrictContract):
    due_on: date | None = None
    limit: int = Field(default=30, ge=1, le=200)


class ResourceSearchArguments(StrictContract):
    search: str = Field(default="", max_length=200)
    skill: Skill | None = None
    resource_type: str = Field(default="", max_length=100)
    topic: str = Field(default="", max_length=150)
    difficulty: str = Field(default="", max_length=100)
    completion: CompletionFilter = CompletionFilter.ALL
    favorite_only: bool = False
    saved_for_later_only: bool = False
    sort: ResourceSort = ResourceSort.RECENTLY_ADDED
    limit: int = Field(default=20, ge=1, le=100)


class ResourceArguments(StrictContract):
    resource_id: int = Field(gt=0)


class ResourceRecommendationArguments(StrictContract):
    skill: Skill
    difficulty: str | None = Field(default=None, max_length=100)
    count: int = Field(default=3, ge=1, le=10)
    target_date: date | None = None


class StudyPlanItemContract(StrictContract):
    item_id: int
    skill: Skill
    position: int
    planned_minutes: int
    resource_id: int | None
    resource_title: str | None
    status: str
    reasons: tuple[str, ...]
    manual_override: bool


class StudyPlanContract(StrictContract):
    found: bool
    plan_id: int | None = None
    plan_date: date
    status: str | None = None
    total_minutes: int = 0
    explanation: tuple[str, ...] = ()
    items: tuple[StudyPlanItemContract, ...] = ()


class SkillProfileContract(StrictContract):
    skill: Skill
    score: float | None
    evidence_status: str
    sample_count: int
    average_accuracy: float | None
    average_confidence: float | None
    average_difficulty: float | None
    hard_item_rate: float | None
    accuracy_trend: float | None
    explanation: str


class LearnerProfileContract(StrictContract):
    found: bool
    snapshot_id: int | None = None
    calculated_at: datetime | None = None
    algorithm_version: str | None = None
    skills: tuple[SkillProfileContract, ...] = ()


class WeakSkillContract(StrictContract):
    skill: Skill
    classification: SkillClassification
    smoothed_score: float | None
    latest_score: float | None
    snapshot_count: int
    reasons: tuple[str, ...]


class WeaknessProfileContract(StrictContract):
    found: bool
    assessment_id: int | None = None
    assessed_at: datetime | None = None
    detector_version: str | None = None
    skills: tuple[WeakSkillContract, ...] = ()


class ReviewItemContract(StrictContract):
    review_item_id: int
    target_type: str
    target_id: int
    review_step: int
    next_review_date: date
    review_count: int
    mastery_status: str


class DueReviewsContract(StrictContract):
    due_on: date
    total_returned: int
    items: tuple[ReviewItemContract, ...]


class ResourceSummaryContract(StrictContract):
    resource_id: int
    title: str
    resource_type: str
    skill: Skill
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    tags: tuple[str, ...]
    favorite: bool = False
    saved_for_later: bool = False
    completed_session_count: int = 0


class ResourceSearchContract(StrictContract):
    total_count: int
    items: tuple[ResourceSummaryContract, ...]


class ResourceDetailContract(ResourceSummaryContract):
    found: Literal[True] = True
    source_url: str | None
    description: str
    content_text: str
    transcript: str
    notes: str


class MissingResourceContract(StrictContract):
    found: Literal[False] = False
    resource_id: int


class ResourceRecommendationContract(StrictContract):
    resource_id: int
    title: str
    skill: Skill
    difficulty: str | None
    score: float
    reasons: tuple[str, ...]


class ResourceRecommendationsContract(StrictContract):
    target_date: date
    skill: Skill
    classification: SkillClassification
    items: tuple[ResourceRecommendationContract, ...]


class HistoricalSessionContract(StrictContract):
    session_id: int
    resource_id: int
    resource_title: str
    skill: Skill
    completed_at: datetime
    actual_duration_seconds: int | None
    accuracy: float | None
    attempt_count: int
    incorrect_item_count: int
    notes: str


class HistoryDayContract(StrictContract):
    study_date: date
    assigned_modules: int
    completed_modules: int
    sessions: tuple[HistoricalSessionContract, ...]


class StudyHistoryContract(StrictContract):
    through_date: date
    days: int
    items: tuple[HistoryDayContract, ...]


class WeeklySkillContract(StrictContract):
    skill: Skill
    completed_modules: int
    completed_sessions: int
    average_accuracy: float | None
    incorrect_item_count: int
    tracked_seconds: int


class WeeklyRecommendationContract(StrictContract):
    title: str
    reason: str
    href: str


class WeeklyReportContract(StrictContract):
    week_start: date
    week_end: date
    study_days: int
    assigned_modules: int
    completed_modules: int
    completion_rate: float
    completed_planned_minutes: int
    completed_sessions: int
    tracked_seconds: int
    vocabulary_learned: int
    difficult_sentences_collected: int
    review_attempt_count: int
    review_retention_rate: float | None
    next_week_review_count: int
    strongest_skill: Skill | None
    weakest_skill: Skill | None
    skill_summaries: tuple[WeeklySkillContract, ...]
    recommendations: tuple[WeeklyRecommendationContract, ...]


class ProviderToolCall(StrictContract):
    call_id: str = Field(min_length=1, max_length=200)
    name: AgentToolName
    arguments: dict[str, object] = Field(default_factory=dict)


class AgentToolResult(StrictContract):
    call_id: str
    name: AgentToolName
    output: dict[str, object]


class AIProviderRequest(StrictContract):
    system_prompt: str
    user_prompt: str
    tools: tuple[AgentToolDefinition, ...]
    previous_response_id: str | None = None
    tool_results: tuple[AgentToolResult, ...] = ()


class AIProviderResponse(StrictContract):
    response_id: str
    output_text: str | None = None
    tool_calls: tuple[ProviderToolCall, ...] = ()

    @model_validator(mode="after")
    def require_output(self) -> "AIProviderResponse":
        if not self.output_text and not self.tool_calls:
            raise ValueError("provider response must contain text or tool calls")
        return self


class AgentRunResult(StrictContract):
    provider_name: str
    response_id: str
    output_text: str
    tools_used: tuple[AgentToolName, ...]
