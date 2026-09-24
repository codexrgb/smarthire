"""
SmartHire Master ML Training & Evaluation Pipeline.
Executes data discovery, schema normalization, data cleaning, classifier benchmark,
recommender indexing, KMeans clustering, PCA visualization, NMF topics, and metric logging.
"""

import sys
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import json
import joblib
from pathlib import Path

from src.config import (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, REPORTS_DIR, FIGURES_DIR, METRICS_DIR, DEMO_WARNING_MESSAGE
)
from src.data.load_data import clean_and_normalize_data, save_processed_datasets, check_real_datasets_exist
from src.models.classifier import train_resume_classifier
from src.models.recommender import build_job_recommender
from src.models.clustering import find_optimal_k, cluster_jobs, create_cluster_visualization, extract_nmf_topics
from src.evaluate import evaluate_classifier, evaluate_clustering


def plot_confusion_matrix(cm_list: list, classes: list, output_path: Path):
    """Plots and saves confusion matrix heatmap."""
    cm = np.array(cm_list)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes)
    plt.title("Resume Classifier Confusion Matrix", fontsize=14, fontweight="bold")
    plt.xlabel("Predicted Category", fontsize=11)
    plt.ylabel("True Category", fontsize=11)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def run_pipeline():
    """Runs the full training, evaluation, and artifact generation pipeline."""
    print("==================================================")
    print("       SMART HIRE - ML TRAINING PIPELINE          ")
    print("==================================================")

    # Step 1: Real Dataset Discovery & Demo Check
    print("\n[STEP 1/13] Checking Dataset Discovery in data/raw/...")
    real_exist, missing_files = check_real_datasets_exist(RAW_DATA_DIR)

    if not real_exist:
        print("\n" + "!"*70)
        print("Required datasets are missing from data/raw/. Add the datasets and run training again.")
        print(f"Missing files: {missing_files}")
        print(f"⚠️ {DEMO_WARNING_MESSAGE}")
        print("!"*70 + "\n")
    else:
        print(f" -> Found all required real raw dataset files in {RAW_DATA_DIR}.")

    # Step 2 to 4: Load, Clean, and Normalize
    print("\n[STEP 2-4/13] Loading, Cleaning & Normalizing Datasets...")
    resumes_df, jobs_df, is_demo_mode = clean_and_normalize_data(RAW_DATA_DIR)

    # Save Processed CSVs
    save_processed_datasets(resumes_df, jobs_df, PROCESSED_DATA_DIR)

    # Step 5 & 6: Train and Evaluate Resume Classifier
    print("\n[STEP 5-6/13] Training Resume Classifier (Logistic Regression vs LinearSVC)...")
    cls_res = train_resume_classifier(resumes_df, text_col="clean_text", label_col="category", save_models=True)
    best_name = cls_res["best_model_name"]
    best_metrics = cls_res["metrics"]

    # Save Confusion Matrix Figure
    if "confusion_matrix" in best_metrics and "classes" in best_metrics:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        plot_confusion_matrix(best_metrics["confusion_matrix"], best_metrics["classes"], FIGURES_DIR / "confusion_matrix.png")
        print(f" -> Confusion Matrix saved to {FIGURES_DIR / 'confusion_matrix.png'}")

    # Step 7 & 8: Build Job Recommender Index
    print("\n[STEP 7-8/13] Building Job Corpus & TF-IDF Index...")
    vectorizer, job_vectors = build_job_recommender(jobs_df, text_col="clean_description", save_models=True)
    print(f" -> Job TF-IDF matrix built with shape {job_vectors.shape}.")

    # Step 9: KMeans Clustering Optimization (K=2 to 10)
    print("\n[STEP 9/13] Evaluating KMeans Clustering across K=2..10...")
    k_eval = find_optimal_k(job_vectors, k_range=range(2, 11), save_plots=True)
    kmeans_model, cluster_labels, inertia, sil_score = cluster_jobs(job_vectors, n_clusters=5)

    # Save Clustering Model Binary
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(kmeans_model, MODELS_DIR / "kmeans_clustering.pkl")

    # Step 10: PCA 2D Cluster Visualization
    print("\n[STEP 10/13] Generating PCA 2D Cluster Projection Plot...")
    pca_coords = create_cluster_visualization(job_vectors, cluster_labels, save_figure=True)
    print(f" -> Cluster visualization saved to {FIGURES_DIR / 'job_clusters_pca.png'}")

    # Step 11: NMF Topic Modeling
    print("\n[STEP 11/13] Extracting NMF Topic Modeling Keywords...")
    topics = extract_nmf_topics(job_vectors, vectorizer, n_topics=5, top_words=10)
    for topic_id, top_words in topics.items():
        print(f"   Topic {topic_id + 1}: {', '.join(top_words)}")

    # Step 12 & 13: Save Metrics & Flag Demo Mode Status
    print("\n[STEP 12-13/13] Finalizing Evaluation Reports & Saving Artifacts...")
    cls_eval = evaluate_classifier(save_report=True)
    clst_eval = evaluate_clustering(save_report=True)

    # Save Pipeline Mode Status
    pipeline_status = {
        "is_demo_mode": is_demo_mode,
        "warning_message": DEMO_WARNING_MESSAGE if is_demo_mode else None,
        "resumes_count": len(resumes_df),
        "jobs_count": len(jobs_df),
        "best_classifier": best_name
    }
    with open(METRICS_DIR / "pipeline_status.json", "w") as f:
        json.dump(pipeline_status, f, indent=2)

    print("\n==================================================")
    print("     TRAINING PIPELINE COMPLETED SUCCESSFULLY!     ")
    print("==================================================")
    if is_demo_mode:
        print(f"[WARNING] {DEMO_WARNING_MESSAGE}")
    else:
        print(" [REAL DATA MODE ACTIVE] All models trained on real datasets.")

    print(f" Best Classifier Model : {best_name}")
    print(f" Classifier Accuracy   : {cls_eval.get('accuracy', 0.0)*100:.2f}%")
    print(f" Classifier F1 Score   : {cls_eval.get('f1_weighted', 0.0)*100:.2f}%")
    print(f" Clustering Silhouette : {clst_eval.get('silhouette_score', 0.0):.4f}")
    print(" Saved Model Artifacts in models/ and Reports in reports/")
    print("==================================================\n")


if __name__ == "__main__":
    run_pipeline()
