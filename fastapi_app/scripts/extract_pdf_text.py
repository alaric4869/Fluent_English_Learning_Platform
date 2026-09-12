"""Extract a page range from a private scanned PDF into local OCR JSON.

This is an import aid, not an automatic publishing pipeline. OCR output must be
checked against the source before it is converted into a versioned practice set.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from rapidocr_onnxruntime import RapidOCR


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--last", type=int, required=True)
    parser.add_argument("--dpi", type=int, default=145)
    parser.add_argument("--pdftoppm", type=Path, required=True)
    return parser.parse_args()


def page_number(path: Path) -> int:
    return int(path.stem.rsplit("-", 1)[-1])


def main() -> None:
    arguments = parse_arguments()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    engine = RapidOCR()
    pages: list[dict[str, str | int]] = []

    with tempfile.TemporaryDirectory(prefix="ielts-import-") as temporary_directory:
        prefix = Path(temporary_directory) / "page"
        subprocess.run(
            [
                str(arguments.pdftoppm),
                "-f",
                str(arguments.first),
                "-l",
                str(arguments.last),
                "-jpeg",
                "-r",
                str(arguments.dpi),
                "-jpegopt",
                "quality=75",
                str(arguments.pdf),
                str(prefix),
            ],
            check=True,
        )
        images = sorted(Path(temporary_directory).glob("page-*.jpg"), key=page_number)
        for image in images:
            result, _ = engine(str(image))
            text = "\n".join(line[1] for line in result) if result else ""
            pages.append({"page": page_number(image), "text": text})

    arguments.output.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

