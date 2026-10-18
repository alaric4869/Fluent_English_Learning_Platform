from fastapi import APIRouter, Depends, HTTPException

from app.api.frontend_dependencies import get_frontend_services
from app.api.learner_context import Learner
from app.composition import ApplicationServices
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import ResourceLibraryFilters, ResourceSort
from app.presenters.ielts import present_practice_workspace
from app.schemas.frontend_ielts import (
    IeltsCatalogResponse,
    IeltsModuleSummaryResponse,
    IeltsPracticeWorkspaceResponse,
)
from app.schemas.ielts import SaveAnswerRequest, SavedAnswerResponse, SubmitAttemptResponse
from app.services.ielts_practice import IncompleteAttemptError, PracticeSetNotFoundError


router = APIRouter(prefix="/api/v1/ielts", tags=["frontend-ielts"])


@router.get("", response_model=IeltsCatalogResponse)
def get_ielts_catalog(
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> IeltsCatalogResponse:
    modules = [_practice_summary(item) for item in services.ielts_practice.list_practice_sets()]
    for skill, resource_type in (
        (Skill.SPEAKING, "shadowing_retelling"),
        (Skill.WRITING, "ielts_writing"),
    ):
        library = services.resources.get_library(
            learner.user_key,
            ResourceLibraryFilters(
                skill=skill,
                resource_type=resource_type,
                sort=ResourceSort.PRIORITY,
            ),
        )
        modules.extend(_resource_summary(item) for item in library.items)
    modules.sort(key=lambda item: (item.test_number, _skill_order(item.skill), item.title))
    return IeltsCatalogResponse(
        target_band="6.5",
        exam_timing="预计 10 月底",
        module_count=len(modules),
        modules=modules,
    )


@router.get("/{slug}", response_model=IeltsPracticeWorkspaceResponse)
def get_ielts_workspace(
    slug: str,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> IeltsPracticeWorkspaceResponse:
    try:
        workspace = services.ielts_practice.get_practice_workspace(slug, learner.user_key)
    except PracticeSetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Practice set not found") from error

    presented = present_practice_workspace(workspace)
    practice_set = presented["practice_set"]
    sections = []
    for section in practice_set["sections"]:
        sections.append(
            {
                "id": section["id"],
                "order_index": section["order_index"],
                "title": section["title"],
                "instructions": section["instructions"],
                "has_audio": section["has_audio"],
                "audio_url": (
                    f"/media/audio/{practice_set['slug']}/{section['order_index']}"
                    if section["has_audio"]
                    else None
                ),
                "content_blocks": section["content_blocks"],
                "source_blocks": section["source_blocks"],
                "question_blocks": section["question_blocks"],
                "embedded_question_numbers": section["embedded_question_numbers"],
                "questions": [
                    {
                        "number": question["number"],
                        "prompt": question["prompt"],
                        "question_type": question["question_type"],
                        "options": question["options"],
                        "answer_group": question.get("answer_group"),
                    }
                    for question in section["questions"]
                ],
            }
        )
    return IeltsPracticeWorkspaceResponse(
        slug=practice_set["slug"],
        book_number=practice_set["book_number"],
        test_number=practice_set["test_number"],
        skill=practice_set["skill"],
        title=practice_set["title"],
        description=practice_set["description"],
        duration_minutes=practice_set["duration_minutes"],
        question_count=sum(len(section["questions"]) for section in practice_set["sections"]),
        sections=sections,
        attempt=presented["attempt"],
    )


@router.put(
    "/{slug}/answers/{question_number}",
    response_model=SavedAnswerResponse,
)
def save_ielts_answer(
    slug: str,
    question_number: int,
    payload: SaveAnswerRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> dict:
    try:
        return services.ielts_practice.save_answer(
            slug,
            learner.user_key,
            question_number,
            payload.answer,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{slug}/submit", response_model=SubmitAttemptResponse)
def submit_ielts_attempt(
    slug: str,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> dict:
    try:
        return services.ielts_practice.submit(slug, learner.user_key)
    except IncompleteAttemptError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "请先完成全部题目再提交。",
                "missing_questions": list(error.missing_questions),
            },
        ) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def _practice_summary(item: dict) -> IeltsModuleSummaryResponse:
    skill = item["skill"]
    return IeltsModuleSummaryResponse(
        key=item["slug"],
        title="听力 Listening" if skill == "listening" else "阅读 Reading",
        description=item["description"],
        skill=skill,
        test_number=item["test_number"],
        duration_minutes=item["duration_minutes"],
        question_count=40,
        section_count=len(item["sections"]),
        detail_label="Interactive",
        workspace_href=f"/ielts/{item['slug']}",
        migrated=True,
    )


def _resource_summary(resource) -> IeltsModuleSummaryResponse:
    content = resource.content
    test_number = int(content.get("test_number", 1))
    if resource.skill is Skill.SPEAKING:
        practice = content.get("speaking_practice", {})
        detail_label = f"{len(practice.get('sentences', []))} sentences"
    else:
        task = content.get("writing_task", {})
        detail_label = f"{task.get('minimum_words', '—')} words"
    return IeltsModuleSummaryResponse(
        key=f"resource-{resource.id}",
        title=(
            "跟读与复述 Speaking"
            if resource.skill is Skill.SPEAKING
            else content.get("writing_task", {}).get("task_type", "写作 Writing")
        ),
        description=resource.description,
        skill=resource.skill.value,
        test_number=test_number,
        duration_minutes=resource.estimated_duration_minutes,
        detail_label=detail_label,
        workspace_href=f"/{resource.skill.value}/{resource.id}",
        migrated=True,
    )


def _skill_order(skill: str) -> int:
    return {"listening": 0, "reading": 1, "writing": 2, "speaking": 3}[skill]
