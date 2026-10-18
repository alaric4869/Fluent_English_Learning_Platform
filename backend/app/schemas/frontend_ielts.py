from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.schemas.ielts import QuestionResultResponse


class IeltsModuleSummaryResponse(BaseModel):
    key: str
    title: str
    description: str
    skill: Literal["listening", "reading", "speaking", "writing"]
    test_number: int
    duration_minutes: int
    question_count: int | None = None
    section_count: int | None = None
    detail_label: str
    workspace_href: str
    migrated: bool


class IeltsCatalogResponse(BaseModel):
    target_band: str
    exam_timing: str
    module_count: int
    modules: list[IeltsModuleSummaryResponse]


class IeltsQuestionOptionResponse(BaseModel):
    key: str
    text: str


class IeltsQuestionResponse(BaseModel):
    number: int
    prompt: str
    question_type: Literal["text", "single_choice", "true_false_not_given"]
    options: list[IeltsQuestionOptionResponse]
    answer_group: str | None = None


class ContentPartResponse(BaseModel):
    text: str | None = None
    answer: int | None = None


class TableRowResponse(BaseModel):
    cells: list[list[ContentPartResponse]]


class TableBlockResponse(BaseModel):
    kind: Literal["table"]
    title: str = ""
    headers: list[str]
    rows: list[TableRowResponse]


class PassageBlockResponse(BaseModel):
    kind: Literal["passage", "notice", "text"]
    title: str = ""
    paragraphs: list[str] = Field(default_factory=list)


class FigureBlockResponse(BaseModel):
    kind: Literal["figure"]
    title: str = ""
    asset_path: str
    alt: str = ""
    caption: str = ""
    answer_numbers: list[int] = Field(default_factory=list)


class FlowchartNodeResponse(BaseModel):
    parts: list[ContentPartResponse]


class FlowchartBlockResponse(BaseModel):
    kind: Literal["flowchart"]
    title: str = ""
    nodes: list[FlowchartNodeResponse]


class NotesItemResponse(BaseModel):
    level: int = 0
    parts: list[ContentPartResponse]


class NotesSectionResponse(BaseModel):
    heading: str
    items: list[NotesItemResponse]


class NotesBlockResponse(BaseModel):
    kind: Literal["notes"]
    title: str = ""
    lead: list[ContentPartResponse] = Field(default_factory=list)
    sections: list[NotesSectionResponse]


IeltsContentBlockResponse = Annotated[
    TableBlockResponse
    | PassageBlockResponse
    | FigureBlockResponse
    | FlowchartBlockResponse
    | NotesBlockResponse,
    Field(discriminator="kind"),
]


class IeltsSectionResponse(BaseModel):
    id: int
    order_index: int
    title: str
    instructions: str
    has_audio: bool
    audio_url: str | None
    content_blocks: list[IeltsContentBlockResponse]
    source_blocks: list[IeltsContentBlockResponse]
    question_blocks: list[IeltsContentBlockResponse]
    embedded_question_numbers: list[int]
    questions: list[IeltsQuestionResponse]


class IeltsAttemptResponse(BaseModel):
    id: int
    status: str
    answers: dict[str, str]
    results: list[QuestionResultResponse]
    score: int | None
    submission_revision: int
    started_at: datetime
    updated_at: datetime
    submitted_at: datetime | None


class IeltsPracticeWorkspaceResponse(BaseModel):
    slug: str
    book_number: int
    test_number: int
    skill: Literal["listening", "reading"]
    title: str
    description: str
    duration_minutes: int
    question_count: int
    sections: list[IeltsSectionResponse]
    attempt: IeltsAttemptResponse
