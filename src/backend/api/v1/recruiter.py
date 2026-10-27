"""
Recruiter & Protected Candidate Routes for SmartHire 2.0 API.
Enforces strict Role-Based Access Control (RBAC): restricted to recruiters and administrators.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from src.backend.database import get_db
from src.backend.models.resume import Resume
from src.backend.models.application import Application
from src.backend.models.recruiter_action import RecruiterAction
from src.backend.security.auth import require_role
from src.utils.security import redact_pii

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


class CandidateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: str
    original_filename: str
    predicted_category: str
    category_confidence: float
    file_size_bytes: int
    uploaded_at: str


class RecruiterActionLogRequest(BaseModel):
    action_type: str
    target_entity_type: str
    target_entity_id: str
    details: Optional[str] = "{}"


class RecruiterActionOut(BaseModel):
    id: str
    recruiter_id: str
    action_type: str
    target_entity_type: str
    target_entity_id: str
    created_at: str


@router.get("/candidates", response_model=List[CandidateSummary])
def list_candidates(
    current_recruiter: dict = Depends(require_role(["recruiter", "admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns candidate resumes. Strictly protected by RBAC; requires recruiter or admin credentials.
    Audit action is logged automatically.
    """
    resumes = db.query(Resume).order_by(Resume.uploaded_at.desc()).limit(50).all()

    # Log action
    audit = RecruiterAction(
        recruiter_id=current_recruiter["id"],
        action_type="list_candidates",
        target_entity_type="resume",
        target_entity_id="all",
        details=f'{{"count": {len(resumes)}}}'
    )
    db.add(audit)
    db.commit()

    return [
        CandidateSummary(
            resume_id=r.id,
            original_filename=r.original_filename,
            predicted_category=r.predicted_category,
            category_confidence=r.category_confidence,
            file_size_bytes=r.file_size_bytes,
            uploaded_at=r.uploaded_at.isoformat()
        )
        for r in resumes
    ]


@router.post("/actions", response_model=RecruiterActionOut)
def record_recruiter_action(
    payload: RecruiterActionLogRequest,
    current_recruiter: dict = Depends(require_role(["recruiter", "admin"])),
    db: Session = Depends(get_db)
):
    """Logs an explicit recruiter action for compliance auditing."""
    audit = RecruiterAction(
        recruiter_id=current_recruiter["id"],
        action_type=payload.action_type,
        target_entity_type=payload.target_entity_type,
        target_entity_id=payload.target_entity_id,
        details=payload.details or "{}"
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return RecruiterActionOut(
        id=audit.id,
        recruiter_id=audit.recruiter_id,
        action_type=audit.action_type,
        target_entity_type=audit.target_entity_type,
        target_entity_id=audit.target_entity_id,
        created_at=audit.created_at.isoformat()
    )


@router.get("/actions", response_model=List[RecruiterActionOut])
def list_recruiter_actions(
    current_recruiter: dict = Depends(require_role(["recruiter", "admin"])),
    db: Session = Depends(get_db)
):
    """Returns recruiter action audit logs."""
    actions = db.query(RecruiterAction).order_by(RecruiterAction.created_at.desc()).limit(50).all()
    return [
        RecruiterActionOut(
            id=a.id,
            recruiter_id=a.recruiter_id,
            action_type=a.action_type,
            target_entity_type=a.target_entity_type,
            target_entity_id=a.target_entity_id,
            created_at=a.created_at.isoformat()
        )
        for a in actions
    ]
