from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.content_import.schemas import SeedManifest, SeedPayload


class SeedImportError(ValueError):
    pass


def load_seed_payloads(seed_path: Path) -> list[dict]:
    """Load and validate either one seed payload or an ordered seed manifest."""
    seed_path = seed_path.resolve()
    raw = _read_json(seed_path)
    if "imports" not in raw:
        return [_validate_payload(raw, seed_path)]

    try:
        manifest = SeedManifest.model_validate(raw)
    except ValidationError as error:
        raise SeedImportError(f"Invalid seed manifest {seed_path}: {error}") from error

    payloads: list[dict] = []
    seen_slugs: set[str] = set()
    for relative_path in manifest.imports:
        import_path = (seed_path.parent / relative_path).resolve()
        if seed_path.parent not in import_path.parents:
            raise SeedImportError(f"Seed import escapes its manifest directory: {relative_path}")
        payload = _validate_payload(_read_json(import_path), import_path)
        slugs = {
            item["slug"]
            for collection in (payload["practice_sets"], payload["learning_resources"])
            for item in collection
        }
        duplicates = seen_slugs & slugs
        if duplicates:
            raise SeedImportError(
                f"Duplicate slugs across seed files: {', '.join(sorted(duplicates))}"
            )
        seen_slugs.update(slugs)
        payloads.append(payload)
    return payloads


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SeedImportError(f"Unable to read seed JSON {path}: {error}") from error
    if not isinstance(payload, dict):
        raise SeedImportError(f"Seed JSON must contain an object: {path}")
    return payload


def _validate_payload(payload: dict, path: Path) -> dict:
    try:
        validated = SeedPayload.model_validate(payload)
    except ValidationError as error:
        raise SeedImportError(f"Invalid seed content {path}: {error}") from error
    return validated.model_dump(exclude_none=True)
