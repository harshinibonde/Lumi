from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.impute import KNNImputer
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from sklearn.svm import SVC

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

EL_KHAROUA_PATH = DATA_DIR / "dementia_prediction.csv"
OASIS_PATH = DATA_DIR / "el_kharoua.csv"

ENSEMBLE_PATH = BASE_DIR / "ensemble.pkl"
SCALER_PATH = BASE_DIR / "scaler.pkl"
IMPUTER_PATH = BASE_DIR / "imputer.pkl"
FEATURE_NAMES_PATH = BASE_DIR / "feature_names.pkl"

TARGET_FEATURES = [
    "MMSE",
    "Age",
    "Gender",
    "EducationLevel",
    "FunctionalAssessment",
    "ADL",
    "MemoryComplaints",
    "BehavioralProblems",
    "Orientation_score",
    "Registration_score",
    "Attention_score",
    "Recall_score",
    "Language_score",
    "Visuospatial_score",
]


def _ensure_target_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in TARGET_FEATURES:
        if col not in out.columns:
            out[col] = np.nan
    return out


def _normalize_el_kharoua(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    if "MMSE" not in data.columns and "mmse_total" in data.columns:
        data["MMSE"] = data["mmse_total"]

    mapping = {
        "Age": "Age",
        "Gender": "Gender",
        "EducationLevel": "EducationLevel",
        "FunctionalAssessment": "FunctionalAssessment",
        "ADL": "ADL",
        "MemoryComplaints": "MemoryComplaints",
        "BehavioralProblems": "BehavioralProblems",
    }
    for src, dst in mapping.items():
        if src in data.columns and dst not in data.columns:
            data[dst] = data[src]

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
    data = df.copy()

    if "Group" in data.columns:
        data = data[data["Group"].str.lower() != "converted"].copy()

    data["MMSE"] = pd.to_numeric(data.get("MMSE"), errors="coerce")
    data["Age"] = pd.to_numeric(data.get("Age"), errors="coerce")
    data["Gender"] = data.get("M/F", "M").map({"F": 0, "M": 1}).astype(float)
    data["EducationLevel"] = pd.to_numeric(data.get("EDUC"), errors="coerce")

    for col in [
        "FunctionalAssessment",
        "ADL",
        "MemoryComplaints",
        "BehavioralProblems",
        "Orientation_score",
        "Registration_score",
        "Attention_score",
        "Recall_score",
        "Language_score",
        "Visuospatial_score",
    ]:
        data[col] = np.nan

    cdr = pd.to_numeric(data.get("CDR"), errors="coerce")

    data["target"] = np.where(
        cdr == 0,
        0,
        np.where(cdr == 0.5, 1, np.where(cdr == 1, 2, 3)),
    )

    data = _ensure_target_columns(data)
    return data[TARGET_FEATURES + ["target"]]


def train() -> None:
    logger.info("Starting clean model retrain")

    el_kharoua_df = pd.read_csv(EL_KHAROUA_PATH)
    oasis_df = pd.read_csv(OASIS_PATH)

    full_df = pd.concat(
        [_normalize_el_kharoua(el_kharoua_df), _normalize_oasis(oasis_df)],
        ignore_index=True,
    )

    X = full_df[TARGET_FEATURES].apply(pd.to_numeric, errors="coerce")
    y = full_df["target"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    imputer = KNNImputer(n_neighbors=5)
    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_test_scaled = scaler.transform(X_test_imputed)

    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)

    svm = SVC(probability=True, kernel="rbf", C=10, class_weight="balanced")
    rf = RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_split=5, min_samples_leaf=4, class_weight="balanced", random_state=42)
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=800, early_stopping=True, random_state=42)

    ensemble = VotingClassifier(
        estimators=[
            ("svm", svm),
            ("rf", rf),
            ("mlp", mlp),
        ],
        voting="soft",
        weights=[1, 1, 1],
    )

    ensemble.fit(X_train_res, y_train_res)

    joblib.dump(imputer, IMPUTER_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(ensemble, ENSEMBLE_PATH)
    joblib.dump(TARGET_FEATURES, FEATURE_NAMES_PATH)

    y_pred = ensemble.predict(X_test_scaled)
    logger.info("Model classification report:\n%s", classification_report(y_test, y_pred, digits=4))

    # ✅ Proper cross-validation with SMOTE (no leakage)
    pipeline = Pipeline([
        ("imputer", KNNImputer(n_neighbors=5)),
        ("scaler", StandardScaler()),
        ("smote", SMOTE(random_state=42)),
        ("model", VotingClassifier(
            estimators=[
                ("svm", SVC(probability=True, kernel="rbf", C=10, class_weight="balanced")),
                ("rf", RandomForestClassifier(n_estimators=200, max_depth=6, min_samples_split=5, min_samples_leaf=4, class_weight="balanced", random_state=42)),
                ("mlp", MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=800, early_stopping=True, random_state=42)),
            ],
            voting="soft",
            weights=[1, 1, 1],
        ))
    ])

    cv_scores = cross_val_score(pipeline, X, y, cv=5)
    logger.info("Cross-val scores (cv=5): %s", cv_scores)
    logger.info("Cross-val mean: %.4f", cv_scores.mean())

    # Validation test
    loaded_model = joblib.load(ENSEMBLE_PATH)
    loaded_scaler = joblib.load(SCALER_PATH)
    loaded_imputer = joblib.load(IMPUTER_PATH)
    loaded_feature_names = joblib.load(FEATURE_NAMES_PATH)

    sample_raw = X_test.iloc[[0]].apply(pd.to_numeric, errors="coerce")
    sample_x = loaded_scaler.transform(loaded_imputer.transform(sample_raw))
    sample_prediction = int(loaded_model.predict(sample_x)[0])
    if len(loaded_feature_names) != len(TARGET_FEATURES):
        raise RuntimeError("Saved feature_names length mismatch")

    logger.info("Sample prediction (int label): %s", sample_prediction)
    print("MODEL RETRAIN SUCCESS")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    train()