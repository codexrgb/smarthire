"""
Resume Category Classifier Module for SmartHire.
Trains and benchmarks Logistic Regression vs. LinearSVC.
Calculates Accuracy, Precision, Recall, Weighted F1 Score, and Confusion Matrix.
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix

from src.config import MODELS_DIR, METRICS_DIR, CLASSIFIER_TFIDF_PARAMS
from src.data.preprocess import clean_text


def train_resume_classifier(
    df: pd.DataFrame,
    text_col: str = "clean_text",
    label_col: str = "category",
    save_models: bool = True
) -> Dict[str, Any]:
    """
    Trains Logistic Regression and LinearSVC on resume TF-IDF features.
    Saves best model to models/classifier.pkl and vectorizer to models/tfidf_vectorizer.pkl.
    Saves metrics to reports/metrics/classifier_metrics.json.
    """
    if text_col not in df.columns or label_col not in df.columns:
        raise ValueError(f"Columns {text_col} and {label_col} must exist in df")

    X_text = df[text_col].fillna("")
    y = df[label_col].astype(str)

    # Filter categories with at least 2 samples for stratified split
    class_counts = y.value_counts()
    valid_classes = class_counts[class_counts >= 2].index
    mask = y.isin(valid_classes)
    X_text = X_text[mask]
    y = y[mask]

    # Stratified Train/Test Split
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_text, y, test_size=0.2, random_state=42, stratify=y
    )

    # Fit TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(**CLASSIFIER_TFIDF_PARAMS)
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)

    # Models to benchmark
    models_to_compare = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42, C=1.0),
        "LinearSVC": LinearSVC(random_state=42, C=1.0, dual="auto")
    }

    results = {}
    best_f1 = -1.0
    best_name = None
    best_model = None

    for name, model in models_to_compare.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average="macro", zero_division=0)
        p_weight, r_weight, f1_weight, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)
        report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_test, y_pred, labels=model.classes_)

        results[name] = {
            "accuracy": round(acc, 4),
            "macro_precision": round(float(p_macro), 4),
            "weighted_precision": round(float(p_weight), 4),
            "macro_recall": round(float(r_macro), 4),
            "weighted_recall": round(float(r_weight), 4),
            "macro_f1": round(float(f1_macro), 4),
            "weighted_f1": round(float(f1_weight), 4),
            "precision": round(float(p_weight), 4),
            "recall": round(float(r_weight), 4),
            "f1_score": round(float(f1_weight), 4),
            "classification_report": report_dict,
            "confusion_matrix": cm.tolist(),
            "classes": model.classes_.tolist()
        }

        print(f"[CLASSIFIER EVAL] {name} -> Accuracy: {acc:.4f}, Weighted F1: {f1_weight:.4f}, Macro F1: {f1_macro:.4f}")

        if f1_weight > best_f1:
            best_f1 = f1_weight
            best_name = name
            best_model = model

    print(f"[CLASSIFIER] Best Model Selected: {best_name} (Weighted F1: {best_f1:.4f})")

    if save_models:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(best_model, MODELS_DIR / "classifier.pkl")
        joblib.dump(vectorizer, MODELS_DIR / "tfidf_vectorizer.pkl")

    overlap_count = len(set(X_train_raw).intersection(set(X_test_raw)))

    metrics_payload = {
        "best_model_name": best_name,
        "total_samples": len(df),
        "train_samples": len(X_train_raw),
        "test_samples": len(X_test_raw),
        "number_of_classes": int(y.nunique()),
        "duplicate_overlap": overlap_count,
        "accuracy": results[best_name]["accuracy"],
        "macro_precision": results[best_name]["macro_precision"],
        "weighted_precision": results[best_name]["weighted_precision"],
        "macro_recall": results[best_name]["macro_recall"],
        "weighted_recall": results[best_name]["weighted_recall"],
        "macro_f1": results[best_name]["macro_f1"],
        "weighted_f1": results[best_name]["weighted_f1"],
        "precision_weighted": results[best_name]["weighted_precision"],
        "recall_weighted": results[best_name]["weighted_recall"],
        "f1_weighted": results[best_name]["weighted_f1"],
        "classification_report": results[best_name]["classification_report"],
        "classes": results[best_name]["classes"],
        "confusion_matrix": results[best_name]["confusion_matrix"],
        "all_models_compared": {
            k: {m: v[m] for m in ["accuracy", "macro_precision", "weighted_precision", "macro_recall", "weighted_recall", "macro_f1", "weighted_f1"]}
            for k, v in results.items()
        }
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(METRICS_DIR / "classifier_metrics.json", "w") as f:
        json.dump(metrics_payload, f, indent=2)

    return {
        "best_model_name": best_name,
        "best_model": best_model,
        "vectorizer": vectorizer,
        "metrics": metrics_payload
    }


def predict_resume_category(
    text: str,
    model: Any = None,
    vectorizer: Any = None
) -> Tuple[str, float, Dict[str, float]]:
    """
    Predicts resume job category using trained model and vectorizer.
    """
    if model is None:
        model_path = MODELS_DIR / "classifier.pkl"
        if model_path.exists():
            model = joblib.load(model_path)
        else:
            return ("Model Not Trained", 0.0, {})

    if vectorizer is None:
        vec_path = MODELS_DIR / "tfidf_vectorizer.pkl"
        if vec_path.exists():
            vectorizer = joblib.load(vec_path)
        else:
            return ("Vectorizer Not Trained", 0.0, {})

    cleaned = clean_text(text)
    if not cleaned:
        return ("Unknown", 0.0, {})

    X_vec = vectorizer.transform([cleaned])
    predicted_cat = str(model.predict(X_vec)[0])

    probs_dict = {}
    confidence = 1.0

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_vec)[0]
        for cls, prob in zip(model.classes_, probs):
            probs_dict[cls] = float(prob)
        confidence = float(np.max(probs))
    elif hasattr(model, "decision_function"):
        scores = model.decision_function(X_vec)[0]
        if len(model.classes_) > 2:
            exp_scores = np.exp(scores - np.max(scores))
            probs = exp_scores / np.sum(exp_scores)
            confidence = float(np.max(probs))
            for cls, prob in zip(model.classes_, probs):
                probs_dict[cls] = float(prob)
        else:
            confidence = 1.0
            probs_dict[predicted_cat] = 1.0

    sorted_probs = dict(sorted(probs_dict.items(), key=lambda x: x[1], reverse=True)[:5])
    return (predicted_cat, round(confidence, 4), sorted_probs)
