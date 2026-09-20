from copy import deepcopy


def present_practice_workspace(workspace: dict) -> dict:
    """Add display-only grouping without changing IELTS domain entities."""
    presented = deepcopy(workspace)
    practice_set = presented["practice_set"]
    question_map: dict[int, dict] = {}

    for section in practice_set["sections"]:
        _prepare_content_blocks(section["content_blocks"])
        question_map.update({question["number"]: question for question in section["questions"]})
        embedded_numbers = _embedded_question_numbers(section["content_blocks"])
        section["embedded_question_numbers"] = embedded_numbers
        section["display_items"] = _display_items(section["questions"], embedded_numbers)

    presented["question_map"] = question_map
    return presented


def _prepare_content_blocks(blocks: list[dict]) -> None:
    for block in blocks:
        if block.get("kind") != "figure":
            continue
        answer_numbers = {int(number) for number in block.get("answer_numbers", [])}
        answer_numbers.update(int(answer["number"]) for answer in block.get("answers", []))
        block["answer_numbers"] = sorted(answer_numbers)


def _embedded_question_numbers(blocks: list[dict]) -> list[int]:
    numbers: set[int] = set()
    for block in blocks:
        if block.get("kind") == "table":
            for row in block.get("rows", []):
                for cell in row.get("cells", []):
                    for part in cell:
                        if "answer" in part:
                            numbers.add(int(part["answer"]))
        if block.get("kind") == "figure":
            numbers.update(int(number) for number in block.get("answer_numbers", []))
            numbers.update(int(answer["number"]) for answer in block.get("answers", []))
        if block.get("kind") == "flowchart":
            for node in block.get("nodes", []):
                for part in node.get("parts", []):
                    if "answer" in part:
                        numbers.add(int(part["answer"]))
    return sorted(numbers)


def _display_items(questions: list[dict], embedded_numbers: list[int]) -> list[dict]:
    embedded = set(embedded_numbers)
    grouped: dict[str, list[dict]] = {}
    for question in questions:
        if question.get("answer_group"):
            grouped.setdefault(question["answer_group"], []).append(question)

    displayed_groups: set[str] = set()
    items: list[dict] = []
    for question in questions:
        if question["number"] in embedded:
            continue
        group_id = question.get("answer_group")
        if group_id:
            if group_id in displayed_groups:
                continue
            displayed_groups.add(group_id)
            members = grouped[group_id]
            items.append(
                {
                    "kind": "multiple_choice_group",
                    "numbers": [member["number"] for member in members],
                    "prompt": question["prompt"],
                    "options": question["options"],
                    "max_selections": len(members),
                }
            )
            continue
        items.append({"kind": "question", "numbers": [question["number"]], "question": question})
    return items
