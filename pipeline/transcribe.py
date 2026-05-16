from faster_whisper import WhisperModel

_model = None


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel("medium", device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path):
    model = get_model()
    segments_iter, info = model.transcribe(
        audio_path,
        language="es",
        word_timestamps=False,
        vad_filter=True,
    )

    segments = []
    for i, s in enumerate(segments_iter):
        segments.append({
            "id": i,
            "start": float(s.start),
            "end": float(s.end),
            "text": s.text.strip(),
        })
    return segments, float(info.duration)
