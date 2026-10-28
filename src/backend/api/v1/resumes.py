"""
Resume Upload & Parsing Route for SmartHire 2.0 API.
Validates file formats, sizes, and malformed files; stores in private storage without logging PII.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Header
)
from sqlalchemy.orm import Session

from src.backend.config import settings
from src.backend.database import get_db
from src.backend.models.resume import Resume
from src.backend.schemas.resume import (
    ResumeParseResponse, ResumeSummaryOut, ResumeDetailOut, ResumeValidationResponse
)
from src.backend.storage.base import storage_service
from src.backend.security.auth import (
    decode_access_token, get_current_user, get_optional_current_user, verify_resume_access
)
from src.backend.services.document_validation import validate_document
from src.parsing.resume_parser import extract_resume_text
from src.features.text_features import extract_skills
from src.models.classifier import predict_resume_category
from src.data.preprocess import clean_text
from src.utils.security import redact_pii

logger = logging.getLogger("smarthire.api.resumes")
router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/validate", response_model=ResumeValidationResponse)
async def validate_resume_document(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
):
    """
    Validates uploaded document or raw text against multi-signal resume criteria.
    Accurately classifies document as resume, research paper, invoice, assignment, etc.
    Returns structured validation result with confidence category, score, and user guidance.
    """
    content_bytes = None
    target_filename = filename or "document.txt"

    if file is not None:
        target_filename = file.filename or "document.txt"
        ext = Path(target_filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return ResumeValidationResponse(
                is_valid=False,
                confidence_category="HIGH",
                confidence_score=0.99,
                document_type="unsupported_format",
                rejection_reason=f"Unsupported file format '{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}",
                user_message="This document does not appear to be a resume. Please upload your resume in PDF or DOCX format."
            )

        content_bytes = await file.read()
        if len(content_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

    val_res = validate_document(
        content_bytes=content_bytes,
        filename=target_filename,
        raw_text=raw_text
    )
    return ResumeValidationResponse(**val_res.to_dict())


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Parses resume from uploaded document (.pdf, .docx, .txt) or direct text.
    Validates file extension, size limit, and malformed content.
    Enforces multi-signal document validation BEFORE storage or DB persistence.
    Extracts plain text, skills, and predicted job category.
    Stores raw binary in private storage without exposing PII in logs.
    """
    # Authenticate user if token provided (optional for parsing)
    current_user_id = None
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = decode_access_token(token)
            current_user_id = payload.get("sub")
        except Exception:
            current_user_id = None

    content_bytes = b""
    target_filename = filename or "document.txt"

    if file is not None:
        target_filename = file.filename or "document.txt"
        ext = Path(target_filename).suffix.lower()

        # Validate file extension
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension '{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # Read content and validate size
        content_bytes = await file.read()
        if len(content_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if len(content_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        # Multi-signal resume validation before persisting or parsing
        val_res = validate_document(content_bytes=content_bytes, filename=target_filename)
        if not val_res.is_valid:
            logger.warning(
                "Document rejected by resume validator: type=%s, category=%s, reason=%s",
                val_res.document_type,
                val_res.confidence_category,
                val_res.rejection_reason
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=val_res.user_message
            )

        # Extract text via parser module
        extracted_text, msg = extract_resume_text(content_bytes, target_filename)
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract readable text from document: {msg}"
            )
    elif raw_text:
        extracted_text = raw_text.strip()
        if len(extracted_text) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume text too short (minimum 10 characters required)."
            )

        target_filename = filename or "pasted_resume.txt"
        val_res = validate_document(raw_text=extracted_text, filename=target_filename)
        if not val_res.is_valid:
            logger.warning(
                "Text input rejected by resume validator: type=%s, category=%s, reason=%s",
                val_res.document_type,
                val_res.confidence_category,
                val_res.rejection_reason
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=val_res.user_message
            )

        content_bytes = extracted_text.encode("utf-8")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a file upload or raw_text form field must be provided."
        )

    # Save to private file storage
    storage_record = storage_service.save_file(content_bytes, target_filename)
    logger.info(
        "Stored resume file metadata: sha256=%s, size=%d bytes (raw text not logged)",
        storage_record["sha256"],
        storage_record["size_bytes"]
    )

    # Extract Skills & Preprocessing
    extracted_skills = extract_skills(extracted_text)
    cleaned_tokens = clean_text(extracted_text)

    # Predict Category
    cat_pred, conf, top_probs = predict_resume_category(extracted_text)

    # Persist in Database
    resume_record = Resume(
        candidate_id=current_user_id,
        original_filename=storage_record["original_filename"],
        storage_path=storage_record["storage_path"],
        file_size_bytes=storage_record["size_bytes"],
        sha256=storage_record["sha256"],
        clean_text=cleaned_tokens,
        predicted_category=cat_pred,
        category_confidence=conf,
        extracted_skills=json.dumps(extracted_skills)
    )
    db.add(resume_record)
    db.commit()
    db.refresh(resume_record)

    # Build response (preview first 500 characters of PII-redacted text)
    redacted_preview = redact_pii(extracted_text[:500])

    return ResumeParseResponse(
        resume_id=resume_record.id,
        original_filename=storage_record["original_filename"],
        file_size_bytes=storage_record["size_bytes"],
        sha256=storage_record["sha256"],
        extracted_skills=extracted_skills,
        predicted_category=cat_pred,
        category_confidence=conf,
        category_probabilities=top_probs,
        status_message="Resume parsed successfully.",
        extracted_text_preview=redacted_preview,
        validation=ResumeValidationResponse(**val_res.to_dict())
    )


