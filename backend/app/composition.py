from dataclasses import dataclass
from importlib.util import find_spec
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.ai_agent.tools import AgentToolRegistry, build_learning_agent_tool_registry
from app.ai_agent.service import LearningAgentService
from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.domain.ai_evaluation.evaluator import WorkEvaluator
from app.domain.ai_evaluation.mock_evaluator import UnavailableWorkEvaluator
from app.domain.resources.rule_based_recommender import RuleBasedResourceRecommender
from app.domain.review.fixed_interval_scheduler import FixedIntervalReviewScheduler
from app.domain.study_plan.rule_based_generator import RuleBasedStudyPlanGenerator
from app.domain.weakness_detection.rule_based_detector import RuleBasedWeaknessDetector
from app.repositories.sqlalchemy_adaptive_learning import (
    SqlAlchemyAdaptationDecisionRepository,
)
from app.repositories.sqlalchemy_agent_coaching import (
    SqlAlchemyAgentCoachingRepository,
)
from app.repositories.sqlalchemy_ai_evaluation import (
    SqlAlchemyWorkEvaluationRepository,
)
from app.repositories.sqlalchemy_history import SqlAlchemyStudyHistoryRepository
from app.repositories.sqlalchemy_ielts import SqlAlchemyIeltsPracticeRepository
from app.repositories.sqlalchemy_learning_evidence import SqlAlchemyLearningEvidenceRepository
from app.repositories.sqlalchemy_listening import SqlAlchemyListeningSentenceRepository
from app.repositories.sqlalchemy_notebook import SqlAlchemyNotebookRepository
from app.repositories.sqlalchemy_learner_profile import SqlAlchemyLearnerProfileRepository
from app.repositories.sqlalchemy_resources import SqlAlchemyResourceRepository
from app.repositories.sqlalchemy_review import SqlAlchemyReviewRepository
from app.repositories.sqlalchemy_speaking import SqlAlchemySpeakingPracticeRepository
from app.repositories.sqlalchemy_study_plan import SqlAlchemyStudyPlanRepository
from app.repositories.sqlalchemy_study_session import SqlAlchemyStudySessionRepository
from app.repositories.sqlalchemy_vocabulary import SqlAlchemyVocabularyRepository
from app.repositories.sqlalchemy_weakness_detection import (
    SqlAlchemyWeaknessAssessmentRepository,
)
from app.repositories.sqlalchemy_writing import SqlAlchemyWritingRepository
from app.services.adaptive_learning import AdaptationDecisionService
from app.services.agent_coaching import AgentCoachingService
from app.services.agent_planning import AgentPlanningService
from app.services.ai_evaluation import LearningWorkEvaluationService
from app.services.dashboard import DashboardService
from app.services.history import HistoryService
from app.services.ielts_learning_evidence import IeltsLearningEvidenceRecorder
from app.services.ielts_practice import IeltsPracticeService
from app.services.learning_evidence import LearningEvidenceService
from app.services.listening import ListeningPracticeService
from app.services.learner_profile import LearnerProfileService
from app.services.progress_analytics import ProgressAnalyticsService
from app.services.notebook import NotebookService
from app.services.resources import ResourceService
from app.services.review import ReviewService
from app.services.speaking import SpeakingPracticeService
from app.services.study_plan import StudyPlanService
from app.services.study_session import StudySessionService
from app.services.weakness_detection import WeaknessDetectionService
from app.services.vocabulary import VocabularyService
from app.services.weekly_review import WeeklyReviewService
from app.services.writing import WritingPracticeService


@dataclass(frozen=True)
class ApplicationServices:
    ielts_practice: IeltsPracticeService
    learner_profile: LearnerProfileService
    weakness_detection: WeaknessDetectionService
    resources: ResourceService
    study_plan: StudyPlanService
    study_sessions: StudySessionService
    adaptation_decisions: AdaptationDecisionService
    history: HistoryService
    progress_analytics: ProgressAnalyticsService
    vocabulary: VocabularyService
    review: ReviewService
    listening: ListeningPracticeService
    speaking: SpeakingPracticeService
    writing: WritingPracticeService
    notebook: NotebookService
    weekly_review: WeeklyReviewService
    dashboard: DashboardService
    ai_evaluation: LearningWorkEvaluationService
    agent_coaching: AgentCoachingService
    agent_planning: AgentPlanningService


