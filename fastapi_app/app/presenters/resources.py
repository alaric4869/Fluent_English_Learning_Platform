from urllib.parse import urlparse

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import (
    CompletionFilter,
    LearningResourceDetails,
    ResourceLibrary,
    ResourceLibraryFacets,
    ResourceLibraryFilters,
    ResourceSort,
)


SKILL_LABELS = {
    Skill.LISTENING: "听力 Listening",
    Skill.SPEAKING: "口语 Speaking",
    Skill.READING: "阅读 Reading",
    Skill.WRITING: "写作 Writing",
    Skill.VOCABULARY: "词块 Vocabulary",
}
COMPLETION_LABELS = {
    CompletionFilter.ALL: "全部进度",
    CompletionFilter.COMPLETED: "已学习",
    CompletionFilter.NOT_COMPLETED: "未学习",
}
SORT_LABELS = {
    ResourceSort.RECENTLY_ADDED: "最近添加",
    ResourceSort.RECENTLY_STUDIED: "最近学习",
    ResourceSort.TITLE: "标题 A–Z",
    ResourceSort.PRIORITY: "优先级",
}
CREATE_TYPE_OPTIONS = (
    ("video", "Video / YouTube"),
    ("audio", "Audio"),
    ("podcast", "Podcast"),
    ("article", "Article"),
    ("exercise", "Online Exercise"),
    ("pronunciation", "Pronunciation"),
    ("grammar", "Grammar"),
    ("ielts", "IELTS"),
    ("ielts_writing", "IELTS Writing"),
    ("pte", "PTE"),
    ("other", "Other"),
)


def present_library_page(
    *,
    library: ResourceLibrary,
    facets: ResourceLibraryFacets,
    filters: ResourceLibraryFilters,
    view: str,
    counts: dict[str, int],
    open_add_resource: bool = False,
) -> dict:
    return {
        "active_page": "library",
        "view": view,
        "items": tuple(_present_card(item) for item in library.items),
        "result_count": library.total_count,
        "counts": counts,
        "search": filters.search,
        "selected_skill": filters.skill.value if filters.skill else "",
        "selected_type": filters.resource_type,
        "selected_topic": filters.topic,
        "selected_difficulty": filters.difficulty,
        "selected_completion": filters.completion.value,
        "selected_sort": filters.sort.value,
        "skill_options": tuple((value.value, label) for value, label in SKILL_LABELS.items()),
        "type_options": tuple((value, _display_type(value)) for value in facets.resource_types),
        "topic_options": facets.topics,
        "difficulty_options": facets.difficulties,
        "completion_options": tuple(
            (value.value, label) for value, label in COMPLETION_LABELS.items()
        ),
        "sort_options": tuple((value.value, label) for value, label in SORT_LABELS.items()),
        "create_type_options": CREATE_TYPE_OPTIONS,
        "open_add_resource": open_add_resource,
    }


def present_resource_detail(resource: LearningResourceDetails) -> dict:
    return {
        "active_page": "library",
        "resource": resource,
        "skill_label": SKILL_LABELS[resource.skill],
        "type_label": _display_type(resource.resource_type),
        "start_href": _start_href(resource),
        "listening_href": f"/listening/{resource.id}"
        if resource.skill is Skill.LISTENING
        else None,
        "skill_options": tuple((value.value, label) for value, label in SKILL_LABELS.items()),
    }


def present_resource_response(resource: LearningResourceDetails) -> dict:
    return {
        "id": resource.id,
        "title": resource.title,
        "resource_type": resource.resource_type,
        "skill": resource.skill,
        "topic": resource.topic,
        "difficulty": resource.difficulty,
        "estimated_duration_minutes": resource.estimated_duration_minutes,
        "source_url": resource.source_url,
        "description": resource.description,
        "content_text": resource.content_text,
        "transcript": resource.transcript,
        "notes": resource.notes,
        "tags": list(resource.tags),
        "priority": resource.priority,
        "favorite": resource.favorite,
        "saved_for_later": resource.saved_for_later,
        "archived": resource.archived,
        "is_user_owned": resource.is_user_owned,
        "last_studied_at": resource.last_studied_at,
        "completed_session_count": resource.completed_session_count,
    }


def _present_card(resource: LearningResourceDetails) -> dict:
    return {
        "resource": resource,
        "skill_label": SKILL_LABELS[resource.skill],
        "type_label": _display_type(resource.resource_type),
        "last_studied_label": (
            resource.last_studied_at.date().isoformat()
            if resource.last_studied_at
            else "尚未学习"
        ),
    }


def _display_type(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _start_href(resource: LearningResourceDetails) -> str | None:
    if resource.skill is Skill.LISTENING:
        return f"/listening/{resource.id}"
    if resource.skill is Skill.WRITING:
        return f"/writing/{resource.id}"
    practice_slug = resource.content.get("practice_set_slug")
    if isinstance(practice_slug, str) and practice_slug:
        return f"/ielts/{practice_slug}"
    if resource.source_url and urlparse(resource.source_url).scheme in {"http", "https"}:
        return resource.source_url
    return None
