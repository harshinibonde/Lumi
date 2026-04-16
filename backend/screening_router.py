import json
import logging
import re
from difflib import SequenceMatcher
from typing import Any

from rapidfuzz import fuzz

import numpy as np
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel

from auth_router import get_current_user
from database import (
    complete_screening_session,
    create_screening_session,
    get_conn,
    save_answer,
    save_result,
)
from ml_router import prediction_to_label, rule_based_from_mmse
from rate_limiter import limiter

router = APIRouter(prefix="/screening", tags=["screening"])
logger = logging.getLogger(__name__)

REGISTRATION_WORDS = {
    "A": ["apple", "table", "penny"],
    "B": ["ball", "car", "man"],
    "C": ["milk", "river", "church"],
}

ATTENTION_SERIAL_7S = ["93", "86", "79", "72", "65"]
ATTENTION_WORLD_BACK = ["D", "L", "R", "O", "W"]
EXPECTED_FEATURE_COUNT = 14
VALID_TASK_RANGE = set(range(1, 12))
TASK_DOMAIN_MAP = {
    1: "Orientation",
    2: "Orientation",
    3: "Registration",
    4: "Attention",
    5: "Recall",
    6: "Language",
    7: "Language",
    8: "Language",
    9: "Language",
    10: "Language",
    11: "Visuospatial",
}
MANUAL_TASKS = {1, 2, 8, 9, 10, 11}
AUTO_SCORE_TASKS = {3, 4, 5, 6, 7}

# Synonym maps for fuzzy matching in naming tasks
NAMING_SYNONYMS = {
    "pencil": ["pencil", "pen", "crayon"],
    "watch": ["watch", "clock", "wristwatch", "timepiece"],
}


class StartSessionRequest(BaseModel):
    setting: str = "clinical"


class AnswerIn(BaseModel):
    session_id: int
    task_number: int
    domain: str
    answer_text: str
    score_awarded: int | None = None


class CompleteSessionRequest(BaseModel):
    session_id: int
    intake: dict[str, float]


def _get_session(session_id: int, user_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM screening_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def _task_max(task_number: int) -> int:
    max_map = {1: 5, 2: 5, 3: 3, 4: 5, 5: 3, 6: 2, 7: 1, 8: 3, 9: 1, 10: 1, 11: 1}
    return max_map[task_number]


def _validate_answer_payload(payload: AnswerIn) -> None:
    if payload.task_number not in VALID_TASK_RANGE:
        raise HTTPException(status_code=400, detail="task_number must be between 1 and 11")

    expected_domain = TASK_DOMAIN_MAP[payload.task_number].lower()
    if payload.domain.strip().lower() != expected_domain:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain for task {payload.task_number}; expected {TASK_DOMAIN_MAP[payload.task_number]}",
        )

    has_text = bool((payload.answer_text or "").strip())
    if not has_text and payload.task_number not in MANUAL_TASKS:
        raise HTTPException(status_code=400, detail="answer_text cannot be empty")


def _validate_complete_payload(payload: CompleteSessionRequest) -> None:
    required_fields = [
        "age",
        "gender",
        "education",
        "functional_assessment",
        "adl",
        "memory_complaints",
        "behavioral_problems",
    ]

    for key in required_fields:
        if key not in payload.intake:
            raise HTTPException(status_code=400, detail=f"Missing intake field: {key}")
        if payload.intake[key] is None:
            raise HTTPException(status_code=400, detail=f"Intake field cannot be null: {key}")

    if float(payload.intake["age"]) <= 0:
        raise HTTPException(status_code=400, detail="age must be greater than 0")
    if float(payload.intake["education"]) < 0:
        raise HTTPException(status_code=400, detail="education must be greater than or equal to 0")


def _fuzzy_match(token: str, target: str, threshold: int = 80) -> bool:
    """Check if a token fuzzy-matches a target word (ratio OR partial_ratio)."""
    return fuzz.ratio(token, target) > threshold or fuzz.partial_ratio(token, target) > threshold


