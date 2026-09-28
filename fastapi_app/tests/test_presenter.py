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


def test_reading_passages_and_answer_layouts_are_split_for_the_workspace() -> None:
    reading = _practice_set("reading")
    reading["sections"][0]["content_blocks"] = [
        {"kind": "passage", "title": "Source", "paragraphs": ["Read this."]},
        {
            "kind": "flowchart",
            "title": "Questions",
            "nodes": [{"parts": [{"text": "Answer "}, {"answer": 1}]}],
        },
    ]

    presented = present_practice_workspace(_workspace(reading))
    section = presented["practice_set"]["sections"][0]

    assert [block["kind"] for block in section["source_blocks"]] == ["passage"]
    assert [block["kind"] for block in section["question_blocks"]] == ["flowchart"]


def test_test_one_notes_keep_answers_inside_the_original_layout() -> None:
    listening = present_practice_workspace(_workspace(_practice_set("listening")))
    reading = present_practice_workspace(_workspace(_practice_set("reading")))

    listening_part_four = listening["practice_set"]["sections"][3]
    reading_section_two = reading["practice_set"]["sections"][1]

    assert listening_part_four["content_blocks"][0]["kind"] == "notes"
    assert listening_part_four["embedded_question_numbers"] == list(range(31, 41))
    assert listening_part_four["display_items"] == []
    assert [block["kind"] for block in reading_section_two["source_blocks"]] == [
        "passage",
        "passage",
    ]
    assert [block["kind"] for block in reading_section_two["question_blocks"]] == ["notes"]
    assert reading_section_two["embedded_question_numbers"] == list(range(22, 28))
    assert [item["numbers"] for item in reading_section_two["display_items"]] == [
        [15],
        [16],
        [17],
        [18],
        [19],
        [20],
        [21],
    ]


def _practice_set(skill: str) -> dict:
    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return next(item for item in payload["practice_sets"] if item["skill"] == skill)


def _workspace(practice_set: dict) -> dict:
    return {
        "practice_set": practice_set,
        "attempt": {"answers": {}, "results": [], "status": "in_progress", "score": None},
    }
