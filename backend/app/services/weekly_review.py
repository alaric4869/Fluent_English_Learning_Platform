from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.domain.history.entities import HistoricalStudySession
from app.domain.history.repository import StudyHistoryRepository
from app.domain.learning_evidence.entities import Skill
from app.domain.listening.repository import ListeningSentenceRepository
from app.domain.review.repository import ReviewRepository
from app.domain.study_plan.entities import DailyStudyPlanItem, StudyPlanItemStatus
from app.domain.study_plan.repository import StudyPlanRepository
from app.domain.vocabulary.repository import VocabularyRepository
from app.domain.weekly_review.calculations import select_skill_highlights, week_range
from app.domain.weekly_review.entities import (
    WeeklyReview,
    WeeklyReviewRecommendation,
    WeeklySkillSummary,
)


class WeeklyReviewService:
    def __init__(
        self,
        study_plan_repository: StudyPlanRepository,
        history_repository: StudyHistoryRepository,
        vocabulary_repository: VocabularyRepository,
        listening_repository: ListeningSentenceRepository,
        review_repository: ReviewRepository,
        learner_timezone: ZoneInfo,
    ) -> None:
        self.study_plan_repository = study_plan_repository
        self.history_repository = history_repository
        self.vocabulary_repository = vocabulary_repository
        self.listening_repository = listening_repository
        self.review_repository = review_repository
        self.learner_timezone = learner_timezone

    def get_current_week(self, user_key: str, today: date) -> WeeklyReview:
        week_start, next_week_start = week_range(today)
        next_week_end = next_week_start + timedelta(days=7)
        data_end = min(next_week_start, today + timedelta(days=1))
        plans = self.study_plan_repository.list_between(
            user_key, week_start, data_end
        )
        start_boundary = self._day_boundary(week_start)
        end_boundary = self._day_boundary(data_end)
        sessions = self.history_repository.list_sessions_between(
            user_key, start_boundary, end_boundary
        )
        completed_items = tuple(
            item
            for plan in plans
            for item in plan.items
            if item.status is StudyPlanItemStatus.COMPLETED
        )
        assigned_modules = sum(len(plan.items) for plan in plans)
        skill_summaries = tuple(
            self._summarize_skill(skill, completed_items, sessions) for skill in Skill
        )
        strongest_skill, weakest_skill = select_skill_highlights(skill_summaries)
        review_attempts = self.review_repository.summarize_attempts_between(
            user_key, start_boundary, end_boundary
        )
        next_week_review_count = self.review_repository.count_active_scheduled_between(
            user_key, next_week_start, next_week_end
        )
        study_dates = {
            plan.plan_date
            for plan in plans
            if any(
                item.status is StudyPlanItemStatus.COMPLETED for item in plan.items
            )
        }
        study_dates.update(
            self._as_local_date(session.completed_at) for session in sessions
        )
        recommendations = self._build_recommendations(
            sessions=sessions,
            summaries=skill_summaries,
            weakest_skill=weakest_skill,
            next_week_review_count=next_week_review_count,
            retention_rate=review_attempts.retention_rate,
            review_count=review_attempts.total_count,
        )
        return WeeklyReview(
            week_start=week_start,
            week_end=next_week_start - timedelta(days=1),
            study_days=len(study_dates),
            assigned_modules=assigned_modules,
            completed_modules=len(completed_items),
            completion_rate=(
                round(len(completed_items) / assigned_modules * 100, 1)
                if assigned_modules
                else 0.0
            ),
            completed_planned_minutes=sum(
                item.planned_minutes for item in completed_items
            ),
            completed_sessions=len(sessions),
            tracked_seconds=sum(
                session.actual_duration_seconds or 0 for session in sessions
            ),
            vocabulary_learned=self.vocabulary_repository.count_learned_between(
                user_key, week_start, data_end
            ),
            difficult_sentences_collected=(
                self.listening_repository.count_learned_between(
                    user_key, week_start, data_end
                )
            ),
            review_attempts=review_attempts,
            next_week_review_count=next_week_review_count,
            strongest_skill=strongest_skill,
            weakest_skill=weakest_skill,
            skill_summaries=skill_summaries,
            recommendations=recommendations,
        )

    @staticmethod
    def _summarize_skill(
        skill: Skill,
        completed_items: tuple[DailyStudyPlanItem, ...],
        sessions: tuple[HistoricalStudySession, ...],
    ) -> WeeklySkillSummary:
        matching_sessions = tuple(item for item in sessions if item.skill is skill)
        measured_sessions = tuple(
            item for item in matching_sessions if item.accuracy is not None
        )
        return WeeklySkillSummary(
            skill=skill,
            completed_modules=sum(item.skill is skill for item in completed_items),
            completed_sessions=len(matching_sessions),
            average_accuracy=(
                round(
                    sum(
                        item.accuracy
                        for item in measured_sessions
                        if item.accuracy is not None
                    )
                    / len(measured_sessions),
                    4,
                )
                if measured_sessions
                else None
            ),
            incorrect_item_count=sum(
                item.incorrect_item_count for item in matching_sessions
            ),
            tracked_seconds=sum(
                item.actual_duration_seconds or 0 for item in matching_sessions
            ),
        )

    @staticmethod
    def _build_recommendations(
        *,
        sessions: tuple[HistoricalStudySession, ...],
        summaries: tuple[WeeklySkillSummary, ...],
        weakest_skill: Skill | None,
        next_week_review_count: int,
        retention_rate: float | None,
        review_count: int,
    ) -> tuple[WeeklyReviewRecommendation, ...]:
        recommendations: list[WeeklyReviewRecommendation] = []
        if next_week_review_count:
            recommendations.append(
                WeeklyReviewRecommendation(
                    title=f"完成 {next_week_review_count} 项排期复习",
                    reason="这些内容已经进入下周的间隔复习队列。",
                    href="/review",
                )
            )
        if weakest_skill is not None:
            summary = next(item for item in summaries if item.skill is weakest_skill)
            recommendations.append(
                WeeklyReviewRecommendation(
                    title=f"优先加强 {weakest_skill.value.title()}",
                    reason=(
                        f"本周 {summary.completed_sessions} 次真实作答平均准确率 "
                        f"{round((summary.average_accuracy or 0) * 100)}%。"
                    ),
                    href="/today",
                )
            )
        seen_resources: set[int] = set()
        measured_sessions = tuple(
            item for item in sessions if item.accuracy is not None
        )
        for session in sorted(
            measured_sessions,
            key=lambda item: (
                item.accuracy if item.accuracy is not None else 1.0,
                -item.incorrect_item_count,
            ),
        ):
            if session.incorrect_item_count == 0 or session.resource_id in seen_resources:
                continue
            recommendations.append(
                WeeklyReviewRecommendation(
                    title=f"重做：{session.resource_title}",
                    reason=(
                        f"上次正确率 {round((session.accuracy or 0) * 100)}%，"
                        f"共 {session.incorrect_item_count} 处错误。"
                    ),
                    href=f"/library/{session.resource_id}",
                )
            )
            seen_resources.add(session.resource_id)
            if len(seen_resources) == 2:
                break
        if review_count >= 3 and retention_rate is not None and retention_rate < 70:
            recommendations.append(
                WeeklyReviewRecommendation(
                    title="减少新词块，先巩固旧内容",
                    reason=f"本周 Good / Easy 占比为 {retention_rate}%。",
                    href="/review",
                )
            )
        if not recommendations:
            recommendations.append(
                WeeklyReviewRecommendation(
                    title="继续完成每日四模块",
                    reason="本周还没有足够的错题或复习证据生成专项建议。",
                    href="/today",
                )
            )
        return tuple(recommendations)

    def _day_boundary(self, value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=self.learner_timezone).astimezone(
            timezone.utc
        )

    def _as_local_date(self, value: datetime) -> date:
        aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return aware.astimezone(self.learner_timezone).date()
