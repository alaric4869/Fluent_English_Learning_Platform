from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import (
    EvidenceStatus,
    HistoricalSkillProfile,
    LearnerProfileEvaluation,
    LearnerProfileSnapshot,
    SkillProfileEvaluation,
)
from app.models.learner_profile import (
    LearnerProfile,
    LearnerProfileSnapshotModel,
    LearnerSkillSnapshot,
)


class SqlAlchemyLearnerProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_snapshot(self, evaluation: LearnerProfileEvaluation) -> LearnerProfileSnapshot:
        profile = self.session.scalar(
            select(LearnerProfile).where(LearnerProfile.user_key == evaluation.user_key)
        )
        if profile is None:
            profile = LearnerProfile(user_key=evaluation.user_key)
            self.session.add(profile)
            self.session.flush()

        existing = self.session.scalar(
            select(LearnerProfileSnapshotModel)
            .where(
                LearnerProfileSnapshotModel.learner_profile_id == profile.id,
                LearnerProfileSnapshotModel.algorithm_version == evaluation.algorithm_version,
                LearnerProfileSnapshotModel.evidence_fingerprint
                == evaluation.evidence_fingerprint,
            )
            .options(selectinload(LearnerProfileSnapshotModel.skills))
        )
        if existing is not None:
            return self._to_snapshot(existing, profile.user_key, created=False)

        snapshot = LearnerProfileSnapshotModel(
            learner_profile_id=profile.id,
            calculated_at=evaluation.calculated_at,
            algorithm_version=evaluation.algorithm_version,
            evidence_fingerprint=evaluation.evidence_fingerprint,
        )
        self.session.add(snapshot)
        self.session.flush()
        self.session.add_all(
            [
                LearnerSkillSnapshot(
                    profile_snapshot_id=snapshot.id,
                    skill=item.skill.value,
                    score=item.score,
                    evidence_status=item.evidence_status.value,
                    sample_count=item.sample_count,
                    average_accuracy=item.average_accuracy,
                    average_confidence=item.average_confidence,
                    average_difficulty=item.average_difficulty,
                    hard_item_rate=item.hard_item_rate,
                    accuracy_trend=item.accuracy_trend,
                    evidence_ids=list(item.evidence_ids),
                    calculation_weights=item.calculation_weights,
                    explanation=item.explanation,
                )
                for item in evaluation.skills
            ]
        )
        profile.updated_at = evaluation.calculated_at
        self.session.commit()
        saved = self._get_snapshot(snapshot.id)
        return self._to_snapshot(saved, profile.user_key, created=True)

    def get_latest(self, user_key: str) -> LearnerProfileSnapshot | None:
        statement = (
            select(LearnerProfileSnapshotModel)
            .join(LearnerProfile)
            .where(LearnerProfile.user_key == user_key)
            .options(selectinload(LearnerProfileSnapshotModel.skills))
            .order_by(
                LearnerProfileSnapshotModel.calculated_at.desc(),
                LearnerProfileSnapshotModel.id.desc(),
            )
            .limit(1)
        )
        snapshot = self.session.scalar(statement)
        return self._to_snapshot(snapshot, user_key, created=False) if snapshot else None

    def list_recent_skill_profiles(
        self,
        user_key: str,
        skill: Skill,
        limit: int,
    ) -> tuple[HistoricalSkillProfile, ...]:
        statement = (
            select(LearnerSkillSnapshot, LearnerProfileSnapshotModel)
            .join(
                LearnerProfileSnapshotModel,
                LearnerProfileSnapshotModel.id == LearnerSkillSnapshot.profile_snapshot_id,
            )
            .join(
                LearnerProfile,
                LearnerProfile.id == LearnerProfileSnapshotModel.learner_profile_id,
            )
            .where(
                LearnerProfile.user_key == user_key,
                LearnerSkillSnapshot.skill == skill.value,
            )
            .order_by(
                LearnerProfileSnapshotModel.calculated_at.desc(),
                LearnerProfileSnapshotModel.id.desc(),
            )
            .limit(limit)
        )
        return tuple(
            HistoricalSkillProfile(
                skill_snapshot_id=item.id,
                profile_snapshot_id=snapshot.id,
                calculated_at=snapshot.calculated_at,
                skill=Skill(item.skill),
                score=item.score,
                evidence_status=EvidenceStatus(item.evidence_status),
                sample_count=item.sample_count,
                average_accuracy=item.average_accuracy,
                average_confidence=item.average_confidence,
                average_difficulty=item.average_difficulty,
                hard_item_rate=item.hard_item_rate,
                accuracy_trend=item.accuracy_trend,
            )
            for item, snapshot in self.session.execute(statement)
        )

    def _get_snapshot(self, snapshot_id: int) -> LearnerProfileSnapshotModel:
        statement = (
            select(LearnerProfileSnapshotModel)
            .where(LearnerProfileSnapshotModel.id == snapshot_id)
            .options(selectinload(LearnerProfileSnapshotModel.skills))
        )
        return self.session.scalars(statement).one()

    @staticmethod
    def _to_snapshot(
        snapshot: LearnerProfileSnapshotModel,
        user_key: str,
        *,
        created: bool,
    ) -> LearnerProfileSnapshot:
        skill_order = {skill.value: index for index, skill in enumerate(Skill)}
        skills = tuple(
            SkillProfileEvaluation(
                skill=Skill(item.skill),
                score=item.score,
                evidence_status=EvidenceStatus(item.evidence_status),
                sample_count=item.sample_count,
                average_accuracy=item.average_accuracy,
                average_confidence=item.average_confidence,
                average_difficulty=item.average_difficulty,
                hard_item_rate=item.hard_item_rate,
                accuracy_trend=item.accuracy_trend,
                evidence_ids=tuple(item.evidence_ids),
                calculation_weights=dict(item.calculation_weights),
                explanation=item.explanation,
            )
            for item in sorted(snapshot.skills, key=lambda row: skill_order[row.skill])
        )
        return LearnerProfileSnapshot(
            id=snapshot.id,
            user_key=user_key,
            calculated_at=snapshot.calculated_at,
            algorithm_version=snapshot.algorithm_version,
            evidence_fingerprint=snapshot.evidence_fingerprint,
            skills=skills,
            created=created,
        )
