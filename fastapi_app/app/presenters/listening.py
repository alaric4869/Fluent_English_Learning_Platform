import re
from urllib.parse import parse_qs, urlparse

from app.domain.listening.entities import SavedListeningSentence
from app.domain.listening.transcript import split_transcript
from app.domain.resources.entities import LearningResourceDetails


def present_listening_workspace(
    resource: LearningResourceDetails,
    saved_sentences: tuple[SavedListeningSentence, ...],
) -> dict:
    saved_by_sentence = {item.sentence: item for item in saved_sentences}
    transcript_sentences = split_transcript(resource.transcript)
    practice_slug = resource.content.get("practice_set_slug")
    local_audio_parts = (
        tuple(
            {
                "number": number,
                "label": f"Part {number}",
                "url": f"/media/audio/{practice_slug}/{number}",
            }
            for number in range(1, 5)
        )
        if isinstance(practice_slug, str)
        and practice_slug
        and resource.skill.value == "listening"
        else ()
    )
    youtube_embed_url = _youtube_embed_url(resource.source_url)
    direct_audio_url = _direct_audio_url(resource.source_url)
    return {
        "active_page": "today",
        "resource": resource,
        "sentences": tuple(
            {
                "position": position,
                "text": sentence,
                "saved": saved_by_sentence.get(sentence),
                "status": (
                    saved_by_sentence[sentence].practice_status.value
                    if sentence in saved_by_sentence
                    else ""
                ),
            }
            for position, sentence in enumerate(transcript_sentences, start=1)
        ),
        "local_audio_parts": local_audio_parts,
        "youtube_embed_url": youtube_embed_url,
        "direct_audio_url": direct_audio_url,
        "external_url": (
            resource.source_url
            if resource.source_url and not youtube_embed_url and not direct_audio_url
            else None
        ),
        "practice_href": f"/ielts/{practice_slug}"
        if isinstance(practice_slug, str) and practice_slug
        else None,
    }


def _youtube_embed_url(source_url: str | None) -> str | None:
    if not source_url:
        return None
    parsed = urlparse(source_url)
    host = parsed.netloc.casefold().removeprefix("www.")
    video_id = ""
    if host in {"youtube.com", "m.youtube.com"} and parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "m.youtube.com"} and parsed.path.startswith("/embed/"):
        video_id = parsed.path.split("/embed/", 1)[1].split("/", 1)[0]
    elif host in {"youtube.com", "m.youtube.com"} and parsed.path.startswith(
        ("/shorts/", "/live/")
    ):
        video_id = parsed.path.strip("/").split("/", 1)[1].split("/", 1)[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id):
        return None
    return f"https://www.youtube-nocookie.com/embed/{video_id}"


def _direct_audio_url(source_url: str | None) -> str | None:
    if not source_url:
        return None
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"}:
        return None
    return source_url if parsed.path.casefold().endswith((".mp3", ".m4a", ".wav", ".ogg")) else None
