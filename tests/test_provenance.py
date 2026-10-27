"""
Unit tests for dataset provenance, synthetic signature detection, and demo-mode integrity.
Tests synthetic, verified, and unknown-provenance cases.
"""

import json
import pytest
import pandas as pd
from pathlib import Path

from src.data.provenance import (
    STATUS_DEMO_SYNTHETIC,
    STATUS_UNKNOWN_UNVERIFIED,
    STATUS_VERIFIED_AUTHENTIC,
    detect_synthetic_signatures,
    inspect_file_provenance,
    assess_repository_datasets,
    compute_file_sha256,
    check_manifest_verification
)
from src.data.load_data import check_real_datasets_exist
from src.config import RAW_DATA_DIR


def test_detect_synthetic_resumes_signature():
    """Detects synthetic resume template phrases."""
    synthetic_resumes = pd.DataFrame({
        "Resume_str": [
            "Experienced Sales professional with 3 years of experience in industry projects. Education: MBA. Worked on cross-functional teams to deliver high-quality solutions.",
            "Experienced Java Developer professional with 5 years of experience in industry projects. Education: B.Tech in Computer Science. Worked on cross-functional teams to deliver high-quality solutions.",
            "Experienced Data Science professional with 7 years of experience in industry projects. Education: M.S. in Data Science. Worked on cross-functional teams to deliver high-quality solutions."
        ]
    })
    is_synth, reasons = detect_synthetic_signatures(synthetic_resumes)
    assert is_synth is True
    assert len(reasons) > 0
    assert any("template" in r.lower() for r in reasons)


def test_detect_synthetic_jobs_signature():
    """Detects synthetic job posting template phrases."""
    synthetic_jobs = pd.DataFrame({
        "job_description": [
            "We are hiring a Sales - Lead at TechCorp located in Seattle, WA. The ideal candidate must have 3 to 5 years of experience. Key responsibilities include designing, developing, and maintaining systems in Sales domain.",
            "We are hiring a Java Developer at InfoSys located in Boston, MA. The ideal candidate must have 2 to 4 years of experience. Key responsibilities include designing, developing, and maintaining systems in Java Developer domain."
        ]
    })
    is_synth, reasons = detect_synthetic_signatures(synthetic_jobs)
    assert is_synth is True
    assert len(reasons) > 0


def test_organic_data_no_synthetic_signature():
    """Organic resume text does not trigger synthetic signature detection."""
    organic_resumes = pd.DataFrame({
        "resume_text": [
            "Alex Smith | Senior Systems Architect. Over a decade leading cloud migration projects at scale. Deep expertise in distributed systems, Rust, and event-driven architectures.",
            "Elena Rostova — Machine Learning Researcher. Published in NeurIPS and ICML on diffusion models and geometric deep learning. Ph.D. in Computer Science."
        ]
    })
    is_synth, reasons = detect_synthetic_signatures(organic_resumes)
    assert is_synth is False
    assert len(reasons) == 0


def test_unknown_provenance_is_not_classified_as_authentic(tmp_path):
    """An unknown CSV without synthetic signatures and without manifest is classified as UNKNOWN_UNVERIFIED, NEVER authentic."""
    unknown_csv = tmp_path / "unknown_dataset.csv"
    pd.DataFrame({
        "resume_text": ["Independent consultant specializing in enterprise cybersecurity auditing and threat modeling."],
        "category": ["Cybersecurity"]
    }).to_csv(unknown_csv, index=False)

    res = inspect_file_provenance(unknown_csv)
    assert res["status"] == STATUS_UNKNOWN_UNVERIFIED
    assert res["is_demo_mode"] is True
    assert any("cannot be inferred" in r.lower() for r in res["reasons"])


def test_verified_authentic_provenance_with_valid_manifest(tmp_path):
    """A dataset with a valid manifest and matching SHA256 is classified as VERIFIED_AUTHENTIC."""
    dataset_file = tmp_path / "genuine_resumes.csv"
    pd.DataFrame({
        "resume_text": ["Staff Engineer with background in distributed transactions, Raft consensus, and Go."],
        "category": ["Systems Engineering"]
    }).to_csv(dataset_file, index=False)

    actual_hash = compute_file_sha256(dataset_file)

    manifest_file = tmp_path / "provenance_manifest.json"
    manifest_data = {
        "datasets": {
            "genuine_resumes.csv": {
                "sha256": actual_hash,
                "source": "https://example.org/curated_research_dataset",
                "license": "CC-BY-4.0",
                "acquisition_date": "2026-10-26",
                "is_authentic": True
            }
        }
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    res = inspect_file_provenance(dataset_file, manifest_path=manifest_file)
    assert res["status"] == STATUS_VERIFIED_AUTHENTIC
    assert res["is_demo_mode"] is False
    assert res["license"] == "CC-BY-4.0"


def test_manifest_tamper_detection(tmp_path):
    """If the file content differs from the manifest SHA256, it is rejected and classified as UNKNOWN_UNVERIFIED."""
    dataset_file = tmp_path / "tampered_resumes.csv"
    pd.DataFrame({
        "resume_text": ["Valid initial text."],
        "category": ["Engineering"]
    }).to_csv(dataset_file, index=False)

    manifest_file = tmp_path / "provenance_manifest.json"
    manifest_data = {
        "datasets": {
            "tampered_resumes.csv": {
                "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "source": "https://example.org/curated_research_dataset",
                "license": "CC-BY-4.0",
                "is_authentic": True
            }
        }
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    res = inspect_file_provenance(dataset_file, manifest_path=manifest_file)
    assert res["status"] == STATUS_UNKNOWN_UNVERIFIED
    assert res["is_demo_mode"] is True
    assert any("mismatch" in r.lower() for r in res["reasons"])


def test_repository_raw_data_correctly_identified_as_synthetic():
    """Validates that current raw datasets are correctly identified as DEMO_SYNTHETIC."""
    assessment = assess_repository_datasets(RAW_DATA_DIR)
    assert assessment["overall_status"] == STATUS_DEMO_SYNTHETIC
    assert assessment["is_demo_mode"] is True
    assert "DEMO" in assessment["ui_badge"]
    assert "synthetic" in assessment["banner_message"].lower()

    # check_real_datasets_exist must return False
    all_verified, reasons = check_real_datasets_exist(RAW_DATA_DIR)
    assert all_verified is False
    assert len(reasons) > 0
