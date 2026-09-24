"""
Data Loading, Schema Normalizer, and Data Quality Pipeline for SmartHire.
Handles dynamic column matching, real dataset discovery vs. demo mode fallback, and dataset normalization.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from src.config import (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, COLUMN_ALIASES, DEMO_WARNING_MESSAGE
)
from src.data.preprocess import clean_text
from src.data.generate_sample_data import ensure_sample_datasets_exist


def check_real_datasets_exist(raw_dir: Path = RAW_DATA_DIR) -> Tuple[bool, List[str]]:
    """
    Checks whether required real public datasets exist in data/raw/.

    Required files:
    - UpdatedResumeDataSet.csv
    - naukri_com-job_sample.csv
    - linkedin_job_postings.csv

    Returns:
        Tuple[bool, List[str]]: (all_exist, missing_files_list)
    """
    required_files = [
        "UpdatedResumeDataSet.csv",
        "naukri_com-job_sample.csv",
        "linkedin_job_postings.csv"
    ]
    missing = []
    for fname in required_files:
        if not (raw_dir / fname).exists():
            missing.append(fname)

    all_exist = len(missing) == 0
    return all_exist, missing


def detect_column(df: pd.DataFrame, target_concept: str) -> Optional[str]:
    """
    Detects which column in df corresponds to target_concept using COLUMN_ALIASES.
    """
    if target_concept not in COLUMN_ALIASES:
        return None

    df_cols = [str(c) for c in df.columns]
    aliases = COLUMN_ALIASES[target_concept]

    # Exact case-insensitive match
    for alias in aliases:
        for col in df_cols:
            if col.strip().lower() == alias.strip().lower():
                return col

    # Partial match fallback
    for alias in aliases:
        for col in df_cols:
            if alias.strip().lower() in col.strip().lower():
                return col

    return None


def standardize_job_df(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Normalizes job dataframe into standard schema."""
    std_df = pd.DataFrame()

    title_col = detect_column(df, "title")
    company_col = detect_column(df, "company")
    loc_col = detect_column(df, "location")
    skills_col = detect_column(df, "skills")
    exp_col = detect_column(df, "experience")
    sal_col = detect_column(df, "salary")
    desc_col = detect_column(df, "description")
    cat_col = detect_column(df, "category")

    std_df["title"] = df[title_col].astype(str) if title_col else "N/A"
    std_df["company"] = df[company_col].astype(str) if company_col else "N/A"
    std_df["location"] = df[loc_col].astype(str) if loc_col else "N/A"
    std_df["skills"] = df[skills_col].astype(str) if skills_col else "N/A"
    std_df["experience"] = df[exp_col].astype(str) if exp_col else "N/A"
    std_df["salary"] = df[sal_col].astype(str) if sal_col else "N/A"
    std_df["description"] = df[desc_col].astype(str) if desc_col else "N/A"
    std_df["category"] = df[cat_col].astype(str) if cat_col else "General"
    std_df["source"] = source_name

    return std_df


def load_raw_resumes(raw_dir: Path = RAW_DATA_DIR) -> Tuple[pd.DataFrame, bool]:
    """
    Loads raw resume datasets.
    If real datasets are missing, falls back to demo synthetic data and warns.
    """
    real_exist, missing = check_real_datasets_exist(raw_dir)
    is_demo = not real_exist

    if is_demo:
        print("\n" + "="*70)
        print("Required datasets are missing from data/raw/. Add the datasets and run training again.")
        print(f"Missing: {missing}")
        print(f"⚠️ {DEMO_WARNING_MESSAGE}")
        print("="*70 + "\n")
        ensure_sample_datasets_exist()

    csv_files = list(raw_dir.glob("*.csv"))
    resume_dfs = []

    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
            res_col = detect_column(df, "resume_text")
            cat_col = detect_column(df, "category")

            if res_col:
                res_df = pd.DataFrame()
                res_df["resume_text"] = df[res_col].astype(str)
                res_df["category"] = df[cat_col].astype(str) if cat_col else "General"
                res_df["source"] = csv_path.name
                resume_dfs.append(res_df)
        except Exception as e:
            print(f"[DATA LOADER WARNING] Could not parse resume CSV {csv_path.name}: {e}")

    if not resume_dfs:
        raise FileNotFoundError(f"No resume CSV datasets found in {raw_dir}")

    combined = pd.concat(resume_dfs, ignore_index=True)
    return combined, is_demo


