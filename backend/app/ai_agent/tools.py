from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Generic, TypeVar, cast

from pydantic import BaseModel, ValidationError

from app.ai_agent.authorization import (
    AgentToolAuthorizationPolicy,
    UnknownAgentToolError,
)
from app.ai_agent.contracts import (
    AgentPermission,
    AgentPrincipal,
    AgentToolDefinition,
    AgentToolName,
    AgentToolResult,
    DatedToolArguments,
    DueReviewsArguments,
    DueReviewsContract,
    EmptyToolArguments,
    HistoricalSessionContract,
    HistoryDayContract,
    LearnerProfileContract,
    MissingResourceContract,
    RecentHistoryArguments,
    ResourceArguments,
    ResourceDetailContract,
    ResourceRecommendationArguments,
    ResourceRecommendationContract,
    ResourceRecommendationsContract,
    ResourceSearchArguments,
    ResourceSearchContract,
    ResourceSummaryContract,
    ReviewItemContract,
    SaveAIRecommendationArguments,
    SavedAIRecommendationContract,
    SkillProfileContract,
    StudyHistoryContract,
    StudyPlanContract,
    StudyPlanItemContract,
    WeaknessProfileContract,
    WeakSkillContract,
    WeeklyRecommendationContract,
    WeeklyReportContract,
    WeeklySkillContract,
)
from app.domain.resources.entities import ResourceLibraryFilters
from app.domain.weakness_detection.entities import SkillClassification
from app.services.history import HistoryService
from app.services.adaptive_learning import AdaptationDecisionService
from app.services.learner_profile import LearnerProfileService
from app.services.resources import ResourceService
from app.services.review import ReviewService
from app.services.study_plan import StudyPlanService
from app.services.weakness_detection import WeaknessDetectionService
from app.services.weekly_review import WeeklyReviewService


InputContract = TypeVar("InputContract", bound=BaseModel)
OutputContract = TypeVar("OutputContract", bound=BaseModel)


@dataclass(frozen=True)
class AgentExecutionContext:
    principal: AgentPrincipal
    today: date


@dataclass(frozen=True)
class AgentTool(Generic[InputContract, OutputContract]):
    definition: AgentToolDefinition
    input_contract: type[InputContract]
    handler: Callable[[AgentExecutionContext, InputContract], OutputContract]

    def execute(
        self,
        context: AgentExecutionContext,
        raw_arguments: dict[str, object],
    ) -> dict[str, object]:
        try:
            arguments = self.input_contract.model_validate(raw_arguments)
        except ValidationError as error:
            raise AgentToolInputError(self.definition.name, error) from error
        output = self.handler(context, arguments)
        return cast(dict[str, object], output.model_dump(mode="json"))