def build_application_services(session: Session) -> ApplicationServices:
    evidence_service = LearningEvidenceService(SqlAlchemyLearningEvidenceRepository(session))
    profile_service = LearnerProfileService(
        evidence_service,
        SqlAlchemyLearnerProfileRepository(session),
        RuleBasedSkillEvaluator(),
    )
    weakness_service = WeaknessDetectionService(
        profile_service,
        SqlAlchemyWeaknessAssessmentRepository(session),
        RuleBasedWeaknessDetector(),
    )
    resource_repository = SqlAlchemyResourceRepository(session)
    resource_service = ResourceService(
        resource_repository,
        RuleBasedResourceRecommender(),
    )
    review_scheduler = FixedIntervalReviewScheduler()
    vocabulary_repository = SqlAlchemyVocabularyRepository(
        session, review_scheduler.scheduler_version
    )
    vocabulary_service = VocabularyService(
        vocabulary_repository,
        resource_repository,
        review_scheduler,
    )
    review_repository = SqlAlchemyReviewRepository(session)
    review_service = ReviewService(review_repository, review_scheduler)
    listening_repository = SqlAlchemyListeningSentenceRepository(
        session, review_scheduler.scheduler_version
    )
    listening_service = ListeningPracticeService(
        listening_repository,
        resource_repository,
        review_scheduler,
    )
    speaking_repository = SqlAlchemySpeakingPracticeRepository(session)
    speaking_service = SpeakingPracticeService(
        speaking_repository,
        resource_repository,
        evidence_service,
        profile_service,
        weakness_service,
    )
    writing_repository = SqlAlchemyWritingRepository(session)
    writing_service = WritingPracticeService(
        writing_repository,
        resource_repository,
        evidence_service,
        profile_service,
        weakness_service,
    )
    notebook_service = NotebookService(
        SqlAlchemyNotebookRepository(session),
        resource_repository,
    )
    plan_repository = SqlAlchemyStudyPlanRepository(session)
    history_repository = SqlAlchemyStudyHistoryRepository(session)
    study_plan_service = StudyPlanService(
        plan_repository,
        weakness_service,
        resource_service,
        RuleBasedStudyPlanGenerator(),
    )
    study_session_service = StudySessionService(
        SqlAlchemyStudySessionRepository(session),
        study_plan_service,
        profile_service,
        weakness_service,
    )
    adaptation_service = AdaptationDecisionService(
        plan_repository,
        SqlAlchemyAdaptationDecisionRepository(session),
        resource_service,
    )
    timezone = ZoneInfo("Australia/Sydney")
    history_service = HistoryService(
        plan_repository,
        history_repository,
        timezone,
    )
    progress_analytics_service = ProgressAnalyticsService(
        plan_repository,
        history_repository,
        profile_service,
        weakness_service,
        review_repository,
        timezone,
    )
    weekly_review_service = WeeklyReviewService(
        plan_repository,
        history_repository,
        vocabulary_repository,
        listening_repository,
        review_repository,
        timezone,
    )
    dashboard_service = DashboardService(
        study_plan_service,
        progress_analytics_service,
        review_service,
        weekly_review_service,
    )
    ai_evaluation_service = LearningWorkEvaluationService(
        SqlAlchemyWorkEvaluationRepository(session),
        build_work_evaluator(),
        resource_repository,
        writing_repository,
        speaking_repository,
    )
    evidence_recorder = IeltsLearningEvidenceRecorder(
        evidence_service,
        profile_service,
        weakness_service,
    )
    ielts_service = IeltsPracticeService(
        SqlAlchemyIeltsPracticeRepository(session),
        submission_observer=evidence_recorder,
    )
    agent_registry = build_learning_agent_tool_registry(
        learner_profile=profile_service,
        weakness_detection=weakness_service,
        resources=resource_service,
        study_plan=study_plan_service,
        history=history_service,
        review=review_service,
        weekly_review=weekly_review_service,
        adaptation_decisions=adaptation_service,
    )
    agent_available, unavailable_reason = learning_agent_configuration()
    agent_coaching_service = AgentCoachingService(
        SqlAlchemyAgentCoachingRepository(session),
        lambda: _build_learning_agent_service(agent_registry),
        available=agent_available,
        unavailable_reason=unavailable_reason,
    )
    agent_planning_service = AgentPlanningService(
        adaptation_service,
        lambda: _build_learning_agent_service(agent_registry),
        available=agent_available,
        unavailable_reason=unavailable_reason,
    )
    return ApplicationServices(
        ielts_practice=ielts_service,
        learner_profile=profile_service,
        weakness_detection=weakness_service,
        resources=resource_service,
        study_plan=study_plan_service,
        study_sessions=study_session_service,
        adaptation_decisions=adaptation_service,
        history=history_service,
        progress_analytics=progress_analytics_service,
        vocabulary=vocabulary_service,
        review=review_service,
        listening=listening_service,
        speaking=speaking_service,
        writing=writing_service,
        notebook=notebook_service,
        weekly_review=weekly_review_service,
        dashboard=dashboard_service,
        ai_evaluation=ai_evaluation_service,
        agent_coaching=agent_coaching_service,
        agent_planning=agent_planning_service,
    )


