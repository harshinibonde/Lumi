from __future__ import annotations

import math
from typing import Any

import numpy as np


def _estimate_syllables(word: str) -> int:
    w = "".join(ch for ch in word.lower() if ch.isalpha())
    if not w:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in w:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if w.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _speech_rate_from_transcript(transcript: str, duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    words = [w for w in transcript.split() if w.strip()]
    if not words:
        return 0.0
    syllables = sum(_estimate_syllables(w) for w in words)
    return float(syllables) / float(duration_sec)


def extract_audio_features(path: str, transcript: str = "") -> dict[str, Any]:
    try:
        import librosa
    except ImportError as e:
        raise RuntimeError("librosa is not installed. Run: pip install librosa") from e

    y, sr = librosa.load(path, sr=16000, mono=True)
    if y.size == 0:
        return {
            "duration_sec": 0.0,
            "mfcc": [0.0] * 13,
            "pitch_hz": 0.0,
            "energy": 0.0,
            "pause_duration_sec": 0.0,
            "speech_rate": 0.0,
        }

    duration_sec = float(librosa.get_duration(y=y, sr=sr))
    frame_length = 1024
    hop_length = 256

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=frame_length, hop_length=hop_length)
    mfcc_mean = np.mean(mfcc, axis=1).tolist()

    f0 = librosa.yin(y, fmin=50, fmax=350, sr=sr, frame_length=frame_length, hop_length=hop_length)
    voiced = f0[np.isfinite(f0)]
    pitch_hz = float(np.median(voiced)) if voiced.size else 0.0

    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    energy = float(np.mean(rms)) if rms.size else 0.0
    threshold = max(0.01, 0.25 * energy)
    pause_frames = int(np.sum(rms < threshold))
    pause_duration_sec = float(pause_frames * hop_length / sr)

    speech_rate = _speech_rate_from_transcript(transcript, duration_sec)

    return {
        "duration_sec": round(duration_sec, 4),
        "mfcc": [float(round(v, 6)) for v in mfcc_mean],
        "pitch_hz": round(pitch_hz, 4),
        "energy": round(energy, 6),
        "pause_duration_sec": round(pause_duration_sec, 4),
        "speech_rate": round(speech_rate, 4),
    }
