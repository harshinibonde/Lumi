from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC


@dataclass(frozen=True)
class DatasetConfig:
    key: str
    path: Path
    label_col: str
    feature_cols: list[str]
    drop_cols: list[str]
    categorical_cols: list[str]


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models" / "screening"
REPORT_PATH = MODEL_DIR / "training_report.txt"

DATASETS = [
    DatasetConfig(
        key="ds1",
        path=DATA_DIR / "dementia_prediction.csv",
        label_col="Group",
        feature_cols=["Age", "M/F", "EDUC", "SES", "MMSE", "eTIV", "nWBV", "ASF"],
        drop_cols=["Subject ID", "MRI ID", "Hand", "Visit", "MR Delay"],
        categorical_cols=["M/F"],
    ),
    DatasetConfig(
        key="ds2",
        path=DATA_DIR / "el_kharoua.csv",
        label_col="Diagnosis",
        feature_cols=[
            "Age",
            "Gender",
            "BMI",
            "Smoking",
            "AlcoholConsumption",
            "PhysicalActivity",
            "DietQuality",
            "SleepQuality",
            "FamilyHistoryAlzheimers",
            "CardiovascularDisease",
            "Diabetes",
            "Depression",
            "HeadInjury",
            "Hypertension",
            "SystolicBP",
            "DiastolicBP",
            "CholesterolTotal",
            "CholesterolLDL",
            "CholesterolHDL",
            "CholesterolTriglycerides",
            "MMSE",
            "FunctionalAssessment",
            "MemoryComplaints",
            "BehavioralProblems",
            "ADL",
            "Confusion",
            "Disorientation",
            "PersonalityChanges",
            "DifficultyCompletingTasks",
            "Forgetfulness",
        ],
        drop_cols=["PatientID", "DoctorInCharge"],
        categorical_cols=["Gender"],
    ),
]

MODEL_SPECS: list[tuple[str, Any]] = [
    ("svm", SVC(kernel="rbf", probability=True, class_weight="balanced", random_state=42)),
    (
        "rf",
        RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42,
        ),
    ),
    ("mlp", MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)),
]


def _load_dataset(config: DatasetConfig) -> tuple[pd.DataFrame, np.ndarray]:
    if not config.path.exists():
        raise FileNotFoundError(f"Dataset not found: {config.path}")
    df = pd.read_csv(config.path)
    if config.drop_cols:
        existing_drop = [col for col in config.drop_cols if col in df.columns]
        if existing_drop:
            df = df.drop(columns=existing_drop)
    missing_features = [col for col in config.feature_cols if col not in df.columns]
    if missing_features:
        raise ValueError(f"{config.key}: missing required columns: {missing_features}")
    if config.label_col not in df.columns:
        raise ValueError(f"{config.key}: missing label column: {config.label_col}")

    x = df[config.feature_cols].copy()
    for col in config.categorical_cols:
        encoder = LabelEncoder()
        x[col] = encoder.fit_transform(x[col].astype(str))
    for col in x.columns:
        x[col] = pd.to_numeric(x[col], errors="coerce")
    na_before = int(x.isna().sum().sum())
    if na_before > 0:
        x = x.fillna(x.median(numeric_only=True))
        x = x.fillna(0.0)
        print(f"{config.key}: imputed {na_before} missing feature values.")

    y_raw = df[config.label_col]
    if config.key == "ds1":
        mapping = {"demented": 1, "nondemented": 0}
        normalized = y_raw.astype(str).str.strip().str.lower()
        keep_mask = normalized.isin(mapping.keys())
        dropped = int((~keep_mask).sum())
        if dropped > 0:
            x = x.loc[keep_mask].reset_index(drop=True)
            normalized = normalized.loc[keep_mask].reset_index(drop=True)
            print(f"ds1: dropped {dropped} rows with unsupported Group labels (e.g. Converted).")
        y_arr = normalized.map(mapping).astype(np.int32).to_numpy()
    else:
        y_arr = y_raw.astype(np.int32).to_numpy()
    return x, y_arr


def _positive_class_probability(model: Any, x_test_scaled: np.ndarray) -> np.ndarray:
    probs = model.predict_proba(x_test_scaled)
    classes = getattr(model, "classes_", None)
    if classes is not None and len(classes) > 0:
        classes_arr = np.asarray(classes)
        match = np.where(classes_arr == 1)[0]
        idx = int(match[0]) if match.size else int(len(classes_arr) - 1)
    else:
        idx = int(probs.shape[1] - 1)
    return probs[:, idx]


def _evaluate_model(
    *,
    model_name: str,
    dataset_key: str,
    estimator: Any,
    model: Any,
    x_test_scaled: np.ndarray,
    y_test: np.ndarray,
    x_full: pd.DataFrame,
    y_full: np.ndarray,
) -> dict[str, Any]:
    y_pred = model.predict(x_test_scaled)
    y_prob = _positive_class_probability(model, x_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        roc_auc = float("nan")

    cv_pipeline = ImbPipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("smote", SMOTE(random_state=42)),
            ("model", clone(estimator)),
        ]
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(cv_pipeline, x_full, y_full, cv=cv, scoring="f1")

    return {
        "title": f"{dataset_key.upper()}-{model_name.upper()}",
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "confusion_matrix": cm,
        "cv_scores": cv_scores,
    }


def _format_report_block(metrics: dict[str, Any]) -> str:
    cm = metrics["confusion_matrix"]
    cv_scores = metrics["cv_scores"]
    return "\n".join(
        [
            f"[{metrics['title']}]",
            f"Accuracy: {metrics['accuracy']:.4f}",
            f"Precision: {metrics['precision']:.4f}",
            f"Recall: {metrics['recall']:.4f}",
            f"F1-score: {metrics['f1']:.4f}",
            f"ROC-AUC: {metrics['roc_auc']:.4f}",
            "Confusion Matrix:",
            str(cm),
            f"5-fold CV F1 scores: {np.array2string(cv_scores, precision=4)}",
            f"5-fold CV F1 mean: {float(np.mean(cv_scores)):.4f}",
            f"5-fold CV F1 std: {float(np.std(cv_scores)):.4f}",
        ]
    )


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    report_lines: list[str] = []

    for config in DATASETS:
        x, y = _load_dataset(config)
        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )

        for model_suffix, estimator in MODEL_SPECS:
            scaler = StandardScaler()
            x_train_scaled = scaler.fit_transform(x_train)
            x_test_scaled = scaler.transform(x_test)

            smote = SMOTE(random_state=42)
            x_resampled, y_resampled = smote.fit_resample(x_train_scaled, y_train)

            model = clone(estimator)
            model.fit(x_resampled, y_resampled)

            model_path = MODEL_DIR / f"{config.key}_{model_suffix}.pkl"
            scaler_path = MODEL_DIR / f"{config.key}_{model_suffix}_scaler.pkl"
            joblib.dump({"model": model, "feature_names": config.feature_cols}, model_path)
            joblib.dump(scaler, scaler_path)

            metrics = _evaluate_model(
                model_name=model_suffix,
                dataset_key=config.key,
                estimator=estimator,
                model=model,
                x_test_scaled=x_test_scaled,
                y_test=y_test,
                x_full=x,
                y_full=y,
            )
            block = _format_report_block(metrics)
            print(block)
            print("")
            report_lines.append(block)
            report_lines.append("")

    REPORT_PATH.write_text("\n".join(report_lines).strip() + "\n", encoding="utf-8")
    print(f"Training report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
