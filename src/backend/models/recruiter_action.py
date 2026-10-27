"""
Recruiter Action Audit Log Model for SmartHire 2.0.
Tracks recruiter evaluation activities, status changes, and exports without recording candidate PII.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.backend.database import Base


class RecruiterAction(Base):
    __tablename__ = "recruiter_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recruiter_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(100), nullable=False)  # e.g., 'view_candidate', 'change_status', 'export_pool'
    target_entity_type = Column(String(50), nullable=False)  # 'resume', 'application', 'job'
    target_entity_id = Column(String(36), nullable=False)
    details = Column(Text, nullable=False, default="{}")  # Non-PII JSON metadata (timestamps, score thresholds)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    recruiter = relationship("User", back_populates="recruiter_actions")