@router.get("/my-resumes", response_model=List[ResumeSummaryOut])
def get_my_resumes(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns resumes uploaded by the currently authenticated user.
    Strictly isolated: candidates can only list their own uploaded resumes.
    """
    resumes = db.query(Resume).filter(Resume.candidate_id == current_user["id"]).order_by(Resume.uploaded_at.desc()).all()
    return [
        ResumeSummaryOut(
            id=r.id,
            candidate_id=r.candidate_id,
            original_filename=r.original_filename,
            file_size_bytes=r.file_size_bytes,
            sha256=r.sha256,
            predicted_category=r.predicted_category,
            category_confidence=r.category_confidence,
            uploaded_at=r.uploaded_at.isoformat()
        )
        for r in resumes
    ]


@router.get("/{resume_id}", response_model=ResumeDetailOut)
def get_resume_by_id(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Retrieves metadata and sanitized preview of a candidate resume.
    Strictly enforces RBAC / candidate ownership verification.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume record '{resume_id}' not found."
        )

    verify_resume_access(resume, current_user)

    try:
        skills = json.loads(resume.extracted_skills)
    except Exception:
        skills = []

    return ResumeDetailOut(
        id=resume.id,
        candidate_id=resume.candidate_id,
        original_filename=resume.original_filename,
        file_size_bytes=resume.file_size_bytes,
        sha256=resume.sha256,
        predicted_category=resume.predicted_category,
        category_confidence=resume.category_confidence,
        extracted_skills=skills,
        uploaded_at=resume.uploaded_at.isoformat(),
        extracted_text_preview=redact_pii(resume.clean_text[:500])
    )


@router.delete("/{resume_id}")
def delete_resume_by_id(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Deletes a candidate's resume from private storage and database.
    Strictly enforces candidate ownership or recruiter/admin role.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume record '{resume_id}' not found."
        )

    verify_resume_access(resume, current_user)

    # Safe file deletion from private storage
    if resume.storage_path:
        try:
            storage_service.delete_file(resume.storage_path)
        except Exception as e:
            logger.warning("Could not delete physical file for resume %s: %s", resume_id, str(e))

    db.delete(resume)
    db.commit()

    return {"status": "success", "message": f"Resume '{resume_id}' deleted successfully."}
