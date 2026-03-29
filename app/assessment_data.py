from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AssessmentQuestion:
    id: str
    question: str
    category: str
    weight: int
    qtype: str
    options: list[str] | None = None
    expected_answer: str | list[str] | None = None
    prompt_words: list[str] | None = None


ASSESSMENT_QUESTIONS: list[AssessmentQuestion] = [
    AssessmentQuestion("q1", "What year is it today?", "orientation", 2, "text", expected_answer="2026"),
    AssessmentQuestion("q2", "What month is it now?", "orientation", 2, "text", expected_answer="march"),
    AssessmentQuestion("q3", "What day of the week is it?", "orientation", 1, "multiple_choice", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], expected_answer="thursday"),
    AssessmentQuestion("q4", "What city are you currently in?", "orientation", 1, "text", expected_answer="nagpur"),
    AssessmentQuestion("q5", "What country are you in?", "orientation", 1, "text", expected_answer="india"),
    AssessmentQuestion("q6", "Remember these words: Apple, Table, River.", "registration", 3, "memory_registration", prompt_words=["Apple", "Table", "River"]),
    AssessmentQuestion("q7", "What comes after Monday?", "attention", 1, "multiple_choice", options=["Sunday", "Tuesday", "Friday", "Saturday"], expected_answer="tuesday"),
    AssessmentQuestion("q8", "Count backward from 20 to 15.", "attention", 2, "text", expected_answer="20 19 18 17 16 15"),
    AssessmentQuestion("q9", "Spell WORLD backwards.", "attention", 2, "text", expected_answer="dlrow"),
    AssessmentQuestion("q10", "Which number is larger?", "attention", 1, "multiple_choice", options=["12", "21"], expected_answer="21"),
    AssessmentQuestion("q11", "What were the three words from earlier?", "recall", 3, "triple_text", expected_answer=["apple", "table", "river"]),
    AssessmentQuestion("q12", "Name this category: apple, banana, orange.", "language", 2, "text", expected_answer="fruits"),
    AssessmentQuestion("q13", "Choose the correct word to complete: Bread and ____.", "language", 2, "multiple_choice", options=["butter", "window", "tree", "clock"], expected_answer="butter"),
    AssessmentQuestion("q14", "Repeat this sentence: 'Today is a good day.'", "language", 2, "text", expected_answer="today is a good day"),
    AssessmentQuestion("q15", "Which one is an animal?", "language", 1, "multiple_choice", options=["Car", "Dog", "Chair", "Lamp"], expected_answer="dog"),
    AssessmentQuestion("q16", "If you found a stamped letter on the ground, what should you do?", "language", 2, "text", expected_answer="put it in the mailbox"),
    AssessmentQuestion("q17", "Touch your right ear with your left hand (then type done).", "language", 1, "text", expected_answer="done"),
    AssessmentQuestion("q18", "Write one short sentence about your day.", "language", 1, "text", expected_answer=None),
]


def classify_score(score: int) -> str:
    if score >= 25:
        return "normal"
    if score >= 21:
        return "mild_impairment"
    if score >= 10:
        return "moderate_impairment"
    return "severe_impairment"


def to_question_payload(question: AssessmentQuestion, include_answer: bool = False) -> dict[str, Any]:
    payload = {
        "id": question.id,
        "question": question.question,
        "category": question.category,
        "weight": question.weight,
        "type": question.qtype,
        "options": question.options or [],
        "prompt_words": question.prompt_words or [],
    }
    if include_answer:
        payload["expected_answer"] = question.expected_answer
    return payload


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _as_text(answer: Any) -> str:
    if isinstance(answer, str):
        return answer
    if isinstance(answer, list):
        return " ".join(str(x) for x in answer)
    if isinstance(answer, dict):
        return " ".join(str(v) for v in answer.values())
    return str(answer) if answer is not None else ""


def score_answer(question: AssessmentQuestion, answer: Any) -> tuple[bool, str]:
    if question.expected_answer is None:
        user_answer = _as_text(answer).strip()
        return (len(user_answer) > 0, user_answer)

    if question.qtype == "triple_text":
        raw_values: list[str]
        if isinstance(answer, list):
            raw_values = [str(v) for v in answer]
        elif isinstance(answer, dict):
            raw_values = [str(v) for v in answer.values()]
        else:
            raw_values = [p.strip() for p in str(answer).split(",")]
        user_values = [_normalize(v) for v in raw_values if _normalize(v)]
        expected = [_normalize(v) for v in (question.expected_answer or [])]
        is_correct = sorted(user_values) == sorted(expected)
        return is_correct, ", ".join(raw_values)

    user_answer = _normalize(_as_text(answer))
    expected_answer = _normalize(str(question.expected_answer))

    if question.id == "q8":
        digits = re.findall(r"\d+", user_answer)
        normalized_seq = " ".join(digits)
        return normalized_seq == expected_answer, _as_text(answer).strip()

    if question.id == "q16":
        keywords = ("mail", "post", "mailbox")
        return any(k in user_answer for k in keywords), _as_text(answer).strip()

    return user_answer == expected_answer, _as_text(answer).strip()