def build_agent_tool_registry(services: ApplicationServices) -> AgentToolRegistry:
    """Expose application services to an agent without exposing persistence."""
    return build_learning_agent_tool_registry(
        learner_profile=services.learner_profile,
        weakness_detection=services.weakness_detection,
        resources=services.resources,
        study_plan=services.study_plan,
        history=services.history,
        review=services.review,
        weekly_review=services.weekly_review,
        adaptation_decisions=services.adaptation_decisions,
    )


def build_work_evaluator() -> WorkEvaluator:
    from app.config import settings

    available, _ = learning_agent_configuration()
    if not available:
        return UnavailableWorkEvaluator()
    if settings.ai_provider == "openrouter":
        from app.integrations.openrouter.work_evaluator import (
            OpenRouterWorkEvaluator,
        )

        return OpenRouterWorkEvaluator(
            model=settings.openrouter_model,
            fallback_model=settings.openrouter_fallback_model,
            api_key=_secret_value(settings.openrouter_api_key),
            max_output_tokens=settings.openrouter_max_output_tokens,
        )
    from app.integrations.openai.work_evaluator import OpenAIWorkEvaluator

    return OpenAIWorkEvaluator(
        model=settings.openai_model,
        api_key=_secret_value(settings.openai_api_key),
        max_output_tokens=settings.openai_max_output_tokens,
    )


def build_learning_agent_service(
    services: ApplicationServices,
) -> LearningAgentService | None:
    return _build_learning_agent_service(build_agent_tool_registry(services))


def _build_learning_agent_service(
    registry: AgentToolRegistry,
) -> LearningAgentService | None:
    from app.config import settings

    available, _ = learning_agent_configuration()
    if not available:
        return None
    if settings.ai_provider == "openrouter":
        from app.integrations.openrouter.responses_provider import (
            OpenRouterChatProvider,
        )

        provider = OpenRouterChatProvider(
            model=settings.openrouter_model,
            fallback_model=settings.openrouter_fallback_model,
            api_key=_secret_value(settings.openrouter_api_key),
            max_output_tokens=settings.openrouter_max_output_tokens,
        )
        return LearningAgentService(provider, registry)
    from app.integrations.openai.responses_provider import OpenAIResponsesProvider

    provider = OpenAIResponsesProvider(
        model=settings.openai_model,
        api_key=_secret_value(settings.openai_api_key),
        max_output_tokens=settings.openai_max_output_tokens,
    )
    return LearningAgentService(provider, registry)


def learning_agent_configuration() -> tuple[bool, str]:
    from app.config import settings

    if settings.ai_provider == "disabled":
        return False, "AI 尚未启用；请先配置服务器端 AI Provider。"
    if settings.ai_provider == "openrouter":
        if not settings.openrouter_model.strip():
            return False, "缺少 OPENROUTER_MODEL 配置。"
        primary = settings.openrouter_model.strip()
        if not (primary.endswith(":free") or primary == "openrouter/free"):
            return False, "OpenRouter 模型必须明确使用 :free 免费版本。"
        fallback = settings.openrouter_fallback_model.strip()
        if not (fallback.endswith(":free") or fallback == "openrouter/free"):
            return False, "OpenRouter 备用模型必须使用免费版本。"
        if not _secret_value(settings.openrouter_api_key):
            return False, "缺少服务器端 OPENROUTER_API_KEY。"
    else:
        if not settings.openai_model.strip():
            return False, "缺少 OPENAI_MODEL 配置。"
        if not _secret_value(settings.openai_api_key):
            return False, "缺少服务器端 OPENAI_API_KEY。"
    if find_spec("openai") is None:
        return False, "尚未安装可选 AI 依赖，请运行 pip install -e '.[ai]'。"
    return True, ""


def _secret_value(secret) -> str | None:
    if secret is None:
        return None
    return secret.get_secret_value().strip() or None
