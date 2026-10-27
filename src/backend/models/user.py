"""
User Model for Authentication and Role-Based Access Control.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship

from src.backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, default="")
    role = Column(String(50), nullable=False, default="candidate")  # 'candidate', 'recruiter', 'admin'
    is_active = Column(Boolean, nullable=False, default=True)
    login_count = Column(Integer, nullable=False, default=0, server_default="0")
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    recruiter_actions = relationship("RecruiterAction", back_populates="recruiter", cascade="all, delete-orphan")
