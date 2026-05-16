from anthropic import Anthropic
from pydantic import BaseModel

MODEL = "claude-sonnet-4-6"
BATCH_SIZE = 20
CONTEXT_SIZE = 3
MAX_TOKENS = 4096

SYSTEM = (
    "You are translating a Spanish podcast for an English-speaking learner. "
    "Translate each marked Spanish segment to natural English. Preserve meaning "
    "over literal wording — translations should sound natural to a native English "
    "speaker, not word-for-word. Return exactly one translation per requested "
    "segment id, in the same order."
)


class Translation(BaseModel):
    id: int
    en: str


class TranslationBatch(BaseModel):
    translations: list[Translation]


def _build_prompt(target, before, after):
    lines = ["Spanish segments. Translate ONLY the [TRANSLATE] segments.", ""]
    for seg in before:
        lines.append(f"[context] id={seg['id']}: {seg['text']}")
    for seg in target:
        lines.append(f"[TRANSLATE] id={seg['id']}: {seg['text']}")
    for seg in after:
        lines.append(f"[context] id={seg['id']}: {seg['text']}")
    return "\n".join(lines)


def translate_segments(segments):
    client = Anthropic()
    translations_by_id: dict[int, str] = {}

    total = len(segments)
    for i in range(0, total, BATCH_SIZE):
        target = segments[i:i + BATCH_SIZE]
        before = segments[max(0, i - CONTEXT_SIZE):i]
        after = segments[i + BATCH_SIZE:i + BATCH_SIZE + CONTEXT_SIZE]

        response = client.messages.parse(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            messages=[{"role": "user", "content": _build_prompt(target, before, after)}],
            output_format=TranslationBatch,
        )

        batch = response.parsed_output
        if batch is None:
            raise RuntimeError(
                f"Translation response failed to parse for batch starting at segment {i}"
            )

        target_ids = {seg["id"] for seg in target}
        returned_ids = {t.id for t in batch.translations}
        if returned_ids != target_ids:
            missing = sorted(target_ids - returned_ids)
            extra = sorted(returned_ids - target_ids)
            raise RuntimeError(
                f"Translation id mismatch in batch starting at segment {i}: "
                f"missing={missing}, extra={extra}"
            )

        for t in batch.translations:
            translations_by_id[t.id] = t.en

        done = min(i + BATCH_SIZE, total)
        print(f"  translated {done}/{total}")

    return translations_by_id
