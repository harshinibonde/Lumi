from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.assessment_data import ASSESSMENT_QUESTIONS

LABELS = ["normal", "mild_impairment", "moderate_impairment", "severe_impairment"]
_LABEL_TO_INDEX = {label: idx for idx, label in enumerate(LABELS)}

FEATURE_NAMES = [
    "score_ratio",
    "correct_ratio",
    "similarity_mean",
    "similarity_std",
    "cat_orientation",
    "cat_memory",
    "cat_attention",
    "cat_language",
    "word_count_norm",
    "sentence_length_norm",
    "lexical_diversity",
    "repetition_ratio",
    "avg_word_len_norm",
    "digit_ratio",
    "punct_ratio",
    "mfcc_mean_norm",
    "mfcc_std_norm",
    "pitch_norm",
    "energy_norm",
    "pause_duration_norm",
    "speech_rate_norm",
    "speech_ratio",
]

DEFAULT_SELECTED_FEATURES = [
    "score_ratio",
    "similarity_mean",
    "cat_memory",
    "cat_attention",
    "lexical_diversity",
    "repetition_ratio",
    "mfcc_mean_norm",
    "pitch_norm",
    "pause_duration_norm",
    "speech_rate_norm",
    "speech_ratio",
]

_EMBED_MODEL = None
_EMBED_LOCK = threading.Lock()
_PIPELINE = None
_PIPELINE_LOCK = threading.Lock()
_MODEL_BUNDLE = None
_MODEL_BUNDLE_LOCK = threading.Lock()
_DUAL_MODEL_BUNDLE = None
_DUAL_MODEL_BUNDLE_LOCK = threading.Lock()


@dataclass(frozen=True)
class ScreeningPipelineResult:
    score_classification: str
    final_classification: str
    svm_classification: str
    random_forest_classification: str
    mlp_classification: str
    svm_confidence: float
    random_forest_confidence: float
    mlp_confidence: float
    selected_features: dict[str, float]
    model_probabilities: dict[str, dict[str, float]]
    pipeline_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score_classification": self.score_classification,
            "final_classification": self.final_classification,
            "svm_classification": self.svm_classification,
            "random_forest_classification": self.random_forest_classification,
            "mlp_classification": self.mlp_classification,
            "svm_confidence": round(self.svm_confidence, 4),
            "random_forest_confidence": round(self.random_forest_confidence, 4),
            "mlp_confidence": round(self.mlp_confidence, 4),
            "selected_features": self.selected_features,
            "model_probabilities": self.model_probabilities,
            "pipeline_version": self.pipeline_version,
        }


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return float(a) / float(b)


def _tokenize(text: str) -> list[str]:
    try:
        import nltk
    except Exception:
        return [t for t in "".join(ch if ch.isalnum() else " " for ch in text.lower()).split() if t]

    try:
        return [t.lower() for t in nltk.word_tokenize(text) if any(ch.isalnum() for ch in t)]
    except LookupError:
        return [t for t in "".join(ch if ch.isalnum() else " " for ch in text.lower()).split() if t]


def _sentence_split(text: str) -> list[str]:
    try:
        import nltk
    except Exception:
        return [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]

    try:
        return [s.strip() for s in nltk.sent_tokenize(text) if s.strip()]
    except LookupError:
        return [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]


def _linguistic_features(text: str) -> dict[str, float]:
    words = _tokenize(text)
    sentences = _sentence_split(text)
    chars = len(text)
    word_count = len(words)
    unique_words = len(set(words))
    avg_word_len = _safe_div(sum(len(w) for w in words), word_count)
    avg_sentence_len = _safe_div(word_count, max(len(sentences), 1))
    digit_count = sum(1 for ch in text if ch.isdigit())
    punctuation_count = sum(1 for ch in text if not ch.isalnum() and not ch.isspace())
    repetitions = sum(max(0, c - 1) for c in {w: words.count(w) for w in set(words)}.values())
    return {
        "char_count": float(chars),
        "word_count": float(word_count),
        "sentence_count": float(len(sentences)),
        "sentence_length": avg_sentence_len,
        "lexical_diversity": _safe_div(unique_words, word_count),
        "avg_word_len": avg_word_len,
        "repetition_ratio": _safe_div(repetitions, max(word_count, 1)),
        "digit_ratio": _safe_div(digit_count, max(chars, 1)),
        "punct_ratio": _safe_div(punctuation_count, max(chars, 1)),
    }


