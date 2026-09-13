from typing import Protocol

from app.domain.study_plan.entities import StudyPlanGenerationContext, StudyPlanProposal


class StudyPlanGenerator(Protocol):
    @property
    def generator_version(self) -> str: ...

    def generate(self, context: StudyPlanGenerationContext) -> StudyPlanProposal: ...
