"""
Resume Schemas for SmartHire 2.0.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ResumeParseResponse(BaseModel):
    resume_id: str
    original_filename: str
    file_size_bytes: int
    sha256: str
    extracted_skills: List[str]
    predicted_category: str
    category_confidence: float
    category_probabilities: Dict[str, float]
    status_message: str
    extracted_text_preview: str = Field(description="First 500 characters of sanitized extracted text")
