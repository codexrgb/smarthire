"""
Unit tests for Dataset Ingestion Framework and Experimental Evaluation routines.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.data.ingest_dataset import validate_dataset_schema, check_authentic_data_readiness
from src.experiments.baseline_evaluation import strip_synthetic_template_prefix
from src.experiments.clustering_evaluation import evaluate_knee_point, extract_top_cluster_terms
from sklearn.feature_extraction.text import TfidfVectorizer


def test_validate_dataset_schema_valid():
    """Organic DataFrame with required columns passes schema validation."""
    df = pd.DataFrame({
        "resume_text": [
            "Staff Platform Engineer with 8 years building Kubernetes operators in Go.",
            "Lead Frontend Architect specializing in React, Next.js, and web performance."
        ],
        "category": ["DevOps", "Frontend"]
    })
    is_valid, report = validate_dataset_schema(df, text_col="resume_text", label_col="category")
    assert is_valid is True
    assert report["is_valid"] is True
    assert report["unique_categories"] == 2


def test_validate_dataset_schema_missing_columns():
    """Missing required text or label column fails validation."""
    df = pd.DataFrame({"random_col": [1, 2, 3]})
    is_valid, report = validate_dataset_schema(df, text_col="resume_text", label_col="category")
    assert is_valid is False
    assert "resume_text" in report["missing_columns"]
    assert "category" in report["missing_columns"]


def test_validate_dataset_schema_rejects_synthetic_data():
    """Candidate dataset containing synthetic template patterns is rejected."""
    df = pd.DataFrame({
        "resume_text": [
            "Experienced Sales professional with 4 years of experience in industry projects. Worked on cross-functional teams to deliver high-quality solutions."
        ],
        "category": ["Sales"]
    })
    is_valid, report = validate_dataset_schema(df, text_col="resume_text", label_col="category")
    assert is_valid is False
    assert "synthetic" in report["error"].lower()


def test_strip_synthetic_template_prefix():
    """Prefix stripper removes the boilerplate template sentence."""
    text = (
        "Experienced Sales professional with 3 years of experience in industry projects. "
        "Education: MBA. Key skills: Negotiation, CRM."
    )
    stripped = strip_synthetic_template_prefix(text)
    assert not stripped.startswith("Experienced Sales professional")
    assert stripped.startswith("Education: MBA")


def test_evaluate_knee_point():
    """Evaluates discrete difference computation on inertia curves."""
    k_vals = [2, 3, 4, 5, 6]
    inertias = [100.0, 60.0, 45.0, 40.0, 38.0]  # Obvious elbow around K=3 or 4
    res = evaluate_knee_point(k_vals, inertias)
    assert res["suggested_elbow_k"] in [3, 4]
    assert res["max_second_difference"] > 0
    assert "assessment" in res


def test_authentic_data_readiness_blocked_by_default():
    """Without an authentic manifest, readiness reports BLOCKED."""
    readiness = check_authentic_data_readiness()
    assert "BLOCKED" in readiness["status_message"]
    assert readiness["authentic_data_available"] is False
