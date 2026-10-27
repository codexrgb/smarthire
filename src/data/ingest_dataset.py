"""
Authentic Dataset Ingestion & Validation Framework for SmartHire 2.0.

Provides strict ingestion, validation, PII redaction, and cryptographic provenance
registration for importing authentic, legally usable resume datasets.

Rules:
1. Raw data files are treated as strictly immutable (read-only).
2. Cleaned data is written to a dedicated location (data/verified_processed/).
3. PII (emails, phone numbers) is redacted from diagnostic logs and processed text.
4. If authentic data is unavailable, the pipeline reports that authentic evaluation is blocked.
5. Never fabricates resumes or labels to fill gaps.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR, RAW_DATA_DIR
from src.data.preprocess import clean_text
from src.data.provenance import (
    compute_file_sha256,
    detect_synthetic_signatures,
    STATUS_DEMO_SYNTHETIC,
    STATUS_VERIFIED_AUTHENTIC,
    STATUS_UNKNOWN_UNVERIFIED
)
from src.utils.security import redact_pii

VERIFIED_PROCESSED_DIR = DATA_DIR / "verified_processed"
DEFAULT_MANIFEST_PATH = DATA_DIR / "provenance_manifest.json"


def validate_dataset_schema(
    df: pd.DataFrame,
    text_col: str = "resume_text",
    label_col: str = "category"
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates required columns, checks for missing values, and checks for duplicates.
    """
    report = {
        "is_valid": False,
        "total_rows": len(df),
        "text_column": text_col,
        "label_column": label_col,
        "missing_columns": [],
        "null_counts": {},
        "empty_text_count": 0,
        "duplicate_text_count": 0,
        "unique_categories": 0,
        "synthetic_detection": None
    }

    if text_col not in df.columns:
        report["missing_columns"].append(text_col)
    if label_col not in df.columns:
        report["missing_columns"].append(label_col)

    if report["missing_columns"]:
        return False, report

    # Nulls & empties
    report["null_counts"] = {col: int(df[col].isna().sum()) for col in [text_col, label_col]}
    valid_text = df[text_col].dropna().astype(str).str.strip()
    report["empty_text_count"] = int((valid_text == "").sum())

    # Duplicates
    report["duplicate_text_count"] = int(df[text_col].duplicated().sum())
    report["unique_categories"] = int(df[label_col].nunique())

    # Synthetic signature scan
    is_synth, synth_reasons = detect_synthetic_signatures(df, text_cols=[text_col])
    report["synthetic_detection"] = {
        "is_synthetic": is_synth,
        "reasons": synth_reasons
    }

    if is_synth:
        report["error"] = "Dataset rejected: Synthetic template signatures detected."
        return False, report

    if len(valid_text) == 0:
        report["error"] = "Dataset rejected: No non-empty text records found."
        return False, report

    report["is_valid"] = True
    return True, report


def ingest_authentic_dataset(
    input_file: Path,
    source: str,
    license_type: str,
    text_col: str = "resume_text",
    label_col: str = "category",
    output_dir: Path = VERIFIED_PROCESSED_DIR,
    manifest_path: Path = DEFAULT_MANIFEST_PATH
) -> Dict[str, Any]:
    """
    Ingests, validates, redacts PII, and registers an authentic dataset into the provenance manifest.
    Raw input file remains completely unchanged.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found at: {input_file}")

    print(f"[INGESTION] Reading candidate dataset: {input_file.name}...")
    df = pd.read_csv(input_file)

    # Validate Schema and Authenticity
    is_valid, validation_report = validate_dataset_schema(df, text_col=text_col, label_col=label_col)
    if not is_valid:
        print(f"[INGESTION ERROR] Validation failed: {validation_report.get('error', 'Schema invalid')}")
        return {"status": "failed", "validation": validation_report}

    print(f"[INGESTION] Validated {len(df)} records across {validation_report['unique_categories']} categories.")

    # Deduplicate and Cleanse
    clean_df = df.dropna(subset=[text_col]).copy()
    clean_df[text_col] = clean_df[text_col].astype(str).str.strip()
    clean_df = clean_df[clean_df[text_col] != ""]
    clean_df = clean_df.drop_duplicates(subset=[text_col])

    # Redact PII in text and generate cleaned tokens
    print("[INGESTION] Applying PII redaction and technical token normalization...")
    clean_df["redacted_text"] = clean_df[text_col].apply(redact_pii)
    clean_df["clean_text"] = clean_df["redacted_text"].apply(clean_text)
    clean_df["resume_id"] = [f"VER_RES_{i+1:04d}" for i in range(len(clean_df))]

    # Save to verified processed directory (leaving raw files untouched)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"verified_{input_file.name}"
    clean_df[["resume_id", "redacted_text", label_col, "clean_text"]].to_csv(out_file, index=False)
    print(f"[INGESTION] Saved verified processed dataset ({len(clean_df)} records) to: {out_file}")

    # Compute SHA-256 of raw file for manifest
    raw_sha256 = compute_file_sha256(input_file)

    # Update Provenance Manifest
    manifest_data = {"datasets": {}}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception:
            manifest_data = {"datasets": {}}

    manifest_data["datasets"][input_file.name] = {
        "sha256": raw_sha256,
        "source": source,
        "license": license_type,
        "records_count": len(clean_df),
        "is_authentic": True,
        "processed_path": str(out_file.relative_to(PROJECT_ROOT))
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"[INGESTION] Registered provenance in {manifest_path.name}")
    return {
        "status": "success",
        "raw_sha256": raw_sha256,
        "records_processed": len(clean_df),
        "output_file": str(out_file),
        "validation": validation_report
    }


def check_authentic_data_readiness() -> Dict[str, Any]:
    """
    Checks whether verified authentic resume data is available for certified retraining.
    If not, reports that evaluation on real resumes remains blocked.
    """
    manifest_path = DEFAULT_MANIFEST_PATH
    has_verified = False
    verified_files = []

    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for fname, meta in data.get("datasets", {}).items():
                    if meta.get("is_authentic") is True:
                        has_verified = True
                        verified_files.append(fname)
        except Exception:
            has_verified = False

    return {
        "authentic_data_available": has_verified,
        "verified_files": verified_files,
        "status_message": (
            "Authentic dataset verified and ready for production model training."
            if has_verified
            else "BLOCKED: No authentic, verified dataset has been ingested. "
                 "Production evaluation on real resumes remains blocked until legitimate data is provided."
        )
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartHire 2.0 Dataset Ingestion & Validation Framework")
    parser.add_argument("--check-status", action="store_true", help="Check if authentic dataset is ready")
    parser.add_argument("--input", type=str, help="Path to raw candidate CSV file")
    parser.add_argument("--source", type=str, help="Source URL or academic citation")
    parser.add_argument("--license", type=str, help="License type (e.g., CC-BY-4.0, MIT, ODC-By)")
    parser.add_argument("--text-col", type=str, default="resume_text", help="Name of text column")
    parser.add_argument("--label-col", type=str, default="category", help="Name of category label column")

    args = parser.parse_args()

    if args.check_status:
        res = check_authentic_data_readiness()
        print(f"Status: {res['status_message']}")
        print(f"Verified files: {res['verified_files']}")
    elif args.input:
        if not args.source or not args.license:
            print("Error: --source and --license are mandatory for provenance registration.")
            sys.exit(1)
        res = ingest_authentic_dataset(
            input_file=Path(args.input),
            source=args.source,
            license_type=args.license,
            text_col=args.text_col,
            label_col=args.label_col
        )
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()
