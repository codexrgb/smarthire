"""
Evaluation & Metrics Reporting Module for SmartHire.
Saves actual calculated evaluation metrics to JSON reports.
"""

import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support, silhouette_score, confusion_matrix
from src.config import MODELS_DIR, METRICS_DIR, PROCESSED_DATA_DIR
from src.models.clustering import find_optimal_k


def evaluate_classifier(save_report: bool = True) -> Dict[str, Any]:
    """
    Evaluates trained Resume Category Classifier strictly on held-out unseen test data (20% split).
    Calculates Accuracy, Macro & Weighted Precision, Recall, F1 Score, and Confusion Matrix.
    """
    model_path = MODELS_DIR / "classifier.pkl"
    vec_path = MODELS_DIR / "tfidf_vectorizer.pkl"
    data_path = PROCESSED_DATA_DIR / "resumes.csv"

    if not data_path.exists():
        data_path = PROCESSED_DATA_DIR / "processed_resumes.csv"

    if not model_path.exists() or not vec_path.exists() or not data_path.exists():
        return {"status": "Model or processed dataset missing. Run train.py first."}

    from sklearn.model_selection import train_test_split

    model = joblib.load(model_path)
    vectorizer = joblib.load(vec_path)
    df = pd.read_csv(data_path)

    X_text = df["clean_text"].fillna("")
    y = df["category"].astype(str)

    # Filter categories with at least 2 samples for stratified split
    class_counts = y.value_counts()
    valid_classes = class_counts[class_counts >= 2].index
    mask = y.isin(valid_classes)
    X_text = X_text[mask]
    y = y[mask]

    # Recreate the exact stratified test split
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_text, y, test_size=0.2, random_state=42, stratify=y
    )

    X_test_vec = vectorizer.transform(X_test_raw)
    y_pred = model.predict(X_test_vec)

    acc = float(accuracy_score(y_test, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average="macro", zero_division=0)
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)

    # Calculate duplicate overlap between train and test
    overlap_count = len(set(X_train_raw).intersection(set(X_test_raw)))

    results = {
        "model_name": type(model).__name__,
        "total_samples": len(df),
        "train_samples": len(X_train_raw),
        "test_samples": len(X_test_raw),
        "number_of_classes": int(y.nunique()),
        "duplicate_overlap": overlap_count,
        "accuracy": round(acc, 4),
        "macro_precision": round(float(p_macro), 4),
        "weighted_precision": round(float(p_weighted), 4),
        "macro_recall": round(float(r_macro), 4),
        "weighted_recall": round(float(r_weighted), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_f1": round(float(f1_weighted), 4),
        "precision_weighted": round(float(p_weighted), 4),
        "recall_weighted": round(float(r_weighted), 4),
        "f1_weighted": round(float(f1_weighted), 4),
        "classification_report": report_dict,
        "classes": model.classes_.tolist(),
        "confusion_matrix": cm.tolist()
    }

    if save_report:
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        with open(METRICS_DIR / "classifier_metrics.json", "w") as f:
            json.dump(results, f, indent=2)

    return results


def evaluate_clustering(save_report: bool = True) -> Dict[str, Any]:
    """Evaluates Job KMeans Clustering using Inertia and Silhouette score across K range."""
    model_path = MODELS_DIR / "kmeans_clustering.pkl"
    vec_path = MODELS_DIR / "job_vectorizer.pkl"
    data_path = PROCESSED_DATA_DIR / "jobs.csv"

    if not data_path.exists():
        data_path = PROCESSED_DATA_DIR / "processed_jobs.csv"

    if not model_path.exists() or not vec_path.exists() or not data_path.exists():
        return {"status": "Clustering model or jobs dataset missing."}

    kmeans = joblib.load(model_path)
    vectorizer = joblib.load(vec_path)
    df = pd.read_csv(data_path)

    tfidf_matrix = vectorizer.transform(df["clean_description"].fillna(""))
    labels = kmeans.predict(tfidf_matrix)

    sil_score = float(silhouette_score(tfidf_matrix, labels)) if len(np.unique(labels)) > 1 else 0.0

    # Evaluate all K from 2 to 10 for full transparency
    k_eval = find_optimal_k(tfidf_matrix, k_range=range(2, 11), save_plots=save_report)

    results = {
        "selected_k_elbow": int(kmeans.n_clusters),
        "n_clusters": int(kmeans.n_clusters),
        "inertia": round(float(kmeans.inertia_), 2),
        "silhouette_score": round(sil_score, 4),
        "k_values": k_eval["k_values"],
        "silhouette_scores": k_eval["silhouette_scores"],
        "best_silhouette_k": k_eval["best_silhouette_k"],
        "max_silhouette_score": k_eval["max_silhouette_score"],
        "best_silhouette_score": k_eval["max_silhouette_score"],
        "k_details": k_eval["k_details"],
        "selection_explanation": "Elbow Method and Silhouette Score may suggest different K values. The selected K is based on the declared selection criterion.",
        "total_jobs_clustered": len(df)
    }

    if save_report:
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        with open(METRICS_DIR / "clustering_metrics.json", "w") as f:
            json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    print(evaluate_classifier())
    print(evaluate_clustering())
