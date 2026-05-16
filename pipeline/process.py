import json
import tempfile
from pathlib import Path

import httpx

from .transcribe import transcribe
from .translate import translate_segments


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EPISODES_DIR = DATA_DIR / "episodes"
INDEX_PATH = DATA_DIR / "index.json"


_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def download_audio(url):
    print("  downloading audio")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    try:
        with httpx.stream(
            "GET", url,
            follow_redirects=True,
            timeout=120.0,
            headers={"User-Agent": _UA},
        ) as r:
            r.raise_for_status()
            for chunk in r.iter_bytes():
                tmp.write(chunk)
    finally:
        tmp.close()
    return tmp.name


def process_episode(*, episode_id, title, audio_url, published, language="es"):
    print(f"processing {episode_id}: {title}")
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)

    audio_path = download_audio(audio_url)
    try:
        print("  transcribing")
        segments, duration = transcribe(audio_path)
        print(f"  got {len(segments)} segments ({duration:.1f}s)")

        print("  translating")
        translations = translate_segments(segments)
    finally:
        Path(audio_path).unlink(missing_ok=True)

    transcript = {
        "id": episode_id,
        "title": title,
        "published": published,
        "audio_url": audio_url,
        "duration_seconds": duration,
        "language": language,
        "segments": [
            {
                "id": s["id"],
                "start": s["start"],
                "end": s["end"],
                "es": s["text"],
                "en": translations[s["id"]],
            }
            for s in segments
        ],
    }

    out_path = EPISODES_DIR / f"{episode_id}.json"
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2))
    print(f"  wrote {out_path}")

    _update_index(episode_id, title, published)


def _update_index(episode_id, title, published):
    if INDEX_PATH.exists():
        index = json.loads(INDEX_PATH.read_text())
    else:
        index = {"episodes": []}

    index["episodes"] = [e for e in index["episodes"] if e["id"] != episode_id]
    index["episodes"].append({"id": episode_id, "title": title, "published": published})
    index["episodes"].sort(key=lambda e: e["published"], reverse=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2))
