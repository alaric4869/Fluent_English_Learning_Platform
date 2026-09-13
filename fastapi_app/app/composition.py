from dataclasses import dataclass
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.domain.resources.rule_based_recommender import RuleBasedResourceRecommender
from app.domain.study_plan.rule_based_generator import RuleBasedStudyPlanGenerator
from app.domain.weakness_detection.rule_based_detector import RuleBasedWeaknessDetector
from app.repositories.sqlalchemy_adaptive_learning import (
    SqlAlchemyAdaptationDecisionRepository,
)
from app.repositories.sqlalchemy_ielts import SqlAlchemyIeltsPracticeRepository
from app.repositories.sqlalchemy_history import SqlAlchemyStudyHistoryRepository
from app.repositories.sqlalchemy_learning_evidence import SqlAlchemyLearningEvidenceRepository
from app.repositories.sqlalchemy_learner_profile import SqlAlchemyLearnerProfileRepository
from app.repositories.sqlalchemy_resources import SqlAlchemyResourceRepository
from app.repositories.sqlalchemy_study_plan import SqlAlchemyStudyPlanRepository
from app.repositories.sqlalchemy_weakness_detection import (
    SqlAlchemyWeaknessAssessmentRepository,
)
from app.services.adaptive_learning import AdaptationDecisionService
from app.services.ielts_learning_evidence import IeltsLearningEvidenceRecorder
from app.services.ielts_practice import IeltsPracticeService
from app.services.history import HistoryService
from app.services.learning_evidence import LearningEvidenceService
from app.services.learner_profile import LearnerProfileService
from app.services.resources import ResourceService
from app.services.progress_analytics import ProgressAnalyticsService
from app.services.study_plan import StudyPlanService
from app.services.weakness_detection import WeaknessDetectionService


@dataclass(frozen=True)
class ApplicationServices:
    ielts_practice: IeltsPracticeService
    learner_profile: LearnerProfileService
    weakness_detection: WeaknessDetectionService
    resources: ResourceService
    study_plan: StudyPlanService
    adaptation_decisions: AdaptationDecisionService
    history: HistoryService
    progress_analytics: ProgressAnalyticsService


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
    resource_service = ResourceService(
        SqlAlchemyResourceRepository(session),
        RuleBasedResourceRecommender(),
    )
    plan_repository = SqlAlchemyStudyPlanRepository(session)
    history_repository = SqlAlchemyStudyHistoryRepository(session)
    study_plan_service = StudyPlanService(
        plan_repository,
        weakness_service,
        resource_service,
        RuleBasedStudyPlanGenerator(),
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
        timezone,
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
        adaptation_decisions=adaptation_service,
        history=history_service,
        progress_analytics=progress_analytics_service,
    )
