"""
Supervised Fit Predictor & Fallback Handler for SmartHire.
Provides supervised hiring-fit classification if ground-truth labeled pairs exist,
or cleanly falls back to the transparent heuristic ML-based Fit Score system.
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Any, Optional

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from src.config import MODELS_DIR
from src.features.match_features import compute_pair_match_features


def train_fit_predictor(
    pair_features_df: pd.DataFrame,
    target_col: str = "is_fit"
) -> Optional[Dict[str, Any]]:
    """
    Trains a supervised model if labeled candidate-job fit data is present.
    If ground-truth target_col is missing or invalid, returns None (disabling predictor).
    """
    if pair_features_df is None or target_col not in pair_features_df.columns:
        print("[FIT PREDICTOR] Ground-truth labeled fit dataset is unavailable. Using heuristic ML Fit Score.")
        return None

    feature_cols = ["text_similarity", "skill_overlap", "experience_match"]
    for col in feature_cols:
        if col not in pair_features_df.columns:
            print(f"[FIT PREDICTOR] Required feature '{col}' missing. Supervised fit predictor disabled.")
            return None

    X = pair_features_df[feature_cols]
    y = pair_features_df[target_col]

    model = LogisticRegression(random_state=42)
    model.fit(X, y)

    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y, y_pred, average="binary", zero_division=0)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS_DIR / "fit_predictor.pkl")

    return {
        "model": model,
        "accuracy": float(acc),
        "f1_score": float(f1)
    }


def predict_pair_fit(
    resume_text: str,
    job_text: str,
    job_skills: str = "",
    text_sim_score: float = 0.0
) -> Dict[str, Any]:
    """
    Computes fit score for a candidate-job pair.
    Uses trained supervised model if available; otherwise uses transparent ML Fit Score heuristic.
    """
    features = compute_pair_match_features(
        resume_text=resume_text,
        job_text=job_text,
        job_skills_str=job_skills,
        text_sim_score=text_sim_score
    )

    fit_model_path = MODELS_DIR / "fit_predictor.pkl"
    if fit_model_path.exists():
        try:
            model = joblib.load(fit_model_path)
            X = pd.DataFrame([[features["text_similarity"], features["skill_overlap"], features["experience_match"]]],
                             columns=["text_similarity", "skill_overlap", "experience_match"])
            fit_prob = float(model.predict_proba(X)[0][1])
            features["fit_score"] = round(fit_prob * 100.0, 2)
            features["score_type"] = "Supervised ML Probability"
        except Exception:
            features["score_type"] = "Transparent ML-based Fit Score (Heuristic)"
    else:
        features["score_type"] = "Transparent ML-based Fit Score (Heuristic)"

    return features
