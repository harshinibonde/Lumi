from __future__ import annotations

from database import save_signal

CONFUSION_PHRASES = [
    "i don't remember",
    "i forgot",
    "i can't remember",
    "where am i",
    "i'm confused",
    "what did you say",
    "i don't understand",
    "i don't know",
    "who are you",
]
POSITIVE_WORDS = ["happy", "good", "great", "lovely", "wonderful", "remember", "yes", "nice", "enjoy", "love", "family", "better"]
NEGATIVE_WORDS = ["scared", "lost", "hurt", "confused", "sad", "alone", "forget", "pain", "worried", "afraid", "miss", "cry"]
ALERT_KEYWORDS = ["fall", "fell", "hurt", "pain", "lost", "scared", "alone", "emergency", "help", "hospital", "accident", "bleeding"]


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def extract_signals(message: str, user_id: int, message_id: int) -> dict:
    text = (message or "").lower().strip()
    words = text.split()

    confusion_hits = sum(1 for phrase in CONFUSION_PHRASES if phrase in text)
    confusion_score = _clamp(confusion_hits / max(len(CONFUSION_PHRASES), 1), 0.0, 1.0)

    pos = sum(1 for w in POSITIVE_WORDS if w in words)
    neg = sum(1 for w in NEGATIVE_WORDS if w in words)
    sentiment_score = _clamp((pos - neg) / max(pos + neg, 1), -1.0, 1.0)

    response_length = len(words)
    vocabulary_diversity = len(set(words)) / max(len(words), 1)
    alert_keywords = [k for k in ALERT_KEYWORDS if k in words]

    save_signal(
        user_id=user_id,
        message_id=message_id,
        confusion_score=float(confusion_score),
        sentiment_score=float(sentiment_score),
        response_length=int(response_length),
        vocabulary_diversity=float(vocabulary_diversity),
        alert_keywords=alert_keywords,
    )

    return {
        "created_for_message_id": message_id,
        "confusion_score": float(confusion_score),
        "sentiment_score": float(sentiment_score),
        "response_length": int(response_length),
        "vocabulary_diversity": float(vocabulary_diversity),
        "alert_keywords": alert_keywords,
    }


if __name__ == "__main__":
    from database import init_db

    init_db()
    sample = extract_signals(
        "I am confused and scared, I need help",
        user_id=1,
        message_id=1,
    )
    print("Signal test:", sample)