def _expected_text(question_id: str) -> str:
    question = next((q for q in ASSESSMENT_QUESTIONS if q.id == question_id), None)
    if not question or question.expected_answer is None:
        return ""
    if isinstance(question.expected_answer, list):
        return " ".join(str(x) for x in question.expected_answer)
    return str(question.expected_answer)


def _get_embed_model():
    global _EMBED_MODEL
    with _EMBED_LOCK:
        if _EMBED_MODEL is None:
            from sentence_transformers import SentenceTransformer

            _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _EMBED_MODEL


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _severity_index(label: str) -> int:
    return _LABEL_TO_INDEX.get(label, 0)


def _decision_conservative(score_classification: str, svm_label: str, rf_label: str, mlp_label: str) -> str:
    idx = max(
        _severity_index(score_classification),
        _severity_index(svm_label),
        _severity_index(rf_label),
        _severity_index(mlp_label),
    )
    return LABELS[idx]


def _collect_audio_stats(audio_features: dict[str, Any] | None) -> dict[str, float]:
    if not audio_features:
        return {
            "mfcc_mean": 0.0,
            "mfcc_std": 0.0,
            "pitch_hz": 0.0,
            "energy": 0.0,
            "pause_duration_sec": 0.0,
            "speech_rate": 0.0,
        }

    mfcc_vals: list[float] = []
    pitch_vals: list[float] = []
    energy_vals: list[float] = []
    pause_vals: list[float] = []
    rate_vals: list[float] = []
    for payload in audio_features.values():
        if isinstance(payload, list):
            local_mfcc = []
            for v in payload[:13]:
                try:
                    local_mfcc.append(float(v))
                except (TypeError, ValueError):
                    continue
            mfcc_vals.extend(local_mfcc)
            continue
        if not isinstance(payload, dict):
            continue
        mfcc = payload.get("mfcc", [])
        if isinstance(mfcc, list):
            for v in mfcc[:13]:
                try:
                    mfcc_vals.append(float(v))
                except (TypeError, ValueError):
                    continue
        for k, target in (
            ("pitch_hz", pitch_vals),
            ("energy", energy_vals),
            ("pause_duration_sec", pause_vals),
            ("speech_rate", rate_vals),
        ):
            try:
                target.append(float(payload.get(k, 0.0)))
            except (TypeError, ValueError):
                pass
    return {
        "mfcc_mean": float(np.mean(mfcc_vals)) if mfcc_vals else 0.0,
        "mfcc_std": float(np.std(mfcc_vals)) if mfcc_vals else 0.0,
        "pitch_hz": float(np.mean(pitch_vals)) if pitch_vals else 0.0,
        "energy": float(np.mean(energy_vals)) if energy_vals else 0.0,
        "pause_duration_sec": float(np.mean(pause_vals)) if pause_vals else 0.0,
        "speech_rate": float(np.mean(rate_vals)) if rate_vals else 0.0,
    }


