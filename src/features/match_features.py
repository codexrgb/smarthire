"""
Match Feature Generator & Heuristic Fit Score Calculator for SmartHire.
Computes transparent multi-factor ML Fit Scores.
"""

import re
import numpy as np
from typing import Dict, Any
from src.features.text_features import extract_skills, calculate_skill_match


def extract_experience_years(text: str) -> float:
    """Extracts numerical years of experience mentioned in text using regex."""
    if not text or not isinstance(text, str):
        return 0.0

    patterns = [
        r"(\d+)\s*\+?\s*(?:years?|yrs?)",
        r"(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)",
        r"experience\s*of\s*(\d+)\s*(?:years?|yrs?)"
    ]

    found_years = []
    text_lower = text.lower()

    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                nums = [float(n) for n in match if n.isdigit()]
                if nums:
                    found_years.append(np.mean(nums))
            elif isinstance(match, str) and match.isdigit():
                found_years.append(float(match))

    return max(found_years) if found_years else 0.0


def calculate_experience_compatibility(candidate_text: str, job_text: str) -> float:
    """Calculates experience compatibility ratio between 0.0 and 1.0."""
    cand_exp = extract_experience_years(candidate_text)
    job_exp = extract_experience_years(job_text)

    if job_exp == 0.0:
        return 1.0  # No explicit experience requirement specified in job

    if cand_exp >= job_exp:
        return 1.0  # Meets or exceeds requirement

    return round(cand_exp / job_exp, 2)


def compute_pair_match_features(
    resume_text: str,
    job_text: str,
    job_skills_str: str = "",
    text_sim_score: float = 0.0
) -> Dict[str, Any]:
    """
    Calculates feature set for candidate-job pair:

    Formula:
    fit_score = (0.50 * text_similarity + 0.30 * skill_overlap + 0.20 * experience_match) * 100

    Label: "ML-Based Fit Score"
    """
    cand_skills = extract_skills(resume_text)
    if job_skills_str and job_skills_str != "N/A":
        raw_job_skills = [s.strip() for s in job_skills_str.split(",") if s.strip()]
    else:
        raw_job_skills = extract_skills(job_text)

    skill_res = calculate_skill_match(cand_skills, raw_job_skills)
    skill_overlap = skill_res["match_percentage"] / 100.0

    exp_match = calculate_experience_compatibility(resume_text, job_text)

    # Transparent ML-Based Fit Score formula
    raw_fit = (0.50 * text_sim_score) + (0.30 * skill_overlap) + (0.20 * exp_match)
    fit_score = round(raw_fit * 100.0, 2)

    return {
        "text_similarity": round(text_sim_score, 4),
        "skill_overlap": round(skill_overlap, 4),
        "experience_match": round(exp_match, 4),
        "fit_score": fit_score,
        "score_label": "ML-Based Fit Score"
    }
