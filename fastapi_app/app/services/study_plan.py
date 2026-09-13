from datetime import date

from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.entities import (
    DailyStudyPlan,
    SkillPlanningSignal,
    StudyPlanGenerationContext,
)
from app.domain.study_plan.generator import StudyPlanGenerator
from app.domain.study_plan.repository import StudyPlanRepository
from app.domain.weakness_detection.entities import (
    SkillClassification,
    WeaknessAssessmentRun,
)
from app.services.resources import ResourceService
from app.services.weakness_detection import WeaknessDetectionService


class StudyPlanService:
    def __init__(
        self,
        repository: StudyPlanRepository,
        weakness_service: WeaknessDetectionService,
        resource_service: ResourceService,
        generator: StudyPlanGenerator,
    ) -> None:
        self.repository = repository
        self.weakness_service = weakness_service
        self.resource_service = resource_service
        self.generator = generator

    def get_or_create_daily_plan(
        self,
        user_key: str,
        plan_date: date,
    ) -> DailyStudyPlan:
        existing = self.repository.get_for_date(user_key, plan_date)
        if existing is not None:
            return existing
        assessment = self.weakness_service.get_current_assessment(user_key)
        if assessment is None:
            assessment = self.weakness_service.refresh_assessment(user_key)
        context = StudyPlanGenerationContext(
            user_key=user_key,
            plan_date=plan_date,
            weakness_assessment_run_id=assessment.id,
            recommender_version=self.resource_service.recommender_version,
            skill_signals=self._build_signals(user_key, plan_date, assessment),
        )
        return self.repository.save(self.generator.generate(context))

    def get_daily_plan(self, user_key: str, plan_date: date) -> DailyStudyPlan | None:
        return self.repository.get_for_date(user_key, plan_date)

    def _build_signals(
        self,
        user_key: str,
        plan_date: date,
        assessment: WeaknessAssessmentRun,
    ) -> tuple[SkillPlanningSignal, ...]:
        assessments = {item.skill: item for item in assessment.skills}
        signals = []
        for skill in Skill:
            skill_assessment = assessments.get(skill)
            classification = (
                skill_assessment.classification
                if skill_assessment
                else SkillClassification.INSUFFICIENT_EVIDENCE
            )
            signals.append(
                SkillPlanningSignal(
                    skill=skill,
                    classification=classification,
                    assessment_reasons=(
                        skill_assessment.reasons
                        if skill_assessment
                        else ("该技能尚无评估记录。",)
                    ),
                    resource_recommendation=self.resource_service.recommend_for_skill(
                        user_key,
                        skill,
                        classification,
                        plan_date,
                    ),
                )
            )
        return tuple(signals)
