from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


IELTS_PRACTICE_SLUG = re.compile(r"^g\d+-test-\d+-(listening|reading)$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionOptionSeed(StrictModel):
    key: str = Field(min_length=1, max_length=12)
    text: str = Field(min_length=1)


class PracticeQuestionSeed(StrictModel):
    number: int = Field(ge=1)
    prompt: str = Field(min_length=1)
    question_type: Literal["text", "single_choice", "true_false_not_given"]
    options: list[QuestionOptionSeed] = Field(default_factory=list)
    accepted_answers: list[str] = Field(min_length=1)
    answer_group: str | None = Field(default=None, max_length=80)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_answers_and_options(self) -> PracticeQuestionSeed:
        if any(not answer.strip() for answer in self.accepted_answers):
            raise ValueError("accepted answers cannot be blank")
        option_keys = [option.key for option in self.options]
        if len(option_keys) != len(set(option_keys)):
            raise ValueError("option keys must be unique")
        if self.question_type != "text":
            if not self.options:
                raise ValueError("choice questions require options")
            valid_keys = set(option_keys)
            if any(answer not in valid_keys for answer in self.accepted_answers):
                raise ValueError("accepted choice answers must reference option keys")
        return self


class PracticeSectionSeed(StrictModel):
    order_index: int = Field(ge=1)
    title: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    content_blocks: list[dict[str, Any]] = Field(default_factory=list)
    audio_path: str | None = None
    questions: list[PracticeQuestionSeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_content_blocks(self) -> PracticeSectionSeed:
        question_numbers = {question.number for question in self.questions}
        for block in self.content_blocks:
            kind = block.get("kind")
            if kind not in {
                "text",
                "notice",
                "passage",
                "table",
                "flowchart",
                "notes",
                "figure",
            }:
                raise ValueError(f"unsupported content block kind: {kind!r}")
            embedded = _embedded_question_numbers(block)
            missing = embedded - question_numbers
            if missing:
                raise ValueError(
                    f"content block references questions outside its section: {sorted(missing)}"
                )
            if kind == "figure" and not block.get("asset_path"):
                raise ValueError("figure blocks require asset_path")
            if kind == "table":
                _validate_table_shape(block)
            if kind == "flowchart":
                _validate_flowchart_shape(block)
            if kind == "notes":
                _validate_notes_shape(block)
        return self


class PracticeSetSeed(StrictModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=120)
    book_number: int = Field(ge=1)
    test_number: int = Field(ge=1)
    skill: Literal["listening", "reading"]
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    duration_minutes: int = Field(gt=0)
    content_version: str = Field(min_length=1, max_length=40)
    resource_type: str | None = None
    topic: str | None = None
    difficulty: str | None = None
    source_url: str | None = None
    local_asset_reference: str | None = None
    tags: list[str] | None = None
    priority: int | None = None
    sections: list[PracticeSectionSeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_practice_structure(self) -> PracticeSetSeed:
        orders = [section.order_index for section in self.sections]
        if orders != list(range(1, len(orders) + 1)):
            raise ValueError("section order_index values must be sequential and ordered")

        questions = [question for section in self.sections for question in section.questions]
        numbers = [question.number for question in questions]
        if len(numbers) != len(set(numbers)):
            raise ValueError("question numbers must be unique within a practice set")
        if numbers != sorted(numbers):
            raise ValueError("questions must be ordered by number")

        if IELTS_PRACTICE_SLUG.fullmatch(self.slug):
            expected_sections = 4 if self.skill == "listening" else 3
            if len(self.sections) != expected_sections:
                raise ValueError(f"IELTS {self.skill} sets require {expected_sections} sections")
            if numbers != list(range(1, 41)):
                raise ValueError("IELTS objective practice sets require questions 1 through 40")

        groups: dict[str, list[PracticeQuestionSeed]] = defaultdict(list)
        for question in questions:
            if question.answer_group:
                groups[question.answer_group].append(question)
        for group_id, members in groups.items():
            if len(members) < 2:
                raise ValueError(f"answer group {group_id!r} requires at least two questions")
            option_sets = [[option.model_dump() for option in item.options] for item in members]
            if any(options != option_sets[0] for options in option_sets[1:]):
                raise ValueError(f"answer group {group_id!r} must use identical options")
            answers = [item.accepted_answers[0] for item in members]
            if len(answers) != len(set(answers)):
                raise ValueError(f"answer group {group_id!r} requires distinct correct options")
        return self


class LearningResourceSeed(StrictModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=120)
    title: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    skill: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    difficulty: str | None = None
    estimated_duration_minutes: int = Field(gt=0)
    source_url: str | None = None
    local_asset_reference: str | None = None
    content: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    priority: int = 50
    active: bool = True
    description: str = ""
    content_text: str = ""
    transcript: str = ""
    notes: str = ""


class SeedPayload(StrictModel):
    practice_sets: list[PracticeSetSeed] = Field(default_factory=list)
    learning_resources: list[LearningResourceSeed] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_slugs(self) -> SeedPayload:
        slugs = [item.slug for item in self.practice_sets]
        slugs.extend(item.slug for item in self.learning_resources)
        if len(slugs) != len(set(slugs)):
            raise ValueError("resource slugs must be unique within one seed file")
        return self


class SeedManifest(StrictModel):
    schema_version: Literal[1]
    imports: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_imports(self) -> SeedManifest:
        if len(self.imports) != len(set(self.imports)):
            raise ValueError("manifest imports must be unique")
        for item in self.imports:
            path = PathLike(item)
            if path.is_absolute or path.escapes_parent or path.suffix != ".json":
                raise ValueError(f"unsafe manifest import path: {item!r}")
        return self


class PathLike:
    """Small path validator that does not touch the filesystem."""

    def __init__(self, value: str) -> None:
        from pathlib import PurePosixPath

        path = PurePosixPath(value)
        self.is_absolute = path.is_absolute()
        self.escapes_parent = ".." in path.parts
        self.suffix = path.suffix


def _embedded_question_numbers(block: dict[str, Any]) -> set[int]:
    numbers = {int(value) for value in block.get("answer_numbers", [])}
    numbers.update(int(item["number"]) for item in block.get("answers", []))
    if block.get("kind") == "table":
        for row in block.get("rows", []):
            for cell in row.get("cells", []):
                for part in cell:
                    if "answer" in part:
                        numbers.add(int(part["answer"]))
    if block.get("kind") == "flowchart":
        for node in block.get("nodes", []):
            for part in node.get("parts", []):
                if "answer" in part:
                    numbers.add(int(part["answer"]))
    if block.get("kind") == "notes":
        for part in block.get("lead", []):
            if "answer" in part:
                numbers.add(int(part["answer"]))
        for section in block.get("sections", []):
            for item in section.get("items", []):
                for part in item.get("parts", []):
                    if "answer" in part:
                        numbers.add(int(part["answer"]))
    return numbers


def _validate_table_shape(block: dict[str, Any]) -> None:
    headers = block.get("headers")
    rows = block.get("rows")
    if not isinstance(headers, list) or not headers:
        raise ValueError("table blocks require headers")
    if not isinstance(rows, list) or not rows:
        raise ValueError("table blocks require rows")
    for row in rows:
        cells = row.get("cells") if isinstance(row, dict) else None
        if not isinstance(cells, list) or len(cells) != len(headers):
            raise ValueError("every table row must have one cell per header")


def _validate_flowchart_shape(block: dict[str, Any]) -> None:
    nodes = block.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("flowchart blocks require nodes")
    for node in nodes:
        parts = node.get("parts") if isinstance(node, dict) else None
        if not isinstance(parts, list) or not parts:
            raise ValueError("every flowchart node requires parts")


def _validate_notes_shape(block: dict[str, Any]) -> None:
    sections = block.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("notes blocks require sections")
    for section in sections:
        if not isinstance(section, dict) or not str(section.get("heading", "")).strip():
            raise ValueError("every notes section requires a heading")
        items = section.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("every notes section requires items")
        for item in items:
            parts = item.get("parts") if isinstance(item, dict) else None
            if not isinstance(parts, list) or not parts:
                raise ValueError("every notes item requires parts")
            if item.get("level", 0) not in {0, 1}:
                raise ValueError("notes item level must be 0 or 1")
