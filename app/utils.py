"""
Streamlit UI Utilities, Cached Loaders, and CSS Styling for SmartHire.
Provides model caching, status checks, custom styling, and sample resume text.
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

from src.config import MODELS_DIR, PROCESSED_DATA_DIR, FIGURES_DIR, METRICS_DIR, MASTER_SKILLS, DEMO_WARNING_MESSAGE
from src.data.preprocess import clean_text
from src.models.classifier import predict_resume_category
from src.models.recommender import recommend_jobs
from src.features.text_features import extract_skills, calculate_skill_match, generate_skill_gap
from src.parsing.resume_parser import extract_resume_text


@st.cache_resource
def load_trained_models():
    """Loads and caches trained ML models and vectorizers."""
    models = {}

    cls_path = MODELS_DIR / "classifier.pkl"
    cls_vec_path = MODELS_DIR / "tfidf_vectorizer.pkl"
    if cls_path.exists() and cls_vec_path.exists():
        models["classifier"] = joblib.load(cls_path)
        models["classifier_vectorizer"] = joblib.load(cls_vec_path)

    rec_vec_path = MODELS_DIR / "job_vectorizer.pkl"
    rec_vecs_path = MODELS_DIR / "job_vectors.pkl"
    if rec_vec_path.exists():
        models["job_vectorizer"] = joblib.load(rec_vec_path)
    if rec_vecs_path.exists():
        models["job_vectors"] = joblib.load(rec_vecs_path)

    kmeans_path = MODELS_DIR / "kmeans_clustering.pkl"
    if kmeans_path.exists():
        models["kmeans"] = joblib.load(kmeans_path)

    return models


@st.cache_data
def load_processed_datasets():
    """Loads and caches processed CSV datasets."""
    resumes_path = PROCESSED_DATA_DIR / "resumes.csv"
    if not resumes_path.exists():
        resumes_path = PROCESSED_DATA_DIR / "processed_resumes.csv"

    jobs_path = PROCESSED_DATA_DIR / "jobs.csv"
    if not jobs_path.exists():
        jobs_path = PROCESSED_DATA_DIR / "processed_jobs.csv"

    resumes_df = pd.read_csv(resumes_path) if resumes_path.exists() else pd.DataFrame()
    jobs_df = pd.read_csv(jobs_path) if jobs_path.exists() else pd.DataFrame()

    return resumes_df, jobs_df


def load_metrics_and_status():
    """Loads evaluation metrics and pipeline demo mode status with provenance verification."""
    metrics = {}

    cls_path = METRICS_DIR / "classifier_metrics.json"
    clst_path = METRICS_DIR / "clustering_metrics.json"
    status_path = METRICS_DIR / "pipeline_status.json"

    if cls_path.exists():
        with open(cls_path, "r") as f:
            metrics["classifier"] = json.load(f)

    if clst_path.exists():
        with open(clst_path, "r") as f:
            metrics["clustering"] = json.load(f)

    status_info = {"is_demo_mode": True}
    if status_path.exists():
        with open(status_path, "r") as f:
            status_info = json.load(f)

    # Perform runtime dataset provenance verification to prevent false "Real Data" claims
    from src.data.provenance import (
        assess_repository_datasets,
        STATUS_VERIFIED_AUTHENTIC,
        STATUS_DEMO_SYNTHETIC,
        STATUS_UNKNOWN_UNVERIFIED
    )
    from src.config import RAW_DATA_DIR

    prov_assessment = assess_repository_datasets(RAW_DATA_DIR)
    status_info["provenance"] = prov_assessment

    # Strict rule: NEVER declare real data mode unless provenance is cryptographically verified
    if prov_assessment["overall_status"] != STATUS_VERIFIED_AUTHENTIC:
        status_info["is_demo_mode"] = True
        status_info["warning_message"] = prov_assessment["banner_message"]
    else:
        status_info["is_demo_mode"] = False
        status_info["warning_message"] = None

    return metrics, status_info


def apply_custom_css():
    """Applies modern styling for Streamlit."""
    st.markdown("""
        <style>
        .main {
            background-color: #f8f9fa;
        }

        .demo-warning-banner {
            background-color: #fef2f2;
            border-left: 6px solid #ef4444;
            color: #991b1b;
            padding: 14px 20px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .unverified-warning-banner {
            background-color: #fffbeb;
            border-left: 6px solid #f59e0b;
            color: #92400e;
            padding: 14px 20px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .real-mode-banner {
            background-color: #f0fdf4;
            border-left: 6px solid #22c55e;
            color: #166534;
            padding: 14px 20px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 20px;
        }

        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            text-align: center;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1e293b;
        }
        .metric-label {
            font-size: 0.95rem;
            font-weight: 500;
            color: #64748b;
        }

        .job-card {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 18px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        }
        .job-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 4px;
        }
        .job-meta {
            font-size: 0.95rem;
            color: #475569;
            margin-bottom: 12px;
        }
        .skill-pill {
            display: inline-block;
            background-color: #e0f2fe;
            color: #0369a1;
            padding: 4px 10px;
            border-radius: 16px;
            font-size: 0.82rem;
            font-weight: 600;
            margin: 2px;
        }
        .missing-skill-pill {
            display: inline-block;
            background-color: #fee2e2;
            color: #b91c1c;
            padding: 4px 10px;
            border-radius: 16px;
            font-size: 0.82rem;
            font-weight: 600;
            margin: 2px;
        }
        .matched-skill-pill {
            display: inline-block;
            background-color: #dcfce7;
            color: #15803d;
            padding: 4px 10px;
            border-radius: 16px;
            font-size: 0.82rem;
            font-weight: 600;
            margin: 2px;
        }
        </style>
    """, unsafe_allow_html=True)


SAMPLE_RESUMES = {
    "Data Scientist": (
        "Senior Data Scientist with 5 years of experience building predictive machine learning models, "
        "data pipelines, and AI solutions. Proficient in Python, Pandas, NumPy, Scikit-learn, SQL, and Tableau. "
        "Strong experience in NLP, Computer Vision, and statistical modeling. Education: M.S. in Data Science."
    ),
    "Java Developer": (
        "Java Software Engineer with 4 years of experience designing scalable microservices and web applications. "
        "Expertise in Java, Spring Boot, Hibernate, REST API, MySQL, and PostgreSQL. Familiar with Docker, Git, "
        "and Jenkins CI/CD pipelines."
    ),
    "DevOps Engineer": (
        "DevOps & Infrastructure Engineer with 6 years of experience automating cloud infrastructure and CI/CD pipelines. "
        "Proficient in Docker, Kubernetes, AWS, Terraform, Jenkins, Linux, Python, and Git. Strong focus on high availability "
        "and system monitoring."
    ),
    "Business Analyst": (
        "Results-oriented Business Analyst with 3 years of experience in requirements gathering, process modeling, "
        "and business intelligence. Proficient in SQL, Excel, Power BI, Tableau, Agile, Jira, and stakeholder management."
    )
}
