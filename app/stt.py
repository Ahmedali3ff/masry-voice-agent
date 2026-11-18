import os
import tempfile

from faster_whisper import WhisperModel

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel(os.getenv('WHISPER_MODEL', 'small'), compute_type='int8')
    return _model


def transcribe(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
        f.write(audio_bytes)
        path = f.name
    try:
        segments, _ = _get_model().transcribe(
            path, language='ar', vad_filter=True, beam_size=5
        )
        return ' '.join(s.text.strip() for s in segments).strip()
    finally:
        os.remove(path)
