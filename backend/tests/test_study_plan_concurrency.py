from datetime import date
from unittest.mock import MagicMock, Mock

from sqlalchemy.exc import IntegrityError

from app.domain.study_plan.entities import StudyPlanProposal
from app.repositories.sqlalchemy_study_plan import SqlAlchemyStudyPlanRepository


def test_concurrent_plan_insert_returns_the_winning_plan() -> None:
    session = MagicMock()
    session.flush.side_effect = IntegrityError(
        "INSERT INTO study_plans",
        {},
        Exception("unique plan date"),
    )
    repository = SqlAlchemyStudyPlanRepository(session)
    concurrent_plan = object()
    repository.get_for_date = Mock(  # type: ignore[method-assign]
        side_effect=[None, concurrent_plan]
    )
    proposal = StudyPlanProposal(
        user_key="learner",
        plan_date=date(2026, 10, 14),
        source="rule_based",
        generator_version="test",
        weakness_assessment_run_id=None,
        recommender_version="test",
        total_minutes=0,
        explanation=(),
        items=(),
    )

    result = repository.save(proposal)

    assert result is concurrent_plan
    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()
