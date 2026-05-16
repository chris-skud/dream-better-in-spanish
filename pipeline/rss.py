import re
import unicodedata
from datetime import date

import feedparser

RSS_URL = "https://rss.buzzsprout.com/2404122.rss"


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60]


def fetch_episodes():
    """Return episodes from the RSS feed, newest first."""
    feed = feedparser.parse(RSS_URL)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Failed to parse feed at {RSS_URL}: {feed.bozo_exception}")

    episodes = []
    for entry in feed.entries:
        audio_url = _pick_audio_url(entry)
        if audio_url is None:
            continue

        pub = entry.published_parsed
        published = date(pub.tm_year, pub.tm_mon, pub.tm_mday).isoformat()
        episode_id = (
            f"ds-{pub.tm_year:04d}{pub.tm_mon:02d}{pub.tm_mday:02d}"
            f"-{slugify(entry.title)}"
        )

        episodes.append({
            "episode_id": episode_id,
            "title": entry.title,
            "audio_url": audio_url,
            "published": published,
        })

    return episodes


def _pick_audio_url(entry):
    for enc in getattr(entry, "enclosures", []) or []:
        if enc.get("type", "").startswith("audio/") and enc.get("href"):
            return enc.href
    return None
