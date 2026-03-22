import os
from pathlib import Path
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_DEFAULT_BASE = "http://127.0.0.1:11434"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", _DEFAULT_BASE).rstrip("/")
OLLAMA_URL = os.getenv("OLLAMA_URL")
if not OLLAMA_URL:
    OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
elif not os.getenv("OLLAMA_BASE_URL"):
    parts = urlsplit(OLLAMA_URL)
    if parts.scheme and parts.netloc:
        OLLAMA_BASE_URL = f"{parts.scheme}://{parts.netloc}".rstrip("/")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))


class OllamaGenerationError(Exception):
    """Raised when Ollama is unreachable or returns an error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _parse_error_body(response: requests.Response) -> str:
    try:
        data = response.json()
        err = data.get("error")
        if isinstance(err, str):
            return err
        if err is not None:
            return str(err)
    except Exception:
        pass
    text = (response.text or "").strip()
    return text if text else f"HTTP {response.status_code}"


def generate_response(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as e:
        raise OllamaGenerationError(
            f"Cannot reach Ollama at {OLLAMA_URL}. Is `ollama serve` running? ({e})"
        ) from e

    if response.status_code != 200:
        raise OllamaGenerationError(_parse_error_body(response))

    try:
        data = response.json()
    except Exception as e:
        raise OllamaGenerationError(f"Invalid JSON from Ollama: {e}") from e

    text = data.get("response")
    if not isinstance(text, str):
        raise OllamaGenerationError("Ollama response missing 'response' field")
    return text


def check_ollama_reachable() -> dict:
    """Lightweight health check (does not run inference)."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        ok = r.status_code == 200
        models: list[str] = []
        if ok:
            try:
                data = r.json()
                for m in data.get("models") or []:
                    name = m.get("name")
                    if isinstance(name, str):
                        models.append(name)
            except Exception:
                pass
        return {
            "reachable": ok,
            "status_code": r.status_code,
            "models": models,
        }
    except requests.RequestException as e:
        return {"reachable": False, "error": str(e), "models": []}
