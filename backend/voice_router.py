from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from groq import Groq

router = APIRouter(prefix="/voice", tags=["voice"])

USE_GROQ_WHISPER = os.getenv("USE_GROQ_WHISPER", "0") == "1"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def _transcribe_with_faster_whisper(path: str) -> str:
    from faster_whisper import WhisperModel

    model = WhisperModel("base", compute_type="int8")
    segments, _ = model.transcribe(path)
    return " ".join(seg.text.strip() for seg in segments).strip()


def _transcribe_with_groq(path: str) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing")
    client = Groq(api_key=GROQ_API_KEY)
    with open(path, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            file=audio,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )
    return transcript.text


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    suffix = "." + (audio.filename.split(".")[-1] if "." in audio.filename else "wav")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = _transcribe_with_groq(tmp_path) if USE_GROQ_WHISPER else _transcribe_with_faster_whisper(tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return {"text": text}
