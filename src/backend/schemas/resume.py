"""
Resume Schemas for SmartHire 2.0.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ResumeValidationResponse(BaseModel):
    is_valid: bool
    confidence_category: str = Field(description="HIGH, MEDIUM, or LOW confidence category")
    confidence_score: float = Field(description="Heuristic index from 0.0 to 1.0 (not a calibrated probability)")
    score_label: str = "Heuristic Validation Index"
    is_calibrated_probability: bool = False
    document_type: str = Field(description="Detected document classification: resume, research_paper, invoice, etc.")
    rejection_reason: Optional[str] = None
    user_message: str
    detected_sections: List[str] = Field(default_factory=list)
    structural_signals: Dict[str, Any] = Field(default_factory=dict)


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
    validation: Optional[ResumeValidationResponse] = None


class ResumeSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: Optional[str] = None
    original_filename: str
    file_size_bytes: int
    sha256: str
    predicted_category: str
    category_confidence: float
    uploaded_at: str


class ResumeDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: Optional[str] = None
    original_filename: str
    file_size_bytes: int
    sha256: str
    predicted_category: str
    category_confidence: float
    extracted_skills: List[str]
    uploaded_at: str
    extracted_text_preview: str
