"""
Application Model for SmartHire 2.0.
Records candidate job applications, matching feature breakdown, and heuristic fit score.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.backend.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    text_similarity = Column(Float, nullable=False, default=0.0)
    skill_overlap = Column(Float, nullable=False, default=0.0)
    experience_match = Column(Float, nullable=False, default=0.0)
    fit_score = Column(Float, nullable=False, default=0.0)  # Heuristic score (0-100)

    status = Column(String(50), nullable=False, default="submitted")  # submitted, reviewing, shortlisted, rejected
    applied_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    candidate = relationship("User", back_populates="applications")