def extract_feature_dict(
    score: int,
    detailed_results: list[dict[str, Any]],
    input_modes: dict[str, str] | None = None,
    audio_features: dict[str, Any] | None = None,
) -> dict[str, float]:
    text_responses: list[str] = []
    similarity_scores: list[float] = []
    category_correct: dict[str, list[int]] = {}

    embed_model = _get_embed_model()
    for row in detailed_results:
        qid = row["question_id"]
        category = row.get("category", "unknown")
        user_text = str(row.get("user_answer") or "")
        text_responses.append(user_text)
        category_correct.setdefault(category, []).append(1 if row.get("is_correct") else 0)

        expected = _expected_text(qid)
        if user_text.strip() and expected.strip():
            embeds = embed_model.encode([user_text, expected], convert_to_numpy=True)
            similarity_scores.append(_cosine_similarity(embeds[0], embeds[1]))
        elif user_text.strip():
            similarity_scores.append(0.5)
        else:
            similarity_scores.append(0.0)

    merged_text = " ".join(text_responses).strip()
    ling = _linguistic_features(merged_text)
    audio_stats = _collect_audio_stats(audio_features)

    score_ratio = _safe_div(score, 30.0)
    correct_ratio = _safe_div(
        sum(1 for r in detailed_results if r.get("is_correct")), len(detailed_results)
    )
    similarity_mean = float(np.mean(similarity_scores)) if similarity_scores else 0.0
    similarity_std = float(np.std(similarity_scores)) if similarity_scores else 0.0
    cat_orientation = _safe_div(
        sum(category_correct.get("orientation", [])),
        max(len(category_correct.get("orientation", [])), 1),
    )
    cat_memory = _safe_div(
        sum(category_correct.get("registration", []) + category_correct.get("recall", [])),
        max(len(category_correct.get("registration", []) + category_correct.get("recall", [])), 1),
    )
    cat_attention = _safe_div(
        sum(category_correct.get("attention", [])),
        max(len(category_correct.get("attention", [])), 1),
    )
    cat_language = _safe_div(
        sum(category_correct.get("language", [])),
        max(len(category_correct.get("language", [])), 1),
    )
    speech_count = 0
    if input_modes:
        speech_count = sum(
            1 for mode in input_modes.values() if str(mode).lower() == "speech"
        )
    speech_ratio = _safe_div(speech_count, max(len(detailed_results), 1))

    return {
        "score_ratio": score_ratio,
        "correct_ratio": correct_ratio,
        "similarity_mean": similarity_mean,
        "similarity_std": similarity_std,
        "cat_orientation": cat_orientation,
        "cat_memory": cat_memory,
        "cat_attention": cat_attention,
        "cat_language": cat_language,
        "word_count_norm": ling["word_count"] / 200.0,
        "sentence_length_norm": ling["sentence_length"] / 50.0,
        "lexical_diversity": ling["lexical_diversity"],
        "repetition_ratio": ling["repetition_ratio"],
        "avg_word_len_norm": ling["avg_word_len"] / 12.0,
        "digit_ratio": ling["digit_ratio"],
        "punct_ratio": ling["punct_ratio"],
        "mfcc_mean_norm": audio_stats["mfcc_mean"] / 100.0,
        "mfcc_std_norm": audio_stats["mfcc_std"] / 100.0,
        "pitch_norm": audio_stats["pitch_hz"] / 500.0,
        "energy_norm": audio_stats["energy"],
        "pause_duration_norm": audio_stats["pause_duration_sec"] / 20.0,
        "speech_rate_norm": audio_stats["speech_rate"] / 8.0,
        "speech_ratio": speech_ratio,
    }


def vectorize_features(feature_dict: dict[str, float], selected_names: list[str]) -> np.ndarray:
    return np.array([float(feature_dict.get(name, 0.0)) for name in selected_names], dtype=np.float32).reshape(1, -1)


def _synthesize_training_data(feature_count: int, n_samples: int = 1200) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(42)
    x = rng.random((n_samples, feature_count))
    y = np.zeros(n_samples, dtype=np.int32)
    for i in range(n_samples):
        risk = 1.0 - (0.45 * x[i, 0] + 0.25 * x[i, 1] + 0.15 * x[i, 2] + 0.15 * x[i, 3])
        risk += 0.1 * x[i, min(feature_count - 1, 8)]
        if risk < 0.2:
            y[i] = 0
        elif risk < 0.4:
            y[i] = 1
        elif risk < 0.7:
            y[i] = 2
        else:
            y[i] = 3
    return x, y


def _build_pipeline(feature_count: int):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC

    x_train, y_train = _synthesize_training_data(feature_count)
    svm = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", SVC(kernel="rbf", probability=True, gamma="scale", random_state=42)),
        ]
    )
    rf = RandomForestClassifier(n_estimators=250, max_depth=10, random_state=42)
    mlp = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)),
        ]
    )
    svm.fit(x_train, y_train)
    rf.fit(x_train, y_train)
    mlp.fit(x_train, y_train)
    return {"svm": svm, "random_forest": rf, "mlp": mlp}


def _get_default_pipeline(feature_count: int):
    global _PIPELINE
    with _PIPELINE_LOCK:
        if _PIPELINE is None:
            _PIPELINE = _build_pipeline(feature_count)
        return _PIPELINE


def _load_model_bundle():
    global _MODEL_BUNDLE
    with _MODEL_BUNDLE_LOCK:
        if _MODEL_BUNDLE is not None:
            return _MODEL_BUNDLE
        model_dir = Path(os.getenv("SCREENING_MODEL_DIR", "models/screening"))
        metadata_path = model_dir / "metadata.json"
        svm_path = model_dir / "svm.joblib"
        rf_path = model_dir / "random_forest.joblib"
        mlp_path = model_dir / "mlp.joblib"
        if not (metadata_path.exists() and svm_path.exists() and rf_path.exists() and mlp_path.exists()):
            _MODEL_BUNDLE = None
            return None
        try:
            import joblib
        except Exception:
            _MODEL_BUNDLE = None
            return None
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        _MODEL_BUNDLE = {
            "selected_features": metadata.get("selected_features", DEFAULT_SELECTED_FEATURES),
            "pipeline_version": metadata.get("pipeline_version", "v4-trained-artifacts"),
            "models": {
                "svm": joblib.load(svm_path),
                "random_forest": joblib.load(rf_path),
                "mlp": joblib.load(mlp_path),
            },
        }
        return _MODEL_BUNDLE


