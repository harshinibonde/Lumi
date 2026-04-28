from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless backend — no display required
import matplotlib.pyplot as plt

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.impute import KNNImputer
from sklearn.model_selection import cross_val_score, train_test_split, StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.metrics import (
    classification_report,
    precision_recall_fscore_support,
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_curve,
    auc,
    precision_recall_curve
)
from sklearn.svm import SVC

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Paths and constants
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

EL_KHAROUA_PATH = DATA_DIR / "dementia_prediction.csv"
OASIS_PATH = DATA_DIR / "el_kharoua.csv"

ENSEMBLE_PATH = BASE_DIR / "ensemble.pkl"
SCALER_PATH = BASE_DIR / "scaler.pkl"
IMPUTER_PATH = BASE_DIR / "imputer.pkl"
FEATURE_NAMES_PATH = BASE_DIR / "feature_names.pkl"

# Feature set used across both datasets
TARGET_FEATURES = [
    "MMSE", "Age", "Gender", "EducationLevel", "FunctionalAssessment",
    "ADL", "MemoryComplaints", "BehavioralProblems",
    "Orientation_score", "Registration_score", "Attention_score",
    "Recall_score", "Language_score", "Visuospatial_score",
]

# ─────────────────────────────────────────────
# Data normalization utilities
# ─────────────────────────────────────────────
def _ensure_target_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all required features exist; missing ones are filled with NaN."""
    out = df.copy()
    for col in TARGET_FEATURES:
        if col not in out.columns:
            out[col] = np.nan
    return out


def _normalize_el_kharoua(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize EL-Kharoua dataset to match unified schema."""
    data = df.copy()

    if "MMSE" not in data.columns and "mmse_total" in data.columns:
        data["MMSE"] = data["mmse_total"]

    # Derive cognitive sub-scores from MMSE
    ratios = {
        "Orientation_score": 10 / 30,
        "Registration_score": 3 / 30,
        "Attention_score": 5 / 30,
        "Recall_score": 3 / 30,
        "Language_score": 8 / 30,
        "Visuospatial_score": 1 / 30,
    }

    if "MMSE" in data.columns:
        for col, ratio in ratios.items():
            if col not in data.columns:
                data[col] = pd.to_numeric(data["MMSE"], errors="coerce") * ratio

    # Target creation based on diagnosis + MMSE thresholds
    diagnosis = pd.to_numeric(data.get("Diagnosis"), errors="coerce").fillna(0)
    mmse = pd.to_numeric(data.get("MMSE"), errors="coerce").fillna(0)

    data["target"] = np.where(
        diagnosis == 0,
        0,
        np.where(mmse < 10, 3, np.where(mmse <= 17, 2, 1)),
    )

    data = _ensure_target_columns(data)
    return data[TARGET_FEATURES + ["target"]]


