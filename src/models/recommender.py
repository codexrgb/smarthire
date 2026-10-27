"""
Job Recommendation Engine Module for SmartHire.
Uses TF-IDF Vectorization and Cosine Similarity to rank local job postings.
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import MODELS_DIR, RECOMMENDER_TFIDF_PARAMS
from src.data.preprocess import clean_text
from src.features.match_features import compute_pair_match_features


def build_job_recommender(
    jobs_df: pd.DataFrame,
    text_col: str = "clean_description",
    save_models: bool = True
) -> Tuple[TfidfVectorizer, Any]:
    """Fits TF-IDF vectorizer on job dataset descriptions."""
    if text_col not in jobs_df.columns:
        raise ValueError(f"Column '{text_col}' missing from jobs_df")

    descriptions = jobs_df[text_col].fillna("")

    vectorizer = TfidfVectorizer(**RECOMMENDER_TFIDF_PARAMS)
    job_vectors = vectorizer.fit_transform(descriptions)

    if save_models:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(vectorizer, MODELS_DIR / "job_vectorizer.pkl")
        joblib.dump(job_vectors, MODELS_DIR / "job_vectors.pkl")

    return vectorizer, job_vectors


def _get_job_text_series(df: pd.DataFrame) -> pd.Series:
    """Helper to extract or build clean job text series safely."""
    if "clean_description" in df.columns:
        return df["clean_description"].fillna("")
    if "description" in df.columns:
        return df["description"].fillna("").astype(str).apply(clean_text)
    if "title" in df.columns:
        return df["title"].fillna("").astype(str).apply(clean_text)
    return pd.Series([""] * len(df))


def recommend_jobs(
    resume_text: str,
    jobs_df: pd.DataFrame,
    vectorizer: Any = None,
    job_vectors: Any = None,
    top_n: int = 10,
    category_filter: str = None
) -> pd.DataFrame:
    """
    Ranks local jobs against resume text using cosine similarity and transparent ML-Based Fit Scores.
    """
    if jobs_df is None or len(jobs_df) == 0:
        return pd.DataFrame()

    if vectorizer is None:
        vec_path = MODELS_DIR / "job_vectorizer.pkl"
        if vec_path.exists():
            vectorizer = joblib.load(vec_path)
        else:
            vectorizer = TfidfVectorizer(**RECOMMENDER_TFIDF_PARAMS)
            job_vectors = vectorizer.fit_transform(_get_job_text_series(jobs_df))

    cleaned_resume = clean_text(resume_text)
    if not cleaned_resume:
        return pd.DataFrame()

    resume_vec = vectorizer.transform([cleaned_resume])

    # Recompute job_vectors if missing or shape mismatched with jobs_df
    if job_vectors is None or (hasattr(job_vectors, "shape") and job_vectors.shape[0] != len(jobs_df)):
        job_vectors = vectorizer.transform(_get_job_text_series(jobs_df))

    # Compute pairwise Cosine Similarity
    sim_scores = cosine_similarity(resume_vec, job_vectors).flatten()

    df_copy = jobs_df.copy()
    df_copy["similarity_score"] = sim_scores

    if category_filter and category_filter != "All" and "category" in df_copy.columns:
        df_copy = df_copy[df_copy["category"].astype(str).str.lower() == category_filter.lower()]

    if len(df_copy) == 0:
        return pd.DataFrame()

    fit_scores = []
    skill_overlaps = []
    exp_matches = []

    for _, row in df_copy.iterrows():
        job_desc = str(row.get("description", ""))
        job_skills = str(row.get("skills", ""))
        sim = float(row.get("similarity_score", 0.0))

        match_feats = compute_pair_match_features(
            resume_text=resume_text,
            job_text=job_desc,
            job_skills_str=job_skills,
            text_sim_score=sim
        )

        fit_scores.append(match_feats["fit_score"])
        skill_overlaps.append(round(match_feats["skill_overlap"] * 100.0, 1))
        exp_matches.append(round(match_feats["experience_match"] * 100.0, 1))

    df_copy["ml_fit_score"] = fit_scores
    df_copy["skill_match_pct"] = skill_overlaps
    df_copy["exp_match_pct"] = exp_matches

    # Sort descending by ML Fit Score & Similarity
    df_copy = df_copy.sort_values(by=["ml_fit_score", "similarity_score"], ascending=False)
    return df_copy.head(top_n).reset_index(drop=True)
