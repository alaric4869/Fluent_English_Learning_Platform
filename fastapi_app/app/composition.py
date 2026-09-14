from dataclasses import dataclass
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.domain.resources.rule_based_recommender import RuleBasedResourceRecommender
from app.domain.review.fixed_interval_scheduler import FixedIntervalReviewScheduler
from app.domain.study_plan.rule_based_generator import RuleBasedStudyPlanGenerator
from app.domain.weakness_detection.rule_based_detector import RuleBasedWeaknessDetector
from app.repositories.sqlalchemy_adaptive_learning import (
    SqlAlchemyAdaptationDecisionRepository,
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
    speaking_service = SpeakingPracticeService(
        SqlAlchemySpeakingPracticeRepository(session),
        resource_repository,
        evidence_service,
        profile_service,
        weakness_service,
    )
    writing_service = WritingPracticeService(
        SqlAlchemyWritingRepository(session),
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
    evidence_recorder = IeltsLearningEvidenceRecorder(
        evidence_service,
        profile_service,
        weakness_service,
    )
    ielts_service = IeltsPracticeService(
        SqlAlchemyIeltsPracticeRepository(session),
        submission_observer=evidence_recorder,
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
    )
