"""
Job Posting Model for SmartHire 2.0.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.orm import relationship

from src.backend.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), index=True, nullable=False)
    company = Column(String(255), index=True, nullable=False)
    location = Column(String(255), nullable=False, default="Remote")
    skills = Column(Text, nullable=False, default="")
    experience_required = Column(String(100), nullable=False, default="N/A")
    salary_range = Column(String(100), nullable=False, default="N/A")
    description = Column(Text, nullable=False, default="")
    clean_description = Column(Text, nullable=False, default="")
    category = Column(String(100), index=True, nullable=False, default="General")
    cluster_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
