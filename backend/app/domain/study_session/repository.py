from typing import Protocol

from app.domain.study_session.entities import (
    ModuleStudySession,
    SaveModuleSessionCommand,
    StartModuleSessionCommand,
)


class StudySessionRepository(Protocol):
    def get_latest_for_plan_items(
        self,
        user_key: str,
        study_plan_item_ids: tuple[int, ...],
    ) -> dict[int, ModuleStudySession]: ...

    def start(self, command: StartModuleSessionCommand) -> ModuleStudySession: ...

    def save_progress(
        self, command: SaveModuleSessionCommand
    ) -> ModuleStudySession: ...

    def complete(self, command: SaveModuleSessionCommand) -> ModuleStudySession: ...
