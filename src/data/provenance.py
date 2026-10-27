"""
Dataset Provenance & Authenticity Verification Module for SmartHire 2.0.

Provides rigorous provenance checks, synthetic signature detection, cryptographic
manifest verification, and explicit demo-mode classification.

Rules:
1. Never infer authenticity from a filename alone.
2. Synthetic data is identified through reliable generation markers and template signatures.
3. Unknown datasets lacking verified cryptographic provenance are classified as UNKNOWN_UNVERIFIED.
4. "REAL DATA MODE ACTIVE" is NEVER displayed unless provenance is cryptographically verified.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, DEMO_WARNING_MESSAGE

# Provenance Status Constants
STATUS_DEMO_SYNTHETIC = "demo_synthetic"
STATUS_UNKNOWN_UNVERIFIED = "unknown_unverified"
STATUS_VERIFIED_AUTHENTIC = "verified_authentic"

# Known Synthetic Signatures
SYNTHETIC_RESUME_TEMPLATE_RE = re.compile(
    r"(?i)^experienced\s+.+\s+professional\s+with\s+\d+\s+years\s+of\s+experience\s+in\s+industry\s+projects",
    re.MULTILINE
)
SYNTHETIC_RESUME_BOILERPLATE = "worked on cross-functional teams to deliver high-quality solutions"
SYNTHETIC_JOB_TEMPLATE_RE = re.compile(
    r"(?i)^we\s+are\s+hiring\s+a\s+.+\s+at\s+.+\s+located\s+in",
    re.MULTILINE
)
SYNTHETIC_JOB_BOILERPLATE = "key responsibilities include designing, developing, and maintaining systems in"


def compute_file_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def detect_synthetic_signatures(df: pd.DataFrame, text_cols: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Scans a DataFrame for known synthetic generation templates and markers.

    Returns:
        Tuple[bool, List[str]]: (is_synthetic, detected_reasons)
    """
    if df is None or df.empty:
        return False, []

    reasons = []

    # Check explicit column markers
    for col in df.columns:
        if str(col).lower() in ["is_synthetic", "synthetic_flag", "is_demo"]:
            if (df[col] == True).any() or (df[col] == 1).any():
                reasons.append(f"Explicit synthetic column '{col}' detected.")

    # Determine candidate text columns to check
    if not text_cols:
        candidate_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["resume", "text", "description", "details", "summary"])]
        if not candidate_cols:
            candidate_cols = [c for c in df.columns if df[c].dtype == object]
    else:
        candidate_cols = [c for c in text_cols if c in df.columns]

    for col in candidate_cols:
        sample_series = df[col].dropna().astype(str).head(100)
        if sample_series.empty:
            continue

        # Check resume template prefix
        matches_res = sample_series.apply(lambda s: bool(SYNTHETIC_RESUME_TEMPLATE_RE.search(s.strip()))).sum()
        if matches_res > 0 and (matches_res / len(sample_series)) >= 0.10:
            reasons.append(
                f"Synthetic resume template ('Experienced <Category> professional with X years...') "
                f"matched in {matches_res}/{len(sample_series)} samples ({matches_res/len(sample_series)*100:.1f}%) in column '{col}'."
            )

        # Check resume boilerplate suffix
        matches_res_bp = sample_series.apply(lambda s: SYNTHETIC_RESUME_BOILERPLATE in s.lower()).sum()
        if matches_res_bp > 0 and (matches_res_bp / len(sample_series)) >= 0.10:
            reasons.append(
                f"Synthetic resume boilerplate phrase matched in {matches_res_bp}/{len(sample_series)} "
                f"samples in column '{col}'."
            )

        # Check job template prefix
        matches_job = sample_series.apply(lambda s: bool(SYNTHETIC_JOB_TEMPLATE_RE.search(s.strip()))).sum()
        if matches_job > 0 and (matches_job / len(sample_series)) >= 0.10:
            reasons.append(
                f"Synthetic job posting template ('We are hiring a <Role> at <Company> located in...') "
                f"matched in {matches_job}/{len(sample_series)} samples ({matches_job/len(sample_series)*100:.1f}%) in column '{col}'."
            )

        # Check job boilerplate phrase
        matches_job_bp = sample_series.apply(lambda s: SYNTHETIC_JOB_BOILERPLATE in s.lower()).sum()
        if matches_job_bp > 0 and (matches_job_bp / len(sample_series)) >= 0.10:
            reasons.append(
                f"Synthetic job description boilerplate matched in {matches_job_bp}/{len(sample_series)} "
                f"samples in column '{col}'."
            )

    is_synthetic = len(reasons) > 0
    return is_synthetic, reasons


