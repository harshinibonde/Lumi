from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.audio_features import extract_audio_features
from app.screening_pipeline import (
    DEFAULT_SELECTED_FEATURES,
    FEATURE_NAMES,
    _linguistic_features,
)

LABELS = ["normal", "mild_impairment", "moderate_impairment", "severe_impairment"]
LABEL_TO_INT = {label: idx for idx, label in enumerate(LABELS)}


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return float(a) / float(b)


def _derive_feature_row(
    transcript: str,
    q_score: float,
    audio_payload: dict | None,
) -> dict[str, float]:
    ling = _linguistic_features(transcript)
    q_score = max(0.0, min(30.0, float(q_score)))
    score_ratio = q_score / 30.0
    # During offline training we may not have per-question correctness; approximate from score ratio.
    cat_est = score_ratio
    if audio_payload is None:
        audio_payload = {
            "mfcc": [0.0] * 13,
            "pitch_hz": 0.0,
            "energy": 0.0,
            "pause_duration_sec": 0.0,
            "speech_rate": 0.0,
        }

    mfcc = audio_payload.get("mfcc", []) if isinstance(audio_payload, dict) else []
    mfcc = [float(v) for v in mfcc[:13]] if isinstance(mfcc, list) else [0.0] * 13
    if not mfcc:
        mfcc = [0.0] * 13

    return {
        "score_ratio": score_ratio,
        "correct_ratio": score_ratio,
        "similarity_mean": 0.5,
        "similarity_std": 0.1,
        "cat_orientation": cat_est,
        "cat_memory": cat_est,
        "cat_attention": cat_est,
        "cat_language": cat_est,
        "word_count_norm": ling["word_count"] / 200.0,
        "sentence_length_norm": ling["sentence_length"] / 50.0,
        "lexical_diversity": ling["lexical_diversity"],
        "repetition_ratio": ling["repetition_ratio"],
        "avg_word_len_norm": ling["avg_word_len"] / 12.0,
        "digit_ratio": ling["digit_ratio"],
        "punct_ratio": ling["punct_ratio"],
        "mfcc_mean_norm": float(np.mean(mfcc)) / 100.0,
        "mfcc_std_norm": float(np.std(mfcc)) / 100.0,
        "pitch_norm": float(audio_payload.get("pitch_hz", 0.0)) / 500.0,
        "energy_norm": float(audio_payload.get("energy", 0.0)),
        "pause_duration_norm": float(audio_payload.get("pause_duration_sec", 0.0)) / 20.0,
        "speech_rate_norm": float(audio_payload.get("speech_rate", 0.0)) / 8.0,
        "speech_ratio": 1.0 if transcript.strip() else 0.0,
    }


def _evaluate(name: str, model, x_test: np.ndarray, y_test: np.ndarray) -> dict:
    pred = model.predict(x_test)
    acc = accuracy_score(y_test, pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, pred, average="weighted", zero_division=0
    )
    cm = confusion_matrix(y_test, pred, labels=[0, 1, 2, 3]).tolist()
    return {
        "model": name,
        "accuracy": float(acc),
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
        "confusion_matrix": cm,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Lumi screening models")
    parser.add_argument("--dataset_csv", required=True, help="Path to CSV with label/transcript/audio_path/q_score")
    parser.add_argument("--output_dir", default="models/screening", help="Directory to save model artifacts")
    parser.add_argument("--test_size", type=float, default=0.2, help="Test split ratio")
    args = parser.parse_args()

    data_path = Path(args.dataset_csv)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    required = {"label"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    features: list[list[float]] = []
    labels: list[int] = []
    selected = DEFAULT_SELECTED_FEATURES

    for _, row in df.iterrows():
        label = str(row.get("label", "")).strip().lower()
        if label not in LABEL_TO_INT:
            continue
        transcript = str(row.get("transcript", "") or "")
        q_score = float(row.get("q_score", 15.0) or 15.0)
        audio_payload = None
        audio_path = str(row.get("audio_path", "") or "").strip()
        if audio_path:
            ap = Path(audio_path)
            if ap.exists():
                try:
                    audio_payload = extract_audio_features(str(ap), transcript=transcript)
                except Exception:
                    audio_payload = None
        feature_row = _derive_feature_row(transcript=transcript, q_score=q_score, audio_payload=audio_payload)
        features.append([float(feature_row.get(name, 0.0)) for name in selected])
        labels.append(LABEL_TO_INT[label])

    if len(features) < 30:
        raise ValueError("Not enough valid rows to train. Need at least 30 labeled samples.")

    x = np.array(features, dtype=np.float32)
    y = np.array(labels, dtype=np.int32)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=args.test_size, random_state=42, stratify=y
    )

    svm = Pipeline(
        [("scaler", StandardScaler()), ("model", SVC(kernel="rbf", probability=True, gamma="scale", random_state=42))]
    )
    rf = RandomForestClassifier(n_estimators=300, max_depth=12, random_state=42)
    mlp = Pipeline(
        [("scaler", StandardScaler()), ("model", MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=700, random_state=42))]
    )

    svm.fit(x_train, y_train)
    rf.fit(x_train, y_train)
    mlp.fit(x_train, y_train)

    metrics = {
        "svm": _evaluate("svm", svm, x_test, y_test),
        "random_forest": _evaluate("random_forest", rf, x_test, y_test),
        "mlp": _evaluate("mlp", mlp, x_test, y_test),
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(svm, out_dir / "svm.joblib")
    joblib.dump(rf, out_dir / "random_forest.joblib")
    joblib.dump(mlp, out_dir / "mlp.joblib")

    metadata = {
        "pipeline_version": "v4-trained-artifacts",
        "selected_features": selected,
        "all_feature_names": FEATURE_NAMES,
        "labels": LABELS,
        "dataset_rows_used": int(len(x)),
        "metrics": metrics,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
