from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.learning_evidence.entities import Skill
from app.domain.weakness_detection.entities import (
    SkillClassification,
    SkillWeaknessAssessment,
    WeaknessAssessmentEvaluation,
    WeaknessAssessmentRun,
)
from app.models.learner_profile import LearnerProfile
from app.models.weakness_detection import (
    WeaknessAssessmentRunModel,
    WeaknessSkillAssessmentModel,
)


class SqlAlchemyWeaknessAssessmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_run(self, evaluation: WeaknessAssessmentEvaluation) -> WeaknessAssessmentRun:
        profile = self.session.scalar(
            select(LearnerProfile).where(LearnerProfile.user_key == evaluation.user_key)
        )
        if profile is None:
            raise LookupError("Learner profile must exist before weakness detection")

        existing = self.session.scalar(
            select(WeaknessAssessmentRunModel)
            .where(
                WeaknessAssessmentRunModel.learner_profile_id == profile.id,
                WeaknessAssessmentRunModel.detector_version == evaluation.detector_version,
                WeaknessAssessmentRunModel.evidence_fingerprint
                == evaluation.evidence_fingerprint,
            )
            .options(selectinload(WeaknessAssessmentRunModel.skills))
        )
        if existing is not None:
            return self._to_run(existing, evaluation.user_key, created=False)

        assessment_run = WeaknessAssessmentRunModel(
            learner_profile_id=profile.id,
            assessed_at=evaluation.assessed_at,
            detector_version=evaluation.detector_version,
            evidence_fingerprint=evaluation.evidence_fingerprint,
        )
        self.session.add(assessment_run)
        self.session.flush()
        self.session.add_all(
            [
                WeaknessSkillAssessmentModel(
                    assessment_run_id=assessment_run.id,
                    skill=item.skill.value,
                    classification=item.classification.value,
                    smoothed_score=item.smoothed_score,
                    latest_score=item.latest_score,
                    scored_snapshot_count=item.scored_snapshot_count,
                    latest_average_accuracy=item.latest_average_accuracy,
                    latest_average_confidence=item.latest_average_confidence,
                    latest_hard_item_rate=item.latest_hard_item_rate,
                    latest_accuracy_trend=item.latest_accuracy_trend,
                    evidence_snapshot_ids=list(item.evidence_snapshot_ids),
                    reasons=list(item.reasons),
                )
                for item in evaluation.skills
            ]
        )
        self.session.commit()
        saved = self._get_run(assessment_run.id)
        return self._to_run(saved, evaluation.user_key, created=True)

    def get_latest(self, user_key: str) -> WeaknessAssessmentRun | None:
        statement = (
            select(WeaknessAssessmentRunModel)
            .join(LearnerProfile)
            .where(LearnerProfile.user_key == user_key)
            .options(selectinload(WeaknessAssessmentRunModel.skills))
            .order_by(
                WeaknessAssessmentRunModel.assessed_at.desc(),
                WeaknessAssessmentRunModel.id.desc(),
            )
            .limit(1)
        )
        assessment_run = self.session.scalar(statement)
        return self._to_run(assessment_run, user_key, created=False) if assessment_run else None

    def _get_run(self, run_id: int) -> WeaknessAssessmentRunModel:
        statement = (
            select(WeaknessAssessmentRunModel)
            .where(WeaknessAssessmentRunModel.id == run_id)
            .options(selectinload(WeaknessAssessmentRunModel.skills))
        )
        return self.session.scalars(statement).one()

    @staticmethod
    def _to_run(
        assessment_run: WeaknessAssessmentRunModel,
        user_key: str,
        *,
        created: bool,
    ) -> WeaknessAssessmentRun:
        skill_order = {skill.value: index for index, skill in enumerate(Skill)}
        skills = tuple(
            SkillWeaknessAssessment(
                skill=Skill(item.skill),
                classification=SkillClassification(item.classification),
                smoothed_score=item.smoothed_score,
                latest_score=item.latest_score,
                scored_snapshot_count=item.scored_snapshot_count,
                latest_average_accuracy=item.latest_average_accuracy,
                latest_average_confidence=item.latest_average_confidence,
                latest_hard_item_rate=item.latest_hard_item_rate,
                latest_accuracy_trend=item.latest_accuracy_trend,
                evidence_snapshot_ids=tuple(item.evidence_snapshot_ids),
                reasons=tuple(item.reasons),
            )
            for item in sorted(
                assessment_run.skills,
                key=lambda row: skill_order[row.skill],
            )
        )
        return WeaknessAssessmentRun(
            id=assessment_run.id,
            user_key=user_key,
            assessed_at=assessment_run.assessed_at,
            detector_version=assessment_run.detector_version,
            evidence_fingerprint=assessment_run.evidence_fingerprint,
            skills=skills,
            created=created,
        )