def _load_dual_model_bundle():
    global _DUAL_MODEL_BUNDLE
    with _DUAL_MODEL_BUNDLE_LOCK:
        if _DUAL_MODEL_BUNDLE is not None:
            return _DUAL_MODEL_BUNDLE
        model_dir = Path(os.getenv("SCREENING_MODEL_DIR", "models/screening"))
        required = {
            "ds1_svm": ("ds1_svm.pkl", "ds1_svm_scaler.pkl"),
            "ds1_rf": ("ds1_rf.pkl", "ds1_rf_scaler.pkl"),
            "ds1_mlp": ("ds1_mlp.pkl", "ds1_mlp_scaler.pkl"),
            "ds2_svm": ("ds2_svm.pkl", "ds2_svm_scaler.pkl"),
            "ds2_rf": ("ds2_rf.pkl", "ds2_rf_scaler.pkl"),
            "ds2_mlp": ("ds2_mlp.pkl", "ds2_mlp_scaler.pkl"),
        }
        if not all((model_dir / names[0]).exists() and (model_dir / names[1]).exists() for names in required.values()):
            _DUAL_MODEL_BUNDLE = None
            return None
        try:
            import joblib
        except Exception:
            _DUAL_MODEL_BUNDLE = None
            return None

        members: dict[str, list[dict[str, Any]]] = {"svm": [], "random_forest": [], "mlp": []}
        architecture_map = {
            "svm": ("ds1_svm", "ds2_svm"),
            "random_forest": ("ds1_rf", "ds2_rf"),
            "mlp": ("ds1_mlp", "ds2_mlp"),
        }
        try:
            for arch, model_keys in architecture_map.items():
                for key in model_keys:
                    model_file, scaler_file = required[key]
                    model_payload = joblib.load(model_dir / model_file)
                    scaler = joblib.load(model_dir / scaler_file)
                    model = model_payload.get("model") if isinstance(model_payload, dict) else model_payload
                    feature_names = model_payload.get("feature_names", DEFAULT_SELECTED_FEATURES) if isinstance(model_payload, dict) else DEFAULT_SELECTED_FEATURES
                    members[arch].append(
                        {
                            "name": key,
                            "model": model,
                            "scaler": scaler,
                            "feature_names": list(feature_names),
                        }
                    )
        except Exception:
            _DUAL_MODEL_BUNDLE = None
            return None

        _DUAL_MODEL_BUNDLE = {
            "pipeline_version": "v5-dual-dataset-ensemble",
            "members": members,
        }
        return _DUAL_MODEL_BUNDLE


def _vectorize_member_features(feature_dict: dict[str, float], feature_names: list[str]) -> np.ndarray:
    return np.array([float(feature_dict.get(name, 0.0)) for name in feature_names], dtype=np.float32).reshape(1, -1)


def _positive_class_probability(model: Any, scaled_vector: np.ndarray) -> float:
    probs = model.predict_proba(scaled_vector)[0]
    classes = getattr(model, "classes_", None)
    if classes is not None and len(classes) > 0:
        classes_arr = np.asarray(classes)
        matches = np.where(classes_arr == 1)[0]
        if matches.size:
            idx = int(matches[0])
        else:
            idx = int(len(classes_arr) - 1)
    else:
        idx = int(len(probs) - 1)
    return float(np.clip(probs[idx], 0.0, 1.0))


def _risk_to_severity(risk_probability: float) -> str:
    if risk_probability < 0.3:
        return "normal"
    if risk_probability <= 0.5:
        return "mild_impairment"
    if risk_probability <= 0.75:
        return "moderate_impairment"
    return "severe_impairment"