class AgentToolRegistry:
    def __init__(
        self,
        tools: tuple[AgentTool[BaseModel, BaseModel], ...],
        authorization_policy: AgentToolAuthorizationPolicy | None = None,
    ) -> None:
        self._tools = {tool.definition.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Agent tool names must be unique")
        self.authorization_policy = (
            authorization_policy or AgentToolAuthorizationPolicy()
        )

    def catalogue(
        self,
        principal: AgentPrincipal,
    ) -> tuple[AgentToolDefinition, ...]:
        return tuple(
            tool.definition
            for tool in self._tools.values()
            if self.authorization_policy.is_authorized(principal, tool.definition)
        )

    def execute(
        self,
        context: AgentExecutionContext,
        call_id: str,
        tool_name: AgentToolName,
        arguments: dict[str, object],
    ) -> AgentToolResult:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise UnknownAgentToolError(tool_name)
        self.authorization_policy.authorize(context.principal, tool.definition)
        return AgentToolResult(
            call_id=call_id,
            name=tool_name,
            output=tool.execute(context, arguments),
        )


class LearningAgentToolHandlers:
    def __init__(
        self,
        *,
        learner_profile: LearnerProfileService,
        weakness_detection: WeaknessDetectionService,
        resources: ResourceService,
        study_plan: StudyPlanService,
        history: HistoryService,
        review: ReviewService,
        weekly_review: WeeklyReviewService,
        adaptation_decisions: AdaptationDecisionService,
    ) -> None:
        self.learner_profile = learner_profile
        self.weakness_detection = weakness_detection
        self.resources = resources
        self.study_plan = study_plan
        self.history = history
        self.review = review
        self.weekly_review = weekly_review
        self.adaptation_decisions = adaptation_decisions

    def get_today_plan(
        self,
        context: AgentExecutionContext,
        arguments: DatedToolArguments,
    ) -> StudyPlanContract:
        plan_date = arguments.on_date or context.today
        plan = self.study_plan.get_daily_plan(context.principal.user_key, plan_date)
        if plan is None:
            return StudyPlanContract(found=False, plan_date=plan_date)
        items = tuple(
            StudyPlanItemContract(
                item_id=item.id,
                skill=item.skill,
                position=item.position,
                planned_minutes=item.planned_minutes,
                resource_id=item.resource_id,
                resource_title=self._resource_title(item.resource_id),
                status=item.status.value,
                reasons=item.reasons,
                manual_override=item.manual_override,
            )
            for item in plan.items
        )
        return StudyPlanContract(
            found=True,
            plan_id=plan.id,
            plan_date=plan.plan_date,
            status=plan.status.value,
            total_minutes=plan.total_minutes,
            explanation=plan.explanation,
            items=items,
        )

    def get_recent_study_history(
        self,
        context: AgentExecutionContext,
        arguments: RecentHistoryArguments,
    ) -> StudyHistoryContract:
        through_date = arguments.through_date or context.today
        first_date = through_date - timedelta(days=arguments.days - 1)
        history = tuple(
            item
            for item in self.history.list_recent_days(
                context.principal.user_key,
                through_date,
                limit=arguments.days,
            )
            if item.study_date >= first_date
        )
        return StudyHistoryContract(
            through_date=through_date,
            days=arguments.days,
            items=tuple(
                HistoryDayContract(
                    study_date=item.study_date,
                    assigned_modules=item.assigned_module_count,
                    completed_modules=item.completed_module_count,
                    sessions=tuple(
                        HistoricalSessionContract(
                            session_id=session.id,
                            resource_id=session.resource_id,
                            resource_title=session.resource_title,
                            skill=session.skill,
                            completed_at=session.completed_at,
                            actual_duration_seconds=session.actual_duration_seconds,
                            accuracy=session.accuracy,
                            attempt_count=session.attempt_count,
                            incorrect_item_count=session.incorrect_item_count,
                            notes=session.notes,
                        )
                        for session in item.sessions
                    ),
                )
                for item in history
            ),
        )

    def get_skill_profile(
        self,
        context: AgentExecutionContext,
        _: EmptyToolArguments,
    ) -> LearnerProfileContract:
        profile = self.learner_profile.get_current_profile(
            context.principal.user_key
        )
        if profile is None:
            return LearnerProfileContract(found=False)
        return LearnerProfileContract(
            found=True,
            snapshot_id=profile.id,
            calculated_at=profile.calculated_at,
            algorithm_version=profile.algorithm_version,
            skills=tuple(
                SkillProfileContract(
                    skill=item.skill,
                    score=item.score,
                    evidence_status=item.evidence_status.value,
                    sample_count=item.sample_count,
                    average_accuracy=item.average_accuracy,
                    average_confidence=item.average_confidence,
                    average_difficulty=item.average_difficulty,
                    hard_item_rate=item.hard_item_rate,
                    accuracy_trend=item.accuracy_trend,
                    explanation=item.explanation,
                )
                for item in profile.skills
            ),
        )

    def get_due_reviews(
        self,
        context: AgentExecutionContext,
        arguments: DueReviewsArguments,
    ) -> DueReviewsContract:
        due_on = arguments.due_on or context.today
        items = self.review.get_due_reviews(
            context.principal.user_key,
            due_on,
            arguments.limit,
        )
        return DueReviewsContract(
            due_on=due_on,
            total_returned=len(items),
            items=tuple(
                ReviewItemContract(
                    review_item_id=item.review_item_id,
                    target_type=item.target_type.value,
                    target_id=item.target_id,
                    review_step=item.review_step,
                    next_review_date=item.next_review_date,
                    review_count=item.review_count,
                    mastery_status=item.mastery_status.value,
                )
                for item in items
            ),
        )

    def get_weak_skills(
        self,
        context: AgentExecutionContext,
        _: EmptyToolArguments,
    ) -> WeaknessProfileContract:
        assessment = self.weakness_detection.get_current_assessment(
            context.principal.user_key
        )
        if assessment is None:
            return WeaknessProfileContract(found=False)
        return WeaknessProfileContract(
            found=True,
            assessment_id=assessment.id,
            assessed_at=assessment.assessed_at,
            detector_version=assessment.detector_version,
            skills=tuple(
                WeakSkillContract(
                    skill=item.skill,
                    classification=item.classification,
                    smoothed_score=item.smoothed_score,
                    latest_score=item.latest_score,
                    snapshot_count=item.scored_snapshot_count,
                    reasons=item.reasons,
                )
                for item in assessment.skills
            ),
        )

    def search_learning_resources(
        self,
        context: AgentExecutionContext,
        arguments: ResourceSearchArguments,
    ) -> ResourceSearchContract:
        library = self.resources.get_library(
            context.principal.user_key,
            ResourceLibraryFilters(
                search=arguments.search,
                skill=arguments.skill,
                resource_type=arguments.resource_type,
                topic=arguments.topic,
                difficulty=arguments.difficulty,
                completion=arguments.completion,
                favorite_only=arguments.favorite_only,
                saved_for_later_only=arguments.saved_for_later_only,
                sort=arguments.sort,
            ),
            limit=arguments.limit,
        )
        return ResourceSearchContract(
            total_count=library.total_count,
            items=tuple(self._resource_summary(item) for item in library.items),
        )

    def get_resource(
        self,
        context: AgentExecutionContext,
        arguments: ResourceArguments,
    ) -> ResourceDetailContract | MissingResourceContract:
        resource = self.resources.get_user_resource(
            context.principal.user_key,
            arguments.resource_id,
        )
        if resource is None:
            return MissingResourceContract(resource_id=arguments.resource_id)
        summary = self._resource_summary(resource)
        return ResourceDetailContract(
            **summary.model_dump(),
            source_url=resource.source_url,
            description=resource.description,
            content_text=resource.content_text,
            transcript=resource.transcript,
            notes=resource.notes,
        )

    def recommend_resources(
        self,
        context: AgentExecutionContext,
        arguments: ResourceRecommendationArguments,
    ) -> ResourceRecommendationsContract:
        target_date = arguments.target_date or context.today
        assessment = self.weakness_detection.get_current_assessment(
            context.principal.user_key
        )
        classification = SkillClassification.INSUFFICIENT_EVIDENCE
        if assessment is not None:
            matching = next(
                (item for item in assessment.skills if item.skill is arguments.skill),
                None,
            )
            if matching is not None:
                classification = matching.classification
        recommendations = self.resources.recommend_resources(
            context.principal.user_key,
            arguments.skill,
            classification,
            target_date,
            count=arguments.count,
            difficulty=arguments.difficulty,
        )
        output = []
        for recommendation in recommendations:
            resource = self.resources.get_resource(recommendation.resource_id)
            if resource is None:
                continue
            output.append(
                ResourceRecommendationContract(
                    resource_id=resource.id,
                    title=resource.title,
                    skill=resource.skill,
                    difficulty=resource.difficulty,
                    score=recommendation.score,
                    reasons=recommendation.reasons,
                )
            )
        return ResourceRecommendationsContract(
            target_date=target_date,
            skill=arguments.skill,
            classification=classification,
            items=tuple(output),
        )

    def generate_weekly_report(
        self,
        context: AgentExecutionContext,
        arguments: DatedToolArguments,
    ) -> WeeklyReportContract:
        today = arguments.on_date or context.today
        report = self.weekly_review.get_current_week(
            context.principal.user_key,
            today,
        )
        return WeeklyReportContract(
            week_start=report.week_start,
            week_end=report.week_end,
            study_days=report.study_days,
            assigned_modules=report.assigned_modules,
            completed_modules=report.completed_modules,
            completion_rate=report.completion_rate,
            completed_planned_minutes=report.completed_planned_minutes,
            completed_sessions=report.completed_sessions,
            tracked_seconds=report.tracked_seconds,
            vocabulary_learned=report.vocabulary_learned,
            difficult_sentences_collected=report.difficult_sentences_collected,
            review_attempt_count=report.review_attempts.total_count,
            review_retention_rate=report.review_attempts.retention_rate,
            next_week_review_count=report.next_week_review_count,
            strongest_skill=report.strongest_skill,
            weakest_skill=report.weakest_skill,
            skill_summaries=tuple(
                WeeklySkillContract(
                    skill=item.skill,
                    completed_modules=item.completed_modules,
                    completed_sessions=item.completed_sessions,
                    average_accuracy=item.average_accuracy,
                    incorrect_item_count=item.incorrect_item_count,
                    tracked_seconds=item.tracked_seconds,
                )
                for item in report.skill_summaries
            ),
            recommendations=tuple(
                WeeklyRecommendationContract(
                    title=item.title,
                    reason=item.reason,
                    href=item.href,
                )
                for item in report.recommendations
            ),
        )

    def save_ai_recommendation(
        self,
        context: AgentExecutionContext,
        arguments: SaveAIRecommendationArguments,
    ) -> SavedAIRecommendationContract:
        decision = self.adaptation_decisions.save_ai_recommendation(
            context.principal.user_key,
            arguments.plan_date,
            arguments.study_plan_item_id,
            proposed_minutes=arguments.proposed_minutes,
            proposed_resource_id=arguments.proposed_resource_id,
            reasons=arguments.reasons,
            provider_name=arguments.provider_name,
            model_name=arguments.model_name,
        )
        return SavedAIRecommendationContract(
            decision_id=decision.id,
            study_plan_id=decision.study_plan_id,
            study_plan_item_id=decision.study_plan_item_id,
            skill=decision.skill,
            current_minutes=decision.previous_planned_minutes,
            proposed_minutes=decision.new_planned_minutes,
            current_resource_id=decision.previous_resource_id,
            proposed_resource_id=decision.new_resource_id,
            reasons=decision.reasons,
        )

    def _resource_title(self, resource_id: int | None) -> str | None:
        if resource_id is None:
            return None
        resource = self.resources.get_resource(resource_id)
        return resource.title if resource else None

    @staticmethod
    def _resource_summary(resource) -> ResourceSummaryContract:
        return ResourceSummaryContract(
            resource_id=resource.id,
            title=resource.title,
            resource_type=resource.resource_type,
            skill=resource.skill,
            topic=resource.topic,
            difficulty=resource.difficulty,
            estimated_duration_minutes=resource.estimated_duration_minutes,
            tags=resource.tags,
            favorite=resource.favorite,
            saved_for_later=resource.saved_for_later,
            completed_session_count=resource.completed_session_count,
        )


def build_learning_agent_tool_registry(
    *,
    learner_profile: LearnerProfileService,
    weakness_detection: WeaknessDetectionService,
    resources: ResourceService,
    study_plan: StudyPlanService,
    history: HistoryService,
    review: ReviewService,
    weekly_review: WeeklyReviewService,
    adaptation_decisions: AdaptationDecisionService,
    authorization_policy: AgentToolAuthorizationPolicy | None = None,
) -> AgentToolRegistry:
    handlers = LearningAgentToolHandlers(
        learner_profile=learner_profile,
        weakness_detection=weakness_detection,
        resources=resources,
        study_plan=study_plan,
        history=history,
        review=review,
        weekly_review=weekly_review,
        adaptation_decisions=adaptation_decisions,
    )
    permission = AgentPermission.READ_LEARNING_DATA
    tools: tuple[AgentTool[BaseModel, BaseModel], ...] = (
        _tool(
            AgentToolName.GET_TODAY_PLAN,
            "Read a persisted study plan for a date. This never creates a plan.",
            DatedToolArguments,
            handlers.get_today_plan,
            permission,
        ),
        _tool(
            AgentToolName.GET_RECENT_STUDY_HISTORY,
            "Read recent study days and measured session results.",
            RecentHistoryArguments,
            handlers.get_recent_study_history,
            permission,
        ),
        _tool(
            AgentToolName.GET_SKILL_PROFILE,
            "Read the latest measured learner skill profile.",
            EmptyToolArguments,
            handlers.get_skill_profile,
            permission,
        ),
        _tool(
            AgentToolName.GET_DUE_REVIEWS,
            "Read spaced-review items due on a date.",
            DueReviewsArguments,
            handlers.get_due_reviews,
            permission,
        ),
        _tool(
            AgentToolName.GET_WEAK_SKILLS,
            "Read the latest explainable weakness assessment.",
            EmptyToolArguments,
            handlers.get_weak_skills,
            permission,
        ),
        _tool(
            AgentToolName.SEARCH_LEARNING_RESOURCES,
            "Search the learner-visible resource library with typed filters.",
            ResourceSearchArguments,
            handlers.search_learning_resources,
            permission,
        ),
        _tool(
            AgentToolName.GET_RESOURCE,
            "Read one learner-visible learning resource.",
            ResourceArguments,
            handlers.get_resource,
            permission,
        ),
        _tool(
            AgentToolName.RECOMMEND_RESOURCES,
            "Get deterministic resource recommendations for one skill.",
            ResourceRecommendationArguments,
            handlers.recommend_resources,
            permission,
        ),
        _tool(
            AgentToolName.GENERATE_WEEKLY_REPORT,
            "Read a weekly report calculated from persisted learning evidence.",
            DatedToolArguments,
            handlers.generate_weekly_report,
            permission,
        ),
        _tool(
            AgentToolName.SAVE_AI_RECOMMENDATION,
            "Save an explainable AI suggestion without changing the study plan.",
            SaveAIRecommendationArguments,
            handlers.save_ai_recommendation,
            AgentPermission.SAVE_AI_RECOMMENDATION,
        ),
    )
    return AgentToolRegistry(tools, authorization_policy)


def _tool(
    name: AgentToolName,
    description: str,
    input_contract: type[InputContract],
    handler: Callable[[AgentExecutionContext, InputContract], OutputContract],
    required_permission: AgentPermission,
) -> AgentTool[InputContract, OutputContract]:
    return AgentTool(
        definition=AgentToolDefinition(
            name=name,
            description=description,
            input_schema=input_contract.model_json_schema(),
            required_permission=required_permission,
        ),
        input_contract=input_contract,
        handler=handler,
    )


class AgentToolInputError(ValueError):
    def __init__(self, tool_name: AgentToolName, error: ValidationError) -> None:
        super().__init__(f"Invalid input for {tool_name.value}: {error}")