def _auto_score(task_number: int, answer_text: str, session: dict[str, Any]) -> int:
    """Robust auto-scoring with fuzzy matching and synonym support."""
    normalized = answer_text.strip().lower()
    tokens = re.findall(r"[a-z0-9]+", normalized)

    if task_number in {1, 2}:
        # Orientation: count non-empty tokens up to 5
        return min(5, len(tokens))

    if task_number == 3:
        # Registration: fuzzy match each expected word
        words = REGISTRATION_WORDS.get(session["registration_set"], [])
        score = 0
        for w in words:
            if any(_fuzzy_match(t, w) for t in tokens):
                score += 1
        return score

    if task_number == 4:
        # Attention
        if session["attention_variant"] == "serial_7s":
            parts = re.findall(r"\d+", normalized)
            expected = ATTENTION_SERIAL_7S
            score = 0
            for i, v in enumerate(expected):
                if i < len(parts):
                    try:
                        if abs(int(parts[i]) - int(v)) <= 1:  # ±1 tolerance
                            score += 1
                    except ValueError:
                        pass
            return score
        else:
            # WORLD backwards
            letters_only = "".join(ch for ch in normalized.upper() if ch.isalpha())
            target = "DLROW"
            # Full credit only if all 5 letters present and fuzzy match is very high
            if len(letters_only) >= 5 and fuzz.ratio(letters_only[:5], target) > 90:
                return 5
            # Fallback: positional character scoring
            letters = list(letters_only)[:5]
            target_list = list(target)
            return sum(1 for i, ch in enumerate(target_list) if i < len(letters) and letters[i] == ch)

    if task_number == 5:
        # Recall: fuzzy match each expected word
        words = REGISTRATION_WORDS.get(session["registration_set"], [])
        score = 0
        for w in words:
            if any(_fuzzy_match(t, w) for t in tokens):
                score += 1
        return score

    if task_number == 6:
        # Naming: fuzzy match with synonyms
        score = 0
        for _obj_key, synonyms in NAMING_SYNONYMS.items():
            if any(_fuzzy_match(t, syn) for t in tokens for syn in synonyms):
                score += 1
        return score

    if task_number == 7:
        # Repetition: fuzzy match against target phrase
        target = "no ifs ands or buts"
        cleaned = " ".join(tokens)
        ratio = fuzz.ratio(cleaned, target)
        # Also try SequenceMatcher as fallback
        seq_ratio = SequenceMatcher(None, cleaned, target).ratio()
        best = max(ratio, seq_ratio * 100)
        return 1 if best >= 70 else 0

    return 0


@router.post("/start")
@limiter.limit("10/minute")
def start_session(request: Request, payload: StartSessionRequest = Body(...), user: dict = Depends(get_current_user)):
    """Start a new screening session with balanced cognitive task variants."""
    _ = request
    session = create_screening_session(int(user["id"]), payload.setting)
    registration_set = session["registration_set"]
    attention_variant = session["attention_variant"]

    place_prompts = (
        ["Country", "State", "City", "Hospital name", "Floor"]
        if payload.setting == "clinical"
        else ["Country", "State", "City", "Neighbourhood", "Street address"]
    )

    return {
        "session": session,
        "variants": {
            "registration_words": REGISTRATION_WORDS[registration_set],
            "attention_variant": attention_variant,
            "orientation_place_prompts": place_prompts,
        },
    }


