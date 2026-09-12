import json
from pathlib import Path

from app.presenters.ielts import present_practice_workspace


SEED_PATH = Path(__file__).parents[1] / "seed" / "g20_test1.json"


def test_table_answers_are_embedded_in_the_original_layout() -> None:
    listening = _practice_set("listening")
    presented = present_practice_workspace(_workspace(listening))
    part_one = presented["practice_set"]["sections"][0]

    assert part_one["embedded_question_numbers"] == list(range(1, 11))
    assert part_one["display_items"] == []
    assert part_one["content_blocks"][0]["kind"] == "table"
    assert len(part_one["content_blocks"][0]["headers"]) == 4


def test_grouped_questions_render_as_one_two_selection_exercise() -> None:
    listening = _practice_set("listening")
    presented = present_practice_workspace(_workspace(listening))
    part_two = presented["practice_set"]["sections"][1]
    groups = [item for item in part_two["display_items"] if item["kind"] == "multiple_choice_group"]

    assert [group["numbers"] for group in groups] == [[17, 18], [19, 20]]
    assert all(group["max_selections"] == 2 for group in groups)


def test_figure_answer_metadata_is_normalized_for_the_renderer() -> None:
    practice_set = _practice_set("listening")
    practice_set["sections"][0]["content_blocks"] = [
        {
            "kind": "figure",
            "asset_path": "map.png",
            "answers": [{"number": 1, "x": 20, "y": 40}],
        }
    ]
    presented = present_practice_workspace(_workspace(practice_set))
    block = presented["practice_set"]["sections"][0]["content_blocks"][0]

    assert block["answer_numbers"] == [1]
    assert presented["practice_set"]["sections"][0]["embedded_question_numbers"] == [1]


def _practice_set(skill: str) -> dict:
    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return next(item for item in payload["practice_sets"] if item["skill"] == skill)


def _workspace(practice_set: dict) -> dict:
    return {
        "practice_set": practice_set,
        "attempt": {"answers": {}, "results": [], "status": "in_progress", "score": None},
    }
