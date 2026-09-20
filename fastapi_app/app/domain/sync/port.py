from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol


SyncOperation = Literal["upsert", "delete"]


@dataclass(frozen=True, slots=True)
class SyncCursor:
    value: str | None = None


@dataclass(frozen=True, slots=True)
class SyncChange:
    entity_type: str
    entity_id: str
    operation: SyncOperation
    changed_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class SyncPage:
    changes: tuple[SyncChange, ...]
    next_cursor: SyncCursor


class LearningSyncPort(Protocol):
    """Boundary for a future authenticated cloud-sync adapter."""

    def list_changes(self, user_key: str, cursor: SyncCursor, limit: int) -> SyncPage: ...
