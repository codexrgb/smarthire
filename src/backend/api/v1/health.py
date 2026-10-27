"""
Health check route for SmartHire 2.0 API.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.backend.config import settings
from src.backend.database import get_db
from src.backend.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Verifies service operational status and database connectivity."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database_connected=db_ok
    )
