"""
Unit and integration tests for the SmartHire resume-to-job recommendation pipeline.
Tests ranking order, empty resumes, missing skills, and relevant vs. irrelevant job descriptions.
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from src.backend.main import app
from src.features.text_features import extract_skills, calculate_skill_match
from src.features.match_features import compute_pair_match_features
from src.models.recommender import recommend_jobs, build_job_recommender


@pytest.fixture
def sample_jobs_df():
    """Provides a controlled multi-role job dataset for recommendation tests."""
    return pd.DataFrame([
        {
            "job_id": "JOB_DATA_01",
            "title": "Senior Data Scientist",
            "company": "Alpha Analytics",
            "location": "Remote",
            "skills": "Python, SQL, Machine Learning, Pandas, PyTorch",
            "experience": "3-5 years",
            "salary": "$130k",
            "category": "Data Science",
            "description": "We are seeking a Senior Data Scientist skilled in Python, SQL, Machine Learning, and PyTorch for predictive modeling.",
            "clean_description": "we are seeking a senior data scientist skilled in python sql machine learning and pytorch for predictive modeling"
        },
        {
            "job_id": "JOB_JAVA_01",
            "title": "Java Developer",
            "company": "Vanguard Systems",
            "location": "New York, NY",
            "skills": "Java, Spring Boot, MySQL, Git",
            "experience": "2-4 years",
            "salary": "$115k",
            "category": "Java Developer",
            "description": "Hiring a Java Developer with experience in Java, Spring Boot, MySQL, and Git for microservices development.",
            "clean_description": "hiring a java developer with experience in java spring boot mysql and git for microservices development"
        },
        {
            "job_id": "JOB_LEGAL_01",
            "title": "Corporate Advocate",
            "company": "Apex Legal",
            "location": "Chicago, IL",
            "skills": "Legal Drafting, Corporate Law, Litigation, Compliance",
            "experience": "4-8 years",
            "salary": "$125k",
            "category": "Advocate",
            "description": "Corporate Advocate needed for commercial litigation, compliance, contract negotiation, and dispute arbitration.",
            "clean_description": "corporate advocate needed for commercial litigation compliance contract negotiation and dispute arbitration"
        },
        {
            "job_id": "JOB_MECH_01",
            "title": "Mechanical Engineer",
            "company": "TechCorp Solutions",
            "location": "Austin, TX",
            "skills": "CAD, SolidWorks, AutoCAD, Thermodynamics",
            "experience": "2-6 years",
            "salary": "$95k",
            "category": "Mechanical Engineer",
            "description": "Mechanical Engineer required for thermodynamics simulations, CAD modeling, and manufacturing tolerances.",
            "clean_description": "mechanical engineer required for thermodynamics simulations cad modeling and manufacturing tolerances"
        }
    ])


# ==============================================================================
# 1. RANKING ORDER TESTS
# ==============================================================================

def test_recommender_ranking_order(sample_jobs_df):
    """
    Verifies that returned recommendations are strictly ordered descending by
    ml_fit_score (and similarity_score as tiebreaker).
    """
    resume = (
        "Experienced Data Scientist with 4 years building machine learning pipelines, "
        "expert in Python, SQL, Pandas, and PyTorch."
    )
    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    recs = recommend_jobs(resume, sample_jobs_df, vectorizer=vec, job_vectors=vecs, top_n=4)

    assert len(recs) == 4
    scores = recs["ml_fit_score"].tolist()
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], f"Ranking inverted at index {i}: {scores[i]} < {scores[i+1]}"

    # Tiebreaker test with identical fit scores
    for i in range(len(recs) - 1):
        if recs["ml_fit_score"].iloc[i] == recs["ml_fit_score"].iloc[i + 1]:
            assert recs["similarity_score"].iloc[i] >= recs["similarity_score"].iloc[i + 1]


def test_recommender_top_n_truncation(sample_jobs_df):
    """Verifies that top_n parameter truncates result count correctly."""
    resume = "Software engineer with Python and Java background."
    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    recs_2 = recommend_jobs(resume, sample_jobs_df, vectorizer=vec, job_vectors=vecs, top_n=2)
    assert len(recs_2) == 2


# ==============================================================================
# 2. EMPTY AND MALFORMED RESUMES TESTS
# ==============================================================================

def test_recommender_empty_resume(sample_jobs_df):
    """Verifies that an empty resume string returns an empty DataFrame."""
    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    recs = recommend_jobs("", sample_jobs_df, vectorizer=vec, job_vectors=vecs)
    assert isinstance(recs, pd.DataFrame)
    assert len(recs) == 0
    assert recs.empty


def test_recommender_whitespace_only_resume(sample_jobs_df):
    """Verifies that whitespace-only resume returns an empty DataFrame."""
    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    recs = recommend_jobs("    \t\n  \r\n   ", sample_jobs_df, vectorizer=vec, job_vectors=vecs)
    assert isinstance(recs, pd.DataFrame)
    assert recs.empty


def test_recommender_punctuation_only_resume(sample_jobs_df):
    """
    Verifies that a resume consisting purely of punctuation symbols
    (which clean_text strips to empty) returns an empty DataFrame.
    """
    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    recs = recommend_jobs("... --- !!! ??? ,,, ;;;", sample_jobs_df, vectorizer=vec, job_vectors=vecs)
    assert isinstance(recs, pd.DataFrame)
    assert recs.empty


def test_recommender_empty_jobs_dataframe():
    """Verifies that an empty jobs DataFrame returns an empty DataFrame safely."""
    recs = recommend_jobs("Python developer", pd.DataFrame())
    assert isinstance(recs, pd.DataFrame)
    assert recs.empty


# ==============================================================================
# 3. MISSING SKILLS TESTS
# ==============================================================================

def test_recommender_resume_with_no_technical_skills(sample_jobs_df):
    """
    Tests recommendation for a candidate who has zero recognized technical skills.
    Skill overlap must be 0.0%, no NaN values, and no uncaught exceptions.
    """
    resume_no_skills = (
        "Enthusiastic and motivated worker seeking job opportunities. "
        "Great communication, leadership, and team collaboration skills."
    )
    extracted = extract_skills(resume_no_skills)
    assert len(extracted) == 0

    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    recs = recommend_jobs(resume_no_skills, sample_jobs_df, vectorizer=vec, job_vectors=vecs)

    assert not recs.empty
    assert (recs["skill_match_pct"] == 0.0).all()
    assert not recs["ml_fit_score"].isna().any()
    assert (recs["ml_fit_score"] >= 0.0).all()


def test_recommender_jobs_with_missing_skills():
    """
    Tests handling of job postings that have missing or 'N/A' required skills.
    Verifies that calculate_skill_match returns 0.0% overlap without division by zero.
    """
    jobs_no_skills = pd.DataFrame([
        {
            "job_id": "JOB_NOSKILL_01",
            "title": "General Worker",
            "company": "Corp A",
            "location": "Remote",
            "skills": "N/A",
            "experience": "N/A",
            "salary": "N/A",
            "category": "General",
            "description": "General position without explicit technical requirements listed.",
            "clean_description": "general position without explicit technical requirements listed"
        }
    ])

    cand_skills = ["Python", "SQL"]
    gap = calculate_skill_match(cand_skills, [])
    assert gap["match_percentage"] == 0.0
    assert gap["matched_skills"] == []

    recs = recommend_jobs("Python developer with SQL experience", jobs_no_skills)
    assert len(recs) == 1
    assert recs.iloc[0]["skill_match_pct"] == 0.0
    assert not np.isnan(recs.iloc[0]["ml_fit_score"])


def test_recommender_both_resume_and_jobs_missing_skills():
    """
    Verifies that when both candidate and job have zero technical skills,
    the score does not crash and skill overlap evaluates cleanly to 0.0%.
    """
    resume_text = "Good team player with punctual attendance and strong work ethic."
    job_text = "Looking for an employee for general day-to-day coordination."

    feats = compute_pair_match_features(resume_text, job_text, job_skills_str="N/A", text_sim_score=0.1)
    assert feats["skill_overlap"] == 0.0
    assert feats["fit_score"] >= 0.0
    assert not np.isnan(feats["fit_score"])


# ==============================================================================
# 4. RELEVANT VERSUS IRRELEVANT JOB DESCRIPTIONS TESTS
# ==============================================================================

def test_recommender_relevant_vs_irrelevant_jobs(sample_jobs_df):
    """
    Compares a Data Scientist resume against:
      - Relevant: Senior Data Scientist (Python, SQL, Machine Learning, PyTorch)
      - Irrelevant: Corporate Advocate (Law, Litigation, Arbitration)
      - Irrelevant: Mechanical Engineer (CAD, Thermodynamics)
    Verifies that the relevant job earns a decisively higher fit score and similarity
    and ranks at #1.
    """
    resume = (
        "Senior Data Scientist with 5 years experience in Python, SQL, Machine Learning, "
        "Pandas, and PyTorch. Built deep learning recommendation models and data pipelines."
    )

    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    recs = recommend_jobs(resume, sample_jobs_df, vectorizer=vec, job_vectors=vecs)

    top_rec = recs.iloc[0]
    assert top_rec["job_id"] == "JOB_DATA_01"
    assert top_rec["category"] == "Data Science"

    data_row = recs[recs["job_id"] == "JOB_DATA_01"].iloc[0]
    legal_row = recs[recs["job_id"] == "JOB_LEGAL_01"].iloc[0]
    mech_row = recs[recs["job_id"] == "JOB_MECH_01"].iloc[0]

    # Relevant job must decisively beat irrelevant jobs in similarity and fit score
    assert data_row["similarity_score"] > legal_row["similarity_score"]
    assert data_row["similarity_score"] > mech_row["similarity_score"]
    assert data_row["skill_match_pct"] > legal_row["skill_match_pct"]
    assert data_row["ml_fit_score"] > legal_row["ml_fit_score"]
    assert data_row["ml_fit_score"] > mech_row["ml_fit_score"]

    # Difference in fit score must be significant (> 30 points)
    assert (data_row["ml_fit_score"] - legal_row["ml_fit_score"]) > 30.0


# ==============================================================================
# 5. ROBUSTNESS & SAFE FALLBACK TESTS
# ==============================================================================

def test_recommender_mismatched_cached_vectors_dimension(sample_jobs_df):
    """
    Verifies that if cached job_vectors has a row-count mismatch with jobs_df
    (e.g. 200 pre-cached rows vs 2 rows in df), recommend_jobs dynamically
    recomputes vectors instead of raising ValueError: Length of values does not match.
    """
    sub_df = sample_jobs_df.head(2).copy()
    vec, vecs = build_job_recommender(sample_jobs_df, save_models=False)
    assert vecs.shape[0] == 4

    # Pass 4-row vectors into a 2-row dataframe
    recs = recommend_jobs("Python and Java developer", sub_df, vectorizer=vec, job_vectors=vecs)
    assert len(recs) == 2
    assert not recs["similarity_score"].isna().any()


def test_recommender_missing_clean_description_column():
    """
    Verifies that a jobs DataFrame without 'clean_description' column
    does not raise KeyError and cleans 'description' or 'title' on the fly.
    """
    raw_df = pd.DataFrame([
        {
            "job_id": "J1",
            "title": "Python Specialist",
            "company": "Tech Corp",
            "location": "Remote",
            "skills": "Python, SQL",
            "experience": "3 years",
            "salary": "$100k",
            "category": "Python Developer",
            "description": "Python specialist needed for backend data workflows and SQL."
        }
    ])
    recs = recommend_jobs("Python specialist", raw_df)
    assert len(recs) == 1
    assert recs.iloc[0]["title"] == "Python Specialist"


# ==============================================================================
# 6. API VALIDATION TESTS (FASTAPI /jobs/recommend)
# ==============================================================================

def test_api_jobs_recommend_rejects_empty_or_too_short():
    """Verifies that /jobs/recommend endpoint returns HTTP 400 for empty or < 10 char text."""
    client = TestClient(app)

    # Empty string
    res_empty = client.post("/api/v1/jobs/recommend", json={"resume_text": ""})
    assert res_empty.status_code in [400, 422]

    # Short string under 10 chars
    res_short = client.post("/api/v1/jobs/recommend", json={"resume_text": "Java"})
    assert res_short.status_code in [400, 422]

    # Whitespace only
    res_spaces = client.post("/api/v1/jobs/recommend", json={"resume_text": "          "})
    assert res_spaces.status_code == 400


# ==============================================================================
# 7. SERVER-SIDE FULL RESUME & 500-CHAR LIMITATION ELIMINATION TESTS
# ==============================================================================

def test_recommender_uses_full_text_via_resume_id():
    """
    Verifies that passing resume_id causes /jobs/recommend to use the full clean_text
    stored in the database, eliminating the 500-character preview truncation.
    """
    import uuid
    import json
    from src.backend.database import SessionLocal
    from src.backend.models.resume import Resume
    from src.data.preprocess import clean_text

    db = SessionLocal()
    # Create a resume longer than 500 chars with generic text up front,
    # but critical technical skills (PyTorch, Machine Learning, SQL) located beyond char 600.
    first_half = (
        "Alice Candidate is an enthusiastic professional with experience in office administration, "
        "customer engagement, communication, team coordination, meeting organization, documentation, "
        "reporting, project tracking, vendor management, and business operations. "
        "Graduated from State University with honors. Seeking technical transition opportunities. "
    )  # ~330 chars
    middle_filler = (
        "Additional responsibilities included organizing internal company events, liaising with "
        "stakeholders, managing scheduling calendars, tracking compliance requirements, and preparing slide decks. "
    )  # ~210 chars. Total now > 540 chars.
    crucial_tech_section = (
        "Key Advanced Technical Skills and Tooling: Machine Learning, Python, PyTorch, SQL, Pandas, Scikit-Learn. "
        "Developed end-to-end deep learning predictive models and neural network classification pipelines."
    )
    full_text = first_half + middle_filler + crucial_tech_section
    assert len(full_text) > 700

    clean_tokens = clean_text(full_text)
    test_id = str(uuid.uuid4())
    rec = Resume(
        id=test_id,
        clean_text=clean_tokens,
        predicted_category="Data Science",
        category_confidence=0.9,
        extracted_skills=json.dumps(["Python", "PyTorch", "SQL", "Pandas", "Scikit-Learn", "Machine Learning"]),
        file_size_bytes=len(full_text),
        sha256="testsha_" + test_id[:16],
        original_filename="long_resume.txt",
        storage_path="storage/test"
    )
    db.add(rec)
    db.commit()

    try:
        client = TestClient(app)
        # Recommendation using resume_id uses the full stored text
        res = client.post("/api/v1/jobs/recommend", json={"resume_id": test_id, "top_n": 5})
        assert res.status_code == 200
        data = res.json()
        assert data["total_results"] > 0
        top_job = data["recommendations"][0]
        # Top job should match Data Science / Machine Learning / Python from the second half
        assert top_job["category"] in ["Data Science", "Python Developer"]
        assert top_job["fit_score"] > 25.0
        assert "description" in top_job

        # Compare with passing ONLY the first 500 characters
        res_truncated = client.post("/api/v1/jobs/recommend", json={"resume_text": full_text[:500], "top_n": 5})
        assert res_truncated.status_code == 200
        truncated_top = res_truncated.json()["recommendations"][0]
        # Full resume match score must be significantly higher than truncated score
        assert top_job["fit_score"] > truncated_top["fit_score"]
    finally:
        db.delete(rec)
        db.commit()
        db.close()


def test_match_score_consistency_with_resume_id():
    """
    Verifies that /matching/score uses resume_id to retrieve the full clean_text
    and that the score matches the recommendation item's score when similarity is passed.
    """
    import uuid
    import json
    from src.backend.database import SessionLocal
    from src.backend.models.resume import Resume
    from src.data.preprocess import clean_text

    db = SessionLocal()
    full_text = "Senior Python Developer with 5 years experience in SQL, Docker, FastAPI, and Git."
    test_id = str(uuid.uuid4())
    rec = Resume(
        id=test_id,
        clean_text=clean_text(full_text),
        predicted_category="Python Developer",
        category_confidence=0.95,
        extracted_skills=json.dumps(["Python", "SQL", "Docker", "FastAPI", "Git"]),
        file_size_bytes=len(full_text),
        sha256="testsha_" + test_id[:16],
        original_filename="python_dev.txt",
        storage_path="storage/test"
    )
    db.add(rec)
    db.commit()

    try:
        client = TestClient(app)
        # Fetch recommendation first
        rec_res = client.post("/api/v1/jobs/recommend", json={"resume_id": test_id, "top_n": 1})
        assert rec_res.status_code == 200
        top_rec = rec_res.json()["recommendations"][0]

        # Call /matching/score with resume_id, job description, and precomputed similarity
        match_payload = {
            "resume_id": test_id,
            "job_text": top_rec["description"] or top_rec["skills"],
            "job_skills": top_rec["skills"],
            "text_similarity": top_rec["similarity_score"]
        }
        match_res = client.post("/api/v1/matching/score", json=match_payload)
        assert match_res.status_code == 200
        match_data = match_res.json()

        # Consistency check: fit_score must match within 0.1
        assert abs(match_data["fit_score"] - top_rec["fit_score"]) < 0.1
        assert match_data["is_probability"] is False
        assert "Heuristic" in match_data["score_label"]
    finally:
        db.delete(rec)
        db.commit()
        db.close()
