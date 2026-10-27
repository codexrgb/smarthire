"""
Matching Feature & Fit Score Schemas for SmartHire 2.0.
Explicitly labels the fit score as a heuristic index, never a probability.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MatchScoreRequest(BaseModel):
    resume_text: Optional[str] = Field(default=None, description="Raw or cleaned candidate resume text")
    resume_id: Optional[str] = Field(default=None, description="Optional ID of previously parsed resume")
    job_text: str = Field(..., min_length=10, description="Job posting title and description")
    job_skills: Optional[str] = Field(default="", description="Optional comma-separated skill list")
    text_similarity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional pre-computed cosine text similarity (0.0 to 1.0). If omitted, computed on the fly."
    )


class MatchScoreResponse(BaseModel):
    text_similarity: float = Field(description="Cosine text similarity between candidate and job descriptions (0.0 - 1.0)")
    skill_overlap: float = Field(description="Ratio of required job skills matched by candidate (0.0 - 1.0)")
    experience_match: float = Field(description="Ratio of candidate experience to required experience (0.0 - 1.0)")
    fit_score: float = Field(description="Composite Multi-Factor Compatibility Index (0.0 - 100.0)")
    matched_skills: List[str]
    missing_skills: List[str]
    score_label: str = Field(default="Heuristic Compatibility Index")
    is_probability: bool = Field(default=False, description="Always False: Score is a deterministic linear heuristic, NOT a probability.")
    explanation: str
