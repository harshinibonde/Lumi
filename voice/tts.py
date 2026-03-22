import os
import tempfile
from pathlib import Path


def synthesize_wav_bytes(text: str, max_chars: int = 8000) -> bytes:
    try:
        import pyttsx3
    except ImportError as e:
        raise RuntimeError(
            "pyttsx3 is not installed. Run: pip install pyttsx3"
        ) from e

    clean = (text or "").strip()
    if not clean:
        raise ValueError("Text is empty")
    clean = clean[:max_chars]

    fd, path_str = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    path = Path(path_str)
    try:
        engine = pyttsx3.init()
        rate = os.getenv("TTS_RATE")
        if rate:
            engine.setProperty("rate", int(rate))
        engine.save_to_file(clean, str(path))
        engine.runAndWait()
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError("TTS produced no audio (check pyttsx3 / SAPI setup)")
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)
