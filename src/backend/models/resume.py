"""
Resume Model for SmartHire 2.0.
References private file storage; stores cleaned tokens rather than raw PII text.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.backend.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)  # Path in private file storage
    file_size_bytes = Column(Integer, nullable=False, default=0)
    sha256 = Column(String(64), index=True, nullable=False)
    clean_text = Column(Text, nullable=False, default="")  # Preprocessed & PII-redacted text
    predicted_category = Column(String(100), index=True, nullable=False, default="General")
    category_confidence = Column(Float, nullable=False, default=0.0)
    extracted_skills = Column(Text, nullable=False, default="[]")  # JSON encoded list of skills
    uploaded_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume", cascade="all, delete-orphan")
