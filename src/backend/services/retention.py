"""
Guest Resume Retention and Privacy Lifecycle Service for SmartHire 2.0.

Automatically identifies and cleans up unauthenticated guest resumes (candidate_id IS NULL)
that exceed the data retention window (default 24 hours).
Guarantees that authenticated candidate-owned resumes are never purged by guest lifecycle routines.
Provides safe storage file deletion, shared deduplication reference checks,
idempotent execution, and a dry-run reporting mode.
"""

import sys
import logging
import argparse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy.orm import Session

from src.backend.database import get_db, SessionLocal
from src.backend.models.resume import Resume
from src.backend.storage.base import PrivateFileStorage, storage_service

logger = logging.getLogger("smarthire.retention")


@dataclass
class RetentionReport:
    dry_run: bool
    retention_hours: int
    cutoff_time_utc: str
    total_guest_resumes_evaluated: int = 0
    eligible_for_deletion_count: int = 0
    deleted_database_records: int = 0
    deleted_storage_files: int = 0
    missing_storage_files: int = 0
    retained_storage_files_shared: int = 0
    candidate_resumes_protected_count: int = 0
    freed_storage_bytes: int = 0
    processed_resume_ids: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def purge_expired_guest_resumes(
    db: Session,
    retention_hours: int = 24,
    dry_run: bool = False,
    storage: Optional[PrivateFileStorage] = None,
    now: Optional[datetime] = None
) -> RetentionReport:
    """
    Cleans up guest resumes (where candidate_id is NULL) older than retention_hours.

    Args:
        db: SQLAlchemy database session.
        retention_hours: Maximum allowable age in hours for guest resumes (default: 24).
        dry_run: If True, previews eligible records without modifying database or storage.
        storage: Optional custom PrivateFileStorage instance (defaults to global storage_service).
        now: Optional custom UTC datetime for deterministic testing.

    Returns:
        RetentionReport: Summary of records evaluated, deleted, freed bytes, and errors.
    """
    effective_storage = storage or storage_service
    current_utc = now or datetime.now(timezone.utc)
    cutoff = current_utc - timedelta(hours=retention_hours)

    report = RetentionReport(
        dry_run=dry_run,
        retention_hours=retention_hours,
        cutoff_time_utc=cutoff.isoformat()
    )

    # 1. Verify candidate-owned resumes are safely counted and preserved
    candidate_count = db.query(Resume).filter(Resume.candidate_id.isnot(None)).count()
    report.candidate_resumes_protected_count = candidate_count

    # 2. Count total guest resumes
    total_guests = db.query(Resume).filter(Resume.candidate_id.is_(None)).count()
    report.total_guest_resumes_evaluated = total_guests

    # 3. Query expired guest resumes
    expired_guest_resumes = (
        db.query(Resume)
        .filter(
            Resume.candidate_id.is_(None),
            Resume.uploaded_at < cutoff
        )
        .all()
    )

    report.eligible_for_deletion_count = len(expired_guest_resumes)

    logger.info(
        "Guest retention run [dry_run=%s]: %d eligible guest resumes (cutoff: %s, candidate records protected: %d)",
        dry_run,
        report.eligible_for_deletion_count,
        cutoff.isoformat(),
        candidate_count
    )

    for resume in expired_guest_resumes:
        report.processed_resume_ids.append(resume.id)

        # Check physical storage file deletion safety
        if resume.storage_path:
            # Verify if any other resume in the system points to the same storage path
            # (e.g. identical SHA-256 deduplicated upload by another candidate or guest)
            other_refs = (
                db.query(Resume)
                .filter(
                    Resume.storage_path == resume.storage_path,
                    Resume.id != resume.id
                )
                .count()
            )

            if other_refs > 0:
                # File is shared with another active record; retain file on disk
                report.retained_storage_files_shared += 1
                logger.info(
                    "Retained shared storage file '%s' for resume '%s' (%d other references)",
                    resume.storage_path,
                    resume.id,
                    other_refs
                )
            else:
                if dry_run:
                    # In dry-run, check existence without deleting
                    try:
                        safe_path = Path(resume.storage_path)
                        if safe_path.exists():
                            report.deleted_storage_files += 1
                            report.freed_storage_bytes += resume.file_size_bytes or 0
                        else:
                            report.missing_storage_files += 1
                    except Exception as e:
                        report.errors.append(f"Storage path check error for {resume.id}: {str(e)}")
                else:
                    try:
                        file_deleted = effective_storage.delete_file(resume.storage_path)
                        if file_deleted:
                            report.deleted_storage_files += 1
                            report.freed_storage_bytes += resume.file_size_bytes or 0
                        else:
                            report.missing_storage_files += 1
                    except Exception as e:
                        logger.warning("Could not delete physical file for resume %s: %s", resume.id, str(e))
                        report.errors.append(f"Storage deletion failed for {resume.id}: {str(e)}")

        if not dry_run:
            db.delete(resume)
            report.deleted_database_records += 1

    if not dry_run and report.deleted_database_records > 0:
        db.commit()

    logger.info(
        "Guest retention completed [dry_run=%s]: %d DB records deleted, %d files freed (%d bytes)",
        dry_run,
        report.deleted_database_records if not dry_run else 0,
        report.deleted_storage_files,
        report.freed_storage_bytes
    )

    return report


def main():
    """CLI Entrypoint for scheduled cron execution or manual maintenance."""
    parser = argparse.ArgumentParser(
        description="SmartHire 2.0 Guest Resume Retention & Lifecycle Cleaner"
    )
    parser.add_argument(
        "--retention-hours",
        type=int,
        default=24,
        help="Retention window in hours (default: 24)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate cleanup and print report without deleting records or files"
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        report = purge_expired_guest_resumes(
            db=db,
            retention_hours=args.retention_hours,
            dry_run=args.dry_run
        )
        print("=== SmartHire 2.0 Guest Retention Report ===")
        print(f" Dry Run Mode:                  {report.dry_run}")
        print(f" Cutoff Time (UTC):             {report.cutoff_time_utc}")
        print(f" Candidate Resumes Protected:   {report.candidate_resumes_protected_count}")
        print(f" Total Guest Resumes Evaluated: {report.total_guest_resumes_evaluated}")
        print(f" Eligible For Deletion:         {report.eligible_for_deletion_count}")
        print(f" Database Records Deleted:      {report.deleted_database_records}")
        print(f" Physical Files Deleted:        {report.deleted_storage_files}")
        print(f" Missing Storage Files Handled: {report.missing_storage_files}")
        print(f" Shared Files Retained:         {report.retained_storage_files_shared}")
        print(f" Freed Storage:                 {report.freed_storage_bytes} bytes")
        if report.errors:
            print(f" Errors Encountered:            {len(report.errors)}")
            for err in report.errors:
                print(f"  - {err}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