def _run_legacy_pipeline(
    *,
    feature_dict: dict[str, float],
    score_classification: str,
) -> ScreeningPipelineResult:
    bundle = _load_model_bundle()
    if bundle:
        selected_names = [name for name in bundle["selected_features"] if name in FEATURE_NAMES]
        models = bundle["models"]
        pipeline_version = str(bundle["pipeline_version"])
    else:
        selected_names = DEFAULT_SELECTED_FEATURES
        models = _get_default_pipeline(len(selected_names))
        pipeline_version = "v4-fallback-synthetic"

    selected_vector = vectorize_features(feature_dict, selected_names)
    selected_features = {name: float(feature_dict.get(name, 0.0)) for name in selected_names}

    try:
        model_probs: dict[str, np.ndarray] = {}
        for model_name, model in models.items():
            probs = model.predict_proba(selected_vector)[0]
            if probs.shape[0] < len(LABELS):
                padded = np.zeros(len(LABELS), dtype=np.float32)
                padded[: probs.shape[0]] = probs
                probs = padded
            model_probs[model_name] = probs

        svm_probs = model_probs["svm"]
        rf_probs = model_probs["random_forest"]
        mlp_probs = model_probs["mlp"]
        svm_idx = int(np.argmax(svm_probs))
        rf_idx = int(np.argmax(rf_probs))
        mlp_idx = int(np.argmax(mlp_probs))
        svm_label = LABELS[svm_idx]
        rf_label = LABELS[rf_idx]
        mlp_label = LABELS[mlp_idx]
        svm_conf = float(svm_probs[svm_idx])
        rf_conf = float(rf_probs[rf_idx])
        mlp_conf = float(mlp_probs[mlp_idx])
        model_probabilities = {
            model_name: {label: float(prob[idx]) for idx, label in enumerate(LABELS)}
            for model_name, prob in model_probs.items()
        }
    except Exception:
        svm_label = score_classification
        rf_label = score_classification
        mlp_label = score_classification
        svm_conf = 0.5
        rf_conf = 0.5
        mlp_conf = 0.5
        model_probabilities = {}

    final_label = _decision_conservative(score_classification, svm_label, rf_label, mlp_label)
    return ScreeningPipelineResult(
        score_classification=score_classification,
        final_classification=final_label,
        svm_classification=svm_label,
        random_forest_classification=rf_label,
        mlp_classification=mlp_label,
        svm_confidence=svm_conf,
        random_forest_confidence=rf_conf,
        mlp_confidence=mlp_conf,
        selected_features=selected_features,
        model_probabilities=model_probabilities,
        pipeline_version=pipeline_version,
    )


try:
    _load_dual_model_bundle()
except Exception:
    pass


def run_screening_pipeline(
    *,
    score: int,
    score_classification: str,
    detailed_results: list[dict[str, Any]],
    input_modes: dict[str, str] | None = None,
    audio_features: dict[str, Any] | None = None,
) -> ScreeningPipelineResult:
    feature_dict = extract_feature_dict(
        score=score,
        detailed_results=detailed_results,
        input_modes=input_modes,
        audio_features=audio_features,
    )
    dual_bundle = _load_dual_model_bundle()
    if not dual_bundle:
        return _run_legacy_pipeline(
            feature_dict=feature_dict,
            score_classification=score_classification,
        )

    selected_features = {name: float(feature_dict.get(name, 0.0)) for name in DEFAULT_SELECTED_FEATURES}
    try:
        architecture_risk: dict[str, float] = {}
        model_probabilities: dict[str, dict[str, float]] = {}
        for arch, members in dual_bundle["members"].items():
            member_risks: list[float] = []
            for member in members:
                raw_vector = _vectorize_member_features(feature_dict, member["feature_names"])
                scaled_vector = member["scaler"].transform(raw_vector)
                risk = _positive_class_probability(member["model"], scaled_vector)
                member_risks.append(risk)
                model_probabilities[member["name"]] = {"risk_probability": float(risk)}
            ensemble_risk = float(np.mean(member_risks)) if member_risks else 0.5
            architecture_risk[arch] = ensemble_risk
            model_probabilities[f"{arch}_ensemble"] = {"risk_probability": ensemble_risk}

        svm_conf = architecture_risk.get("svm", 0.5)
        rf_conf = architecture_risk.get("random_forest", 0.5)
        mlp_conf = architecture_risk.get("mlp", 0.5)
        svm_label = _risk_to_severity(svm_conf)
        rf_label = _risk_to_severity(rf_conf)
        mlp_label = _risk_to_severity(mlp_conf)
    except Exception:
        return _run_legacy_pipeline(
            feature_dict=feature_dict,
            score_classification=score_classification,
        )

    final_label = _decision_conservative(score_classification, svm_label, rf_label, mlp_label)
    return ScreeningPipelineResult(
        score_classification=score_classification,
        final_classification=final_label,
        svm_classification=svm_label,
        random_forest_classification=rf_label,
        mlp_classification=mlp_label,
        svm_confidence=svm_conf,
        random_forest_confidence=rf_conf,
        mlp_confidence=mlp_conf,
        selected_features=selected_features,
        model_probabilities=model_probabilities,
        pipeline_version=str(dual_bundle["pipeline_version"]),
    )


def serialize_pipeline_details(result: ScreeningPipelineResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=True)
