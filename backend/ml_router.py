from __future__ import annotations

import json
from typing import Any

import joblib
import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

MODEL_PATH = "ensemble.pkl"
SCALER_PATH = "scaler.pkl"
IMPUTER_PATH = "imputer.pkl"
FEATURES_PATH = "feature_names.pkl"

router = APIRouter(prefix="/ml", tags=["ml"])

LABEL_MAP = {0: "Normal", 1: "Mild", 2: "Moderate", 3: "Severe"}


class PredictRequest(BaseModel):
    MMSE: float
    Age: float
    Gender: float
    EducationLevel: float
    FunctionalAssessment: float
    ADL: float
    MemoryComplaints: float
    BehavioralProblems: float
    Orientation_score: float
    Registration_score: float
    Attention_score: float
    Recall_score: float
    Language_score: float
    Visuospatial_score: float


def load_model_bundle() -> dict[str, Any]:
    return {
        "model": joblib.load("ensemble.pkl"),
        "scaler": joblib.load("scaler.pkl"),
        "imputer": joblib.load("imputer.pkl"),
        "feature_names": joblib.load("feature_names.pkl"),
    }


def models_loaded() -> bool:
    from pathlib import Path

    return Path(MODEL_PATH).exists() and Path(SCALER_PATH).exists() and Path(IMPUTER_PATH).exists() and Path(FEATURES_PATH).exists()


def rule_based_from_mmse(mmse_total: float) -> str:
    if mmse_total >= 27:
        return "Normal"
    if mmse_total >= 18:
        return "Mild"
    if mmse_total >= 10:
        return "Moderate"
    return "Severe"


def prediction_to_label(pred: Any) -> str:
    try:
        return LABEL_MAP.get(int(pred), str(pred))
    except (TypeError, ValueError):
        return str(pred)


@router.post("/predict")
def predict(payload: PredictRequest, request: Request) -> dict[str, Any]:
    bundle = getattr(request.app.state, "model_bundle", None)
    if bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    feature_names = bundle["feature_names"]
    imputer = bundle["imputer"]
    scaler = bundle["scaler"]
    model = bundle["model"]

    input_map = payload.model_dump()
    feature_vector = [float(input_map[k]) for k in feature_names]
    x = np.array(feature_vector, dtype=float).reshape(1, -1)
    x = imputer.transform(x)
    x = scaler.transform(x)

    ensemble_pred = prediction_to_label(model.predict(x)[0])
    proba = model.predict_proba(x)[0]
    classes = [prediction_to_label(c) for c in list(model.classes_)]
    confidence = float(np.max(proba))

    estimator_map = dict(model.estimators_)
    svm_pred = prediction_to_label(estimator_map["svm"].predict(x)[0])
    rf_pred = prediction_to_label(estimator_map["rf"].predict(x)[0])
    mlp_pred = prediction_to_label(estimator_map["mlp"].predict(x)[0])

    rule_based = rule_based_from_mmse(payload.MMSE)
    agreement = int(ensemble_pred == rule_based)

    return {
        "ml_prediction": ensemble_pred,
        "ml_confidence": confidence,
        "class_probabilities": {k: float(v) for k, v in zip(classes, proba)},
        "svm_prediction": svm_pred,
        "rf_prediction": rf_pred,
        "mlp_prediction": mlp_pred,
        "rule_based": rule_based,
        "agreement": agreement,
        "ml_features": feature_vector,
    }


@router.get("/results/{user_id}")
def get_results_for_user(user_id: int) -> list[dict[str, Any]]:
    from database import get_conn

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM screening_results WHERE user_id = ? ORDER BY datetime(created_at) ASC",
            (user_id,),
        ).fetchall()

    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["domain_scores"] = json.loads(item.get("domain_scores") or "{}")
        item["ml_features"] = json.loads(item.get("ml_features") or "[]")
        out.append(item)
    return out


@router.get("/results")
def get_all_results() -> list[dict[str, Any]]:
    from database import get_conn

    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM screening_results ORDER BY datetime(created_at) DESC").fetchall()

    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["domain_scores"] = json.loads(item.get("domain_scores") or "{}")
        item["ml_features"] = json.loads(item.get("ml_features") or "[]")
        out.append(item)
    return out
