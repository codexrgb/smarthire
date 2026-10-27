"""
Candidate-Job Matching & Compatibility Scoring Route for SmartHire 2.0 API.
Reuses existing match features and skill gap routines.
Treats fit score as a multi-factor heuristic index, never a calibrated hiring probability.
"""

import joblib
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.backend.database import get_db
from src.backend.models.resume import Resume
from src.backend.security.auth import get_optional_current_user, verify_resume_access
from src.backend.schemas.match import MatchScoreRequest, MatchScoreResponse
from src.features.match_features import compute_pair_match_features
from src.features.text_features import generate_skill_gap
from src.data.preprocess import clean_text
from src.config import MODELS_DIR

router = APIRouter(prefix="/matching", tags=["Matching"])


def compute_pairwise_cosine_similarity(text_a: str, text_b: str) -> float:
    """Computes cosine similarity between two text snippets using TF-IDF."""
    clean_a = clean_text(text_a)
    clean_b = clean_text(text_b)
    if not clean_a or not clean_b:
        return 0.0

    # Try loading pre-trained job vectorizer
    vec_path = MODELS_DIR / "job_vectorizer.pkl"
    if vec_path.exists():
        try:
            vectorizer = joblib.load(vec_path)
            vecs = vectorizer.transform([clean_a, clean_b])
            sim = float(cosine_similarity(vecs[0:1], vecs[1:2])[0][0])
            return max(0.0, min(1.0, sim))
        except Exception:
            pass

    # Fallback to local pairwise TF-IDF
    local_vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    vecs = local_vec.fit_transform([clean_a, clean_b])
    sim = float(cosine_similarity(vecs[0:1], vecs[1:2])[0][0])
    return max(0.0, min(1.0, sim))


@router.post("/score", response_model=MatchScoreResponse)
def calculate_match_score(
    payload: MatchScoreRequest,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Computes transparent multi-factor compatibility score between candidate resume and job posting.
    Supports either direct resume_text or looking up full clean_text by resume_id.
    Strictly verifies ownership/role authorization when referencing stored candidate resumes.

    Formula:
      Fit Score = (0.50 * TextSimilarity + 0.30 * SkillOverlap + 0.20 * ExperienceMatch) * 100

    IMPORTANT:
      This score is a deterministic linear heuristic index, NOT a calibrated probability of hiring.
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
        if resume_record and resume_record.clean_text:
            resume_text = resume_record.clean_text.strip()

    if len(resume_text) < 10 or len(payload.job_text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both resume_text and job_text must contain at least 10 characters."
        )

    # Compute or use provided text similarity
    if payload.text_similarity is not None:
        text_sim = float(payload.text_similarity)
    else:
        text_sim = compute_pairwise_cosine_similarity(resume_text, payload.job_text)

    # Compute match features
    match_feats = compute_pair_match_features(
        resume_text=resume_text,
        job_text=payload.job_text,
        job_skills_str=payload.job_skills or "",
        text_sim_score=text_sim
    )

    # Skill gap details
    skill_gap = generate_skill_gap(
        resume_text=resume_text,
        job_text_or_skills=payload.job_skills if payload.job_skills else payload.job_text
    )

    return MatchScoreResponse(
        text_similarity=match_feats["text_similarity"],
        skill_overlap=match_feats["skill_overlap"],
        experience_match=match_feats["experience_match"],
        fit_score=match_feats["fit_score"],
        matched_skills=skill_gap["matched_skills"],
        missing_skills=skill_gap["missing_skills"],
        score_label="Heuristic Compatibility Index",
        is_probability=False,
        explanation=(
            f"Compatibility index computed from 50% text similarity ({match_feats['text_similarity']*100:.1f}%), "
            f"30% skill overlap ({match_feats['skill_overlap']*100:.1f}%), and "
            f"20% experience compatibility ({match_feats['experience_match']*100:.1f}%). "
            f"This is an empirical ranking index, not an interview probability."
        )
    )
