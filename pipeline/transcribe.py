import sys

from faster_whisper import WhisperModel

_model = None

MAX_CHARS = 300
MAX_DURATION = 30.0


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel("medium", device="cpu", compute_type="int8")
    return _model


def _merge_segments(raw):
    merged = []
    current = None
    for s in raw:
        if current is None:
            current = {"start": s["start"], "end": s["end"], "text": s["text"]}
            continue
        combined_text = current["text"] + " " + s["text"]
        combined_duration = s["end"] - current["start"]
        if len(combined_text) <= MAX_CHARS and combined_duration <= MAX_DURATION:
            current["text"] = combined_text
            current["end"] = s["end"]
        else:
            merged.append(current)
            current = {"start": s["start"], "end": s["end"], "text": s["text"]}
    if current is not None:
        merged.append(current)
    return [{"id": i, **m} for i, m in enumerate(merged)]


def transcribe(audio_path):
    model = get_model()
    segments_iter, info = model.transcribe(
        audio_path,
        language="es",
        word_timestamps=False,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 1200},
    )

    raw = []
    total = float(info.duration)
    for s in segments_iter:
        raw.append({
            "start": float(s.start),
            "end": float(s.end),
            "text": s.text.strip(),
        })
        pct = min(100, int(s.end / total * 100)) if total else 0
        sys.stdout.write(f"\r  transcribing: {_fmt(s.end)} / {_fmt(total)} ({pct}%)")
        sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()
    segments = _merge_segments(raw)
    return segments, total


def _fmt(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"
