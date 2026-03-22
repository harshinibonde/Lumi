import os
import threading

_MODEL = None
_MODEL_LOCK = threading.Lock()
_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")


def _get_model():
    global _MODEL
    with _MODEL_LOCK:
        if _MODEL is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise RuntimeError(
                    "faster-whisper is not installed. Run: pip install faster-whisper"
                ) from e
            device = os.getenv("WHISPER_DEVICE", "cpu")
            compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
            _MODEL = WhisperModel(_MODEL_NAME, device=device, compute_type=compute_type)
        return _MODEL


def transcribe_file(path: str, language: str | None = None) -> str:
    model = _get_model()
    kwargs = {"beam_size": 5}
    if language:
        kwargs["language"] = language
    segments, _info = model.transcribe(path, **kwargs)
    parts = [s.text for s in segments]
    return " ".join(p.strip() for p in parts if p.strip()).strip()
