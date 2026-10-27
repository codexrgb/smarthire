"""
Job Recommendation Schemas for SmartHire 2.0.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class JobRecommendRequest(BaseModel):
    resume_text: Optional[str] = Field(default=None, description="Resume text to recommend jobs against")
    resume_id: Optional[str] = Field(default=None, description="Optional ID of previously parsed resume")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of top jobs to return")
    category_filter: Optional[str] = Field(default="All", description="Optional category filter (e.g., 'Data Science', 'Sales')")


class JobRecommendItem(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    skills: str
    experience: str
    salary: str
    category: str
    description: Optional[str] = Field(default="", description="Job description")
    similarity_score: float
    skill_match_pct: float
    fit_score: float


class JobRecommendResponse(BaseModel):
    total_results: int
    recommendations: List[JobRecommendItem]