def _normalize_oasis(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize OASIS dataset to match unified schema."""
    data = df.copy()

    if "Group" in data.columns:
        data = data[data["Group"].str.lower() != "converted"].copy()

    data["MMSE"] = pd.to_numeric(data.get("MMSE"), errors="coerce")
    data["Age"] = pd.to_numeric(data.get("Age"), errors="coerce")
    data["Gender"] = data.get("M/F", "M").map({"F": 0, "M": 1}).astype(float)
    data["EducationLevel"] = pd.to_numeric(data.get("EDUC"), errors="coerce")

    for col in TARGET_FEATURES:
        if col not in data.columns:
            data[col] = np.nan

    cdr = pd.to_numeric(data.get("CDR"), errors="coerce")

    data["target"] = np.where(
        cdr == 0,
        0,
        np.where(cdr == 0.5, 1, np.where(cdr == 1, 2, 3)),
    )

    return data[TARGET_FEATURES + ["target"]]


# ─────────────────────────────────────────────
# Model training and evaluation
# ─────────────────────────────────────────────
def train() -> None:
    logger.info("Starting clean model retrain")

    # Load and merge datasets
    el_kharoua_df = pd.read_csv(EL_KHAROUA_PATH)
    oasis_df = pd.read_csv(OASIS_PATH)

    full_df = pd.concat(
        [_normalize_el_kharoua(el_kharoua_df), _normalize_oasis(oasis_df)],
        ignore_index=True,
    )

    X = full_df[TARGET_FEATURES].apply(pd.to_numeric, errors="coerce")
    y = full_df["target"].astype(int)

    # Train-test split with stratification to preserve class distribution
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Preprocessing: imputation → scaling → SMOTE
    imputer = KNNImputer(n_neighbors=5)
    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)

    # Base learners
    svm = SVC(probability=True, kernel="rbf", C=10, class_weight="balanced")
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=6,
        min_samples_split=5, min_samples_leaf=4,
        class_weight="balanced", random_state=42
    )
    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        max_iter=800, early_stopping=True, random_state=42
    )

    # Soft voting ensemble (weights tuned based on model performance)
    ensemble = VotingClassifier(
        estimators=[("svm", svm), ("rf", rf), ("mlp", mlp)],
        voting="soft",
        weights=[1, 2, 2],
    )

    ensemble.fit(X_train, y_train)

    # Save trained artifacts
    joblib.dump(imputer, IMPUTER_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(ensemble, ENSEMBLE_PATH)
    joblib.dump(TARGET_FEATURES, FEATURE_NAMES_PATH)

    # ─────────────────────────────────────────────
    # Evaluation
    # ─────────────────────────────────────────────
    y_pred = ensemble.predict(X_test)
    logger.info("Model classification report:\n%s",
                classification_report(y_test, y_pred, digits=4))

    # 1. Per-class performance (Precision / Recall / F1)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred)

    classes = ['Class 0', 'Class 1', 'Class 2', 'Class 3']
    x = np.arange(len(classes))
    width = 0.25

    plt.figure()
    plt.bar(x - width, precision, width, label='Precision')
    plt.bar(x, recall, width, label='Recall')
    plt.bar(x + width, f1, width, label='F1-score')
    plt.title('Per-Class Performance')
    plt.xlabel('Classes')
    plt.ylabel('Score')
    plt.xticks(x, classes)
    plt.legend()
    plt.savefig(BASE_DIR / "plot_per_class_performance.png", dpi=100)
    plt.close()

    # 2. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    ConfusionMatrixDisplay(cm).plot()
    plt.title("Confusion Matrix")
    plt.savefig(BASE_DIR / "plot_confusion_matrix.png", dpi=100)
    plt.close()

    # 3. ROC Curve (Multiclass)
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2, 3])
    y_score = ensemble.predict_proba(X_test)

    plt.figure()
    for i in range(4):
        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
        plt.plot(fpr, tpr, label=f"Class {i} (AUC = {auc(fpr, tpr):.2f})")

    plt.title("ROC Curve")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend()
    plt.savefig(BASE_DIR / "plot_roc_curve.png", dpi=100)
    plt.close()

    # 4. Precision-Recall Curve
    plt.figure()
    for i in range(4):
        p, r, _ = precision_recall_curve(y_test_bin[:, i], y_score[:, i])
        plt.plot(r, p, label=f"Class {i}")

    plt.title("Precision-Recall Curve")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.legend()
    plt.savefig(BASE_DIR / "plot_precision_recall.png", dpi=100)
    plt.close()

    # 5. Cross-validation with StratifiedKFold
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    pipeline = Pipeline([
        ("imputer", KNNImputer(n_neighbors=5)),
        ("scaler", StandardScaler()),
        ("smote", SMOTE(random_state=42)),
        ("model", ensemble),
    ])

    cv_scores = cross_val_score(pipeline, X, y, cv=skf)

    logger.info("Cross-val scores: %s", cv_scores)
    logger.info("Cross-val mean: %.4f", cv_scores.mean())
    logger.info("Cross-val std: %.4f", cv_scores.std())

    # CV stability plot
    plt.figure()
    plt.plot(range(1, 6), cv_scores, marker='o')
    plt.axhline(cv_scores.mean(), linestyle='--')
    plt.title("Cross-Validation Scores")
    plt.xlabel("Fold")
    plt.ylabel("Accuracy")
    plt.savefig(BASE_DIR / "plot_cv_scores.png", dpi=100)
    plt.close()

    print("MODEL RETRAIN SUCCESS")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    train()