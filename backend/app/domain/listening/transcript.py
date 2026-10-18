import re


def split_transcript(transcript: str) -> tuple[str, ...]:
    """Return stable display sentences from learner-provided transcript text."""
    if not transcript.strip():
        return ()
    sentences: list[str] = []
    for paragraph in re.split(r"\n+", transcript.strip()):
        normalized = " ".join(paragraph.split())
        if not normalized:
            continue
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"“‘\'])', normalized)
        sentences.extend(part.strip() for part in parts if part.strip())
    return tuple(sentences)