def check_manifest_verification(
    file_path: Path,
    manifest_path: Optional[Path] = None
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Verifies a file against a cryptographic provenance manifest.

    Returns:
        Tuple[bool, Optional[Dict], str]: (is_verified, manifest_record, reason)
    """
    if manifest_path is None:
        # Check standard manifest locations
        manifest_locations = [
            file_path.parent / "provenance_manifest.json",
            file_path.parent / "provenance.json",
            RAW_DATA_DIR / "provenance_manifest.json",
            RAW_DATA_DIR / "provenance.json"
        ]
        manifest_path = next((p for p in manifest_locations if p.exists()), None)

    if not manifest_path or not manifest_path.exists():
        return False, None, "No cryptographic provenance manifest found."

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        return False, None, f"Failed to parse provenance manifest at {manifest_path}: {e}"

    datasets_meta = manifest.get("datasets", {})
    file_key = file_path.name

    if file_key not in datasets_meta:
        return False, None, f"File '{file_key}' not registered in provenance manifest."

    record = datasets_meta[file_key]
    expected_sha256 = record.get("sha256", "").lower().strip()
    actual_sha256 = compute_file_sha256(file_path).lower().strip()

    if not expected_sha256:
        return False, record, f"Manifest record for '{file_key}' lacks 'sha256' field."

    if expected_sha256 != actual_sha256:
        return False, record, f"SHA-256 mismatch for '{file_key}': expected {expected_sha256}, got {actual_sha256}."

    # Must contain verified source and legal license
    source = record.get("source", "").strip()
    license_info = record.get("license", "").strip()
    is_authentic = record.get("is_authentic", False)

    if not source or not license_info or not is_authentic:
        return False, record, f"Manifest record for '{file_key}' has missing or uncertified authenticity fields."

    return True, record, "Cryptographically verified against provenance manifest."


def inspect_file_provenance(file_path: Path, manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Inspects a single dataset file for provenance, returning status and metadata.
    """
    if not file_path.exists():
        return {
            "file": file_path.name,
            "status": "missing",
            "is_demo_mode": True,
            "reasons": ["File does not exist."]
        }

    # Step 1: Scan for synthetic generation signatures
    try:
        df = pd.read_csv(file_path, nrows=200)
        is_synthetic, synthetic_reasons = detect_synthetic_signatures(df)
    except Exception as e:
        return {
            "file": file_path.name,
            "status": STATUS_UNKNOWN_UNVERIFIED,
            "is_demo_mode": True,
            "reasons": [f"Could not read CSV file: {e}"]
        }

    if is_synthetic:
        return {
            "file": file_path.name,
            "status": STATUS_DEMO_SYNTHETIC,
            "is_demo_mode": True,
            "reasons": synthetic_reasons,
            "sha256": compute_file_sha256(file_path)
        }

    # Step 2: If no synthetic signatures found, check cryptographic manifest
    is_verified, record, manifest_msg = check_manifest_verification(file_path, manifest_path)
    if is_verified:
        return {
            "file": file_path.name,
            "status": STATUS_VERIFIED_AUTHENTIC,
            "is_demo_mode": False,
            "reasons": [manifest_msg],
            "sha256": record.get("sha256"),
            "source": record.get("source"),
            "license": record.get("license"),
            "acquisition_date": record.get("acquisition_date")
        }

    # Step 3: Unverified/Unknown data (never infer authenticity from filename!)
    return {
        "file": file_path.name,
        "status": STATUS_UNKNOWN_UNVERIFIED,
        "is_demo_mode": True,
        "reasons": [manifest_msg, "Dataset authenticity cannot be inferred from filename or structure alone."],
        "sha256": compute_file_sha256(file_path)
    }


def assess_repository_datasets(raw_dir: Path = RAW_DATA_DIR) -> Dict[str, Any]:
    """
    Conducts a comprehensive provenance audit across all raw datasets in raw_dir.
    Determines overall system dataset mode:
      - STATUS_DEMO_SYNTHETIC
      - STATUS_UNKNOWN_UNVERIFIED
      - STATUS_VERIFIED_AUTHENTIC
    """
    expected_files = [
        "UpdatedResumeDataSet.csv",
        "naukri_com-job_sample.csv",
        "linkedin_job_postings.csv"
    ]

    file_results = {}
    any_synthetic = False
    any_unverified = False
    all_verified = True

    for fname in expected_files:
        fpath = raw_dir / fname
        res = inspect_file_provenance(fpath)
        file_results[fname] = res

        if res["status"] == STATUS_DEMO_SYNTHETIC:
            any_synthetic = True
            all_verified = False
        elif res["status"] in [STATUS_UNKNOWN_UNVERIFIED, "missing"]:
            any_unverified = True
            all_verified = False

    if any_synthetic:
        overall_status = STATUS_DEMO_SYNTHETIC
        is_demo_mode = True
        ui_badge = "DEMO / SYNTHETIC"
        banner_msg = "⚠️ DEMO MODE ACTIVE: Synthetic template data detected. These metrics must not be used as final project results."
    elif all_verified:
        overall_status = STATUS_VERIFIED_AUTHENTIC
        is_demo_mode = False
        ui_badge = "VERIFIED AUTHENTIC"
        banner_msg = "🟢 VERIFIED DATA MODE ACTIVE: All datasets verified via cryptographic provenance manifest."
    else:
        overall_status = STATUS_UNKNOWN_UNVERIFIED
        is_demo_mode = True
        ui_badge = "UNVERIFIED DATASET"
        banner_msg = "⚠️ UNVERIFIED DATASET: Dataset provenance has not been cryptographically verified. Results cannot be certified."

    return {
        "overall_status": overall_status,
        "is_demo_mode": is_demo_mode,
        "ui_badge": ui_badge,
        "banner_message": banner_msg,
        "file_assessments": file_results
    }