def load_raw_jobs(raw_dir: Path = RAW_DATA_DIR) -> Tuple[pd.DataFrame, bool]:
    """
    Loads raw job listing datasets.
    """
    real_exist, _ = check_real_datasets_exist(raw_dir)
    is_demo = not real_exist

    if is_demo:
        ensure_sample_datasets_exist()

    csv_files = list(raw_dir.glob("*.csv"))
    job_dfs = []

    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
            title_col = detect_column(df, "title")
            desc_col = detect_column(df, "description")

            if title_col or desc_col:
                std_job = standardize_job_df(df, source_name=csv_path.name)
                job_dfs.append(std_job)
        except Exception as e:
            print(f"[DATA LOADER WARNING] Could not parse job CSV {csv_path.name}: {e}")

    if not job_dfs:
        raise FileNotFoundError(f"No job posting CSV datasets found in {raw_dir}")

    combined = pd.concat(job_dfs, ignore_index=True)
    return combined, is_demo


def clean_and_normalize_data(raw_dir: Path = RAW_DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, bool]:
    """
    Ingests, cleans, deduplicates, and standardizes resume and job datasets.
    Reports counts before and after cleaning.
    """
    resumes_raw, is_demo_res = load_raw_resumes(raw_dir)
    jobs_raw, is_demo_job = load_raw_jobs(raw_dir)
    is_demo_mode = is_demo_res or is_demo_job

    # --- Clean Resumes ---
    res_before = len(resumes_raw)
    res_df = resumes_raw.dropna(subset=["resume_text"]).copy()
    res_df["resume_text"] = res_df["resume_text"].astype(str).str.strip()
    res_df = res_df[res_df["resume_text"] != ""]
    res_df = res_df[res_df["resume_text"] != "nan"]
    res_df.drop_duplicates(subset=["resume_text"], inplace=True)
    res_after = len(res_df)

    res_df["resume_id"] = [f"RES_{i+1:04d}" for i in range(res_after)]
    res_df["clean_text"] = res_df["resume_text"].apply(clean_text)
    res_df = res_df[["resume_id", "resume_text", "category", "clean_text", "source"]]

    print(f"[DATA CLEANING] Resumes Record Count: {res_before} before -> {res_after} after cleaning.")

    # --- Clean Jobs ---
    jobs_before = len(jobs_raw)
    job_df = jobs_raw.copy()

    # Replace empty/nan strings with N/A
    for col in ["title", "company", "location", "skills", "experience", "salary", "description"]:
        job_df[col] = job_df[col].astype(str).str.strip()
        job_df[col] = job_df[col].replace(["", "nan", "None", "null"], "N/A")

    # Filter out records where both title and description are N/A
    job_df = job_df[(job_df["title"] != "N/A") | (job_df["description"] != "N/A")]
    job_df.drop_duplicates(subset=["title", "company", "description"], inplace=True)
    jobs_after = len(job_df)

    job_df["job_id"] = [f"JOB_{i+1:04d}" for i in range(jobs_after)]

    # Searchable clean description combining title, skills, description
    job_df["full_search_text"] = (
        job_df["title"].replace("N/A", "") + " " +
        job_df["description"].replace("N/A", "") + " " +
        job_df["skills"].replace("N/A", "")
    )
    job_df["clean_description"] = job_df["full_search_text"].apply(clean_text)

    cols_order = ["job_id", "title", "company", "location", "skills", "experience", "salary", "description", "clean_description", "category", "source"]
    job_df = job_df[cols_order]

    print(f"[DATA CLEANING] Jobs Record Count: {jobs_before} before -> {jobs_after} after cleaning.")

    return res_df, job_df, is_demo_mode


def save_processed_datasets(res_df: pd.DataFrame, job_df: pd.DataFrame, out_dir: Path = PROCESSED_DATA_DIR):
    """Saves cleaned datasets to data/processed/."""
    out_dir.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(out_dir / "resumes.csv", index=False)
    job_df.to_csv(out_dir / "jobs.csv", index=False)
    # Also save backwards-compatible aliases if needed
    res_df.to_csv(out_dir / "processed_resumes.csv", index=False)
    job_df.to_csv(out_dir / "processed_jobs.csv", index=False)
    print(f"[DATA SAVE] Saved normalized datasets to {out_dir}/resumes.csv and {out_dir}/jobs.csv")