@router.post("/answer")
@limiter.limit("30/minute")
def submit_answer(request: Request, payload: AnswerIn = Body(...), user: dict = Depends(get_current_user)):
    """Store one screening answer with manual or auto-scoring rules."""
    try:
        _ = request
        _validate_answer_payload(payload)

        session = _get_session(payload.session_id, int(user["id"]))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        answer = payload.answer_text
        max_score = _task_max(payload.task_number)

        # PART 6: Tasks 3-7 ALWAYS use backend auto-scoring (ignore frontend score)
        if payload.task_number in AUTO_SCORE_TASKS:
            score = _auto_score(payload.task_number, answer, session)
            auto_scored = 1
            method = "backend_auto"
        elif payload.score_awarded is not None:
            score = max(0, min(max_score, int(payload.score_awarded)))
            auto_scored = 0
            method = "frontend_score"
        else:
            if payload.task_number in MANUAL_TASKS:
                raise HTTPException(status_code=400, detail="score_awarded required for manual tasks")
            score = _auto_score(payload.task_number, answer, session)
            auto_scored = 1
            method = "backend_auto"

        # PART 7: Debug logging for every answer
        logger.info(
            "SCORE | task=%d | answer='%.80s' | score=%d/%d | method=%s",
            payload.task_number, answer, score, max_score, method,
        )

        answer_id = save_answer(
            session_id=payload.session_id,
            task_number=payload.task_number,
            domain=payload.domain,
            answer_text=answer,
            score_awarded=score,
            max_score=max_score,
            auto_scored=auto_scored,
        )
        return {
            "answer_id": answer_id,
            "task_number": payload.task_number,
            "score_awarded": score,
            "max_score": max_score,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /screening/answer")
        raise HTTPException(status_code=500, detail="Failed to score screening answer")


@router.post("/complete")
@limiter.limit("10/minute")
def complete_session(
    request: Request,
    payload: CompleteSessionRequest = Body(...),
    user: dict = Depends(get_current_user),
):
    """Compute final MMSE/domain scores and run ML inference for a session."""
    try:
        logger.info("/screening/complete started for user_id=%s session_id=%s", user.get("id"), payload.session_id)
        _validate_complete_payload(payload)

        session = _get_session(payload.session_id, int(user["id"]))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, task_number, score_awarded FROM answers WHERE session_id = ? ORDER BY id ASC",
                (payload.session_id,),
            ).fetchall()

        if not rows:
            raise HTTPException(status_code=400, detail="No answers submitted")

        task_scores = {i: 0.0 for i in range(1, 12)}
        for row in rows:
            task_num = int(row["task_number"])
            if task_num in task_scores:
                task_scores[task_num] = float(row["score_awarded"] or 0)

        domain_scores = {
            "orientation_score": float(task_scores[1] + task_scores[2]),
            "registration_score": float(task_scores[3]),
            "attention_score": float(task_scores[4]),
            "recall_score": float(task_scores[5]),
            "language_score": float(task_scores[6] + task_scores[7] + task_scores[8] + task_scores[9] + task_scores[10]),
            "visuospatial_score": float(task_scores[11]),
        }
        mmse_total = float(sum(task_scores.values()))

        bundle = getattr(request.app.state, "model_bundle", None)
        if bundle is None:
            raise HTTPException(status_code=503, detail="Model not loaded")

        feature_names = bundle["feature_names"]
        imputer = bundle["imputer"]
        scaler = bundle["scaler"]
        model = bundle["model"]

        if not feature_names or len(feature_names) != EXPECTED_FEATURE_COUNT:
            raise HTTPException(status_code=503, detail="Model feature configuration invalid")

        try:
            input_map = {
                "MMSE": float(mmse_total),
                "Age": float(payload.intake["age"]),
                "Gender": float(payload.intake["gender"]),
                "EducationLevel": float(payload.intake["education"]),
                "FunctionalAssessment": float(payload.intake["functional_assessment"]),
                "ADL": float(payload.intake["adl"]),
                "MemoryComplaints": float(payload.intake["memory_complaints"]),
                "BehavioralProblems": float(payload.intake["behavioral_problems"]),
                "Orientation_score": float(domain_scores["orientation_score"]),
                "Registration_score": float(domain_scores["registration_score"]),
                "Attention_score": float(domain_scores["attention_score"]),
                "Recall_score": float(domain_scores["recall_score"]),
                "Language_score": float(domain_scores["language_score"]),
                "Visuospatial_score": float(domain_scores["visuospatial_score"]),
            }
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"Missing intake feature: {exc}")

        feature_vector = [float(input_map[k]) for k in feature_names]
        if len(feature_vector) != EXPECTED_FEATURE_COUNT:
            raise HTTPException(status_code=503, detail="Feature vector shape mismatch")

        x = np.array(feature_vector, dtype=float).reshape(1, -1)
        x = imputer.transform(x)
        x = scaler.transform(x)

        ensemble_pred = prediction_to_label(model.predict(x)[0])
        proba = model.predict_proba(x)[0]
        confidence = float(np.max(proba))

        svm_pred = ensemble_pred
        rf_pred = ensemble_pred
        mlp_pred = ensemble_pred

        estimator_map = getattr(model, "named_estimators_", None)
        if estimator_map is None:
            raw_estimators = getattr(model, "estimators", [])
            if raw_estimators and isinstance(raw_estimators[0], tuple):
                estimator_map = {name: est for name, est in raw_estimators}
            else:
                estimator_map = {}

        try:
            svm_model = estimator_map.get("svm") if estimator_map else None
            rf_model = estimator_map.get("rf") if estimator_map else None
            mlp_model = estimator_map.get("mlp") if estimator_map else None

            if svm_model is not None:
                svm_pred = prediction_to_label(svm_model.predict(x)[0])
            if rf_model is not None:
                rf_pred = prediction_to_label(rf_model.predict(x)[0])
            if mlp_model is not None:
                mlp_pred = prediction_to_label(mlp_model.predict(x)[0])
        except Exception:
            logger.exception("Sub-estimator prediction failed; falling back to ensemble prediction")

        rule_based = rule_based_from_mmse(mmse_total)
        agreement = int(ensemble_pred == rule_based)

        save_result(
            session_id=payload.session_id,
            user_id=int(user["id"]),
            mmse_total=mmse_total,
            domain_scores=domain_scores,
            ml_prediction=ensemble_pred,
            ml_confidence=confidence,
            svm_prediction=svm_pred,
            rf_prediction=rf_pred,
            mlp_prediction=mlp_pred,
            rule_based=rule_based,
            agreement=agreement,
            ml_features=feature_vector,
            registration_set=session["registration_set"],
            attention_variant=session["attention_variant"],
        )
        complete_screening_session(payload.session_id)

        logger.info("/screening/complete finished for session_id=%s with prediction=%s", payload.session_id, ensemble_pred)

        return {
            "session_id": payload.session_id,
            "mmse_total": mmse_total,
            "domain_scores": domain_scores,
            "ml_prediction": ensemble_pred,
            "ml_confidence": confidence,
            "svm_prediction": svm_pred,
            "rf_prediction": rf_pred,
            "mlp_prediction": mlp_pred,
            "rule_based": rule_based,
            "agreement": agreement,
            "flag_for_clinical_review": bool(not agreement),
            "registration_set": session["registration_set"],
            "attention_variant": session["attention_variant"],
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /screening/complete")
        raise HTTPException(status_code=500, detail="Failed to complete screening session")


@router.get("/results")
def get_results(user: dict = Depends(get_current_user)):
    """Return historical screening results for the authenticated user."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM screening_results WHERE user_id = ? ORDER BY created_at DESC",
            (int(user["id"]),),
        ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["domain_scores"] = json.loads(item.get("domain_scores") or "{}")
        item["ml_features"] = json.loads(item.get("ml_features") or "[]")
        out.append(item)
    return out
