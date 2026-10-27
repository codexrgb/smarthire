"""
Job Recommendation & Explorer Route for SmartHire 2.0 API.
Reuses existing TF-IDF cosine recommender routines.
"""

import joblib
import pandas as pd
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.resume import Resume
from src.backend.security.auth import get_optional_current_user, verify_resume_access
from src.backend.schemas.job import (
    JobRecommendRequest, JobRecommendItem, JobRecommendResponse
)
from src.config import PROCESSED_DATA_DIR, MODELS_DIR
from src.models.recommender import recommend_jobs

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Cache jobs DataFrame and recommendation artifacts in memory
_jobs_cache = None
_vectorizer_cache = None
_vectors_cache = None


def get_jobs_data() -> pd.DataFrame:
    """Loads and caches processed jobs dataset."""
    global _jobs_cache
    if _jobs_cache is None:
        jobs_path = PROCESSED_DATA_DIR / "jobs.csv"
        if not jobs_path.exists():
            jobs_path = PROCESSED_DATA_DIR / "processed_jobs.csv"
        if jobs_path.exists():
            _jobs_cache = pd.read_csv(jobs_path)
        else:
            _jobs_cache = pd.DataFrame()
    return _jobs_cache


def get_recommendation_models():
    """Loads and caches recommender vectorizer and pre-computed job vectors."""
    global _vectorizer_cache, _vectors_cache
    if _vectorizer_cache is None:
        vec_path = MODELS_DIR / "job_vectorizer.pkl"
        if vec_path.exists():
            try:
                _vectorizer_cache = joblib.load(vec_path)
            except Exception:
                _vectorizer_cache = None

    if _vectors_cache is None:
        vectors_path = MODELS_DIR / "job_vectors.pkl"
        if vectors_path.exists():
            try:
                _vectors_cache = joblib.load(vectors_path)
            except Exception:
                _vectors_cache = None

    return _vectorizer_cache, _vectors_cache


@router.post("/recommend", response_model=JobRecommendResponse)
def get_job_recommendations(
    payload: JobRecommendRequest,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Ranks local job postings against candidate resume text using TF-IDF Cosine Similarity
    and transparent multi-factor compatibility scores.
    Supports either full text directly or looking up full clean_text by resume_id.
    Strictly verifies ownership/role authorization when referencing stored candidate resumes.
    """
    resume_text = (payload.resume_text or "").strip()
    if payload.resume_id:
        resume_record = db.query(Resume).filter(Resume.id == payload.resume_id).first()
        if not resume_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume record '{payload.resume_id}' not found."
            )
        # Enforce RBAC / candidate ownership
        verify_resume_access(resume_record, current_user)
        if resume_record.clean_text:
            resume_text = resume_record.clean_text.strip()

    if len(resume_text) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text or valid parsed resume must contain at least 10 characters."
        )

    jobs_df = get_jobs_data()
    if jobs_df.empty:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job dataset not loaded. Ensure data/processed/jobs.csv exists."
        )

    vec, vecs = get_recommendation_models()

    recs_df = recommend_jobs(
        resume_text=resume_text,
        jobs_df=jobs_df,
        vectorizer=vec,
        job_vectors=vecs,
        top_n=payload.top_n,
        category_filter=payload.category_filter
    )

    items = []
    for _, row in recs_df.iterrows():
        items.append(JobRecommendItem(
            job_id=str(row.get("job_id", "N/A")),
            title=str(row.get("title", "N/A")),
            company=str(row.get("company", "N/A")),
            location=str(row.get("location", "N/A")),
            skills=str(row.get("skills", "N/A")),
            experience=str(row.get("experience", "N/A")),
            salary=str(row.get("salary", "N/A")),
            category=str(row.get("category", "N/A")),
            description=str(row.get("description", "")),
            similarity_score=round(float(row.get("similarity_score", 0.0)), 4),
            skill_match_pct=round(float(row.get("skill_match_pct", 0.0)), 2),
            fit_score=round(float(row.get("ml_fit_score", 0.0)), 2)
        ))

    return JobRecommendResponse(
        total_results=len(items),
        recommendations=items
    )


@router.get("", response_model=List[JobRecommendItem])
def list_jobs(
    title: Optional[str] = Query(None, description="Filter by title substring"),
    location: Optional[str] = Query(None, description="Filter by location substring"),
    limit: int = Query(20, ge=1, le=100)
):
    """Lists and filters job postings from processed dataset."""
    df = get_jobs_data()
    if df.empty:
        return []

    fil_df = df.copy()
    if title:
        fil_df = fil_df[fil_df["title"].astype(str).str.contains(title, case=False, na=False)]
    if location:
        fil_df = fil_df[fil_df["location"].astype(str).str.contains(location, case=False, na=False)]

    items = []
    for _, row in fil_df.head(limit).iterrows():
        items.append(JobRecommendItem(
            job_id=str(row.get("job_id", "N/A")),
            title=str(row.get("title", "N/A")),
            company=str(row.get("company", "N/A")),
            location=str(row.get("location", "N/A")),
            skills=str(row.get("skills", "N/A")),
            experience=str(row.get("experience", "N/A")),
            salary=str(row.get("salary", "N/A")),
            category=str(row.get("category", "N/A")),
            description=str(row.get("description", "")),
            similarity_score=0.0,
            skill_match_pct=0.0,
            fit_score=0.0
        ))

    return items
