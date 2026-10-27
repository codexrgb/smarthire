"""
Unit & Integration Tests for Guest Resume Retention & Privacy Lifecycle.

Verifies:
- Safe cleanup of guest resumes (candidate_id IS NULL) older than 24 hours.
- Strict preservation of candidate-owned resumes regardless of age.
- Preservation of recent guest resumes (< 24 hours).
- Graceful handling of missing physical storage files.
- Idempotency when running repeated cleanup cycles.
- Dry-run reporting mode leaving database and filesystem unchanged.
- Preservation of deduplicated physical storage files shared with candidate resumes.
"""

import os
import uuid
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database import Base
from src.backend.models.user import User
from src.backend.models.resume import Resume
from src.backend.storage.base import PrivateFileStorage
from src.backend.services.retention import purge_expired_guest_resumes


@pytest.fixture
def retention_env():
    """Isolated in-memory database and temporary file storage directory for retention tests."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSession()

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = PrivateFileStorage(base_dir=Path(tmp_dir))
        yield {"db": db, "storage": storage, "storage_dir": Path(tmp_dir)}

    db.close()
    Base.metadata.drop_all(bind=test_engine)


def create_test_resume(
    db,
    storage,
    candidate_id: str | None,
    filename: str,
    content: bytes,
    uploaded_at: datetime
) -> Resume:
    saved = storage.save_file(content, filename)
    resume = Resume(
        id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        original_filename=saved["original_filename"],
        storage_path=saved["storage_path"],
        file_size_bytes=saved["size_bytes"],
        sha256=saved["sha256"],
        clean_text=content.decode("utf-8", errors="ignore"),
        predicted_category="Engineering",
        category_confidence=0.92,
        uploaded_at=uploaded_at
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def test_retention_old_guest_resumes_cleaned_up(retention_env):
    db = retention_env["db"]
    storage = retention_env["storage"]
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(hours=25)

    resume = create_test_resume(
        db=db,
        storage=storage,
        candidate_id=None,
        filename="old_guest_resume.txt",
        content=b"Candidate guest content older than 24 hours.",
        uploaded_at=old_time
    )
    storage_path = Path(resume.storage_path)
    assert storage_path.exists()

    report = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=False, storage=storage, now=now)

    assert report.eligible_for_deletion_count == 1
    assert report.deleted_database_records == 1
    assert report.deleted_storage_files == 1
    assert not storage_path.exists()
    assert db.query(Resume).filter(Resume.id == resume.id).first() is None


def test_retention_recent_guest_resumes_preserved(retention_env):
    db = retention_env["db"]
    storage = retention_env["storage"]
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    recent_time = now - timedelta(hours=5)

    resume = create_test_resume(
        db=db,
        storage=storage,
        candidate_id=None,
        filename="recent_guest_resume.txt",
        content=b"Recent guest resume created 5 hours ago.",
        uploaded_at=recent_time
    )
    storage_path = Path(resume.storage_path)
    assert storage_path.exists()

    report = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=False, storage=storage, now=now)

    assert report.eligible_for_deletion_count == 0
    assert report.deleted_database_records == 0
    assert report.deleted_storage_files == 0
    assert storage_path.exists()
    assert db.query(Resume).filter(Resume.id == resume.id).first() is not None


def test_retention_candidate_resumes_never_deleted(retention_env):
    db = retention_env["db"]
    storage = retention_env["storage"]
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    ancient_time = now - timedelta(days=30)

    # Create candidate user
    candidate_user = User(
        id=str(uuid.uuid4()),
        email="candidate_protected@example.com",
        hashed_password="secure_hash_candidate",
        full_name="Protected Candidate",
        role="candidate"
    )
    db.add(candidate_user)
    db.commit()

    candidate_resume = create_test_resume(
        db=db,
        storage=storage,
        candidate_id=candidate_user.id,
        filename="candidate_permanent_resume.txt",
        content=b"Candidate-owned portfolio resume.",
        uploaded_at=ancient_time
    )
    storage_path = Path(candidate_resume.storage_path)
    assert storage_path.exists()

    report = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=False, storage=storage, now=now)

    assert report.candidate_resumes_protected_count == 1
    assert report.eligible_for_deletion_count == 0
    assert report.deleted_database_records == 0
    assert storage_path.exists()
    assert db.query(Resume).filter(Resume.id == candidate_resume.id).first() is not None


def test_retention_missing_storage_files_graceful(retention_env):
    db = retention_env["db"]
    storage = retention_env["storage"]
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(hours=36)

    resume = create_test_resume(
        db=db,
        storage=storage,
        candidate_id=None,
        filename="ghost_guest_resume.txt",
        content=b"Content destined for pre-deletion.",
        uploaded_at=old_time
    )
    storage_path = Path(resume.storage_path)
    if storage_path.exists():
        storage_path.unlink()
    assert not storage_path.exists()

    report = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=False, storage=storage, now=now)

    assert report.eligible_for_deletion_count == 1
    assert report.deleted_database_records == 1
    assert report.missing_storage_files == 1
    assert len(report.errors) == 0
    assert db.query(Resume).filter(Resume.id == resume.id).first() is None


def test_retention_repeated_cleanup_idempotent(retention_env):
    db = retention_env["db"]
    storage = retention_env["storage"]
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(hours=48)

    resume = create_test_resume(
        db=db,
        storage=storage,
        candidate_id=None,
        filename="idempotent_test_resume.txt",
        content=b"Testing idempotent multi-cycle cleanup.",
        uploaded_at=old_time
    )

    # Cycle 1
    report1 = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=False, storage=storage, now=now)
    assert report1.eligible_for_deletion_count == 1
    assert report1.deleted_database_records == 1

    # Cycle 2 (immediate re-run)
    report2 = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=False, storage=storage, now=now)
    assert report2.eligible_for_deletion_count == 0
    assert report2.deleted_database_records == 0
    assert report2.deleted_storage_files == 0
    assert len(report2.errors) == 0


def test_retention_dry_run_mode(retention_env):
    db = retention_env["db"]
    storage = retention_env["storage"]
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(hours=50)

    resume = create_test_resume(
        db=db,
        storage=storage,
        candidate_id=None,
        filename="dry_run_guest_resume.txt",
        content=b"Dry run simulation sample text.",
        uploaded_at=old_time
    )
    storage_path = Path(resume.storage_path)
    assert storage_path.exists()

    report = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=True, storage=storage, now=now)

    assert report.dry_run is True
    assert report.eligible_for_deletion_count == 1
    assert report.deleted_database_records == 0
    # Storage file and DB record MUST still exist after dry-run
    assert storage_path.exists()
    assert db.query(Resume).filter(Resume.id == resume.id).first() is not None


def test_retention_shared_deduped_file_preserved(retention_env):
    """
    If a guest resume shares identical content and storage_path with a candidate resume,
    the guest resume DB record is purged, but the physical file is preserved for the candidate.
    """
    db = retention_env["db"]
    storage = retention_env["storage"]
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
    old_time = now - timedelta(hours=40)

    candidate_user = User(
        id=str(uuid.uuid4()),
        email="shared_owner@example.com",
        hashed_password="pw_hash_shared",
        full_name="Shared Owner",
        role="candidate"
    )
    db.add(candidate_user)
    db.commit()

    shared_content = b"Exact identical resume content for SHA256 deduplication."
    filename = "shared_document.txt"

    # Guest resume
    guest_resume = create_test_resume(
        db=db,
        storage=storage,
        candidate_id=None,
        filename=filename,
        content=shared_content,
        uploaded_at=old_time
    )

    # Candidate resume referencing same storage file
    candidate_resume = Resume(
        id=str(uuid.uuid4()),
        candidate_id=candidate_user.id,
        original_filename=guest_resume.original_filename,
        storage_path=guest_resume.storage_path,
        file_size_bytes=guest_resume.file_size_bytes,
        sha256=guest_resume.sha256,
        clean_text=guest_resume.clean_text,
        predicted_category=guest_resume.predicted_category,
        category_confidence=guest_resume.category_confidence,
        uploaded_at=now
    )
    db.add(candidate_resume)
    db.commit()

    storage_path = Path(guest_resume.storage_path)
    assert storage_path.exists()

    report = purge_expired_guest_resumes(db=db, retention_hours=24, dry_run=False, storage=storage, now=now)

    assert report.eligible_for_deletion_count == 1
    assert report.deleted_database_records == 1
    assert report.retained_storage_files_shared == 1
    assert report.deleted_storage_files == 0
    # Physical file still exists on disk because candidate needs it
    assert storage_path.exists()
    assert db.query(Resume).filter(Resume.id == guest_resume.id).first() is None
    assert db.query(Resume).filter(Resume.id == candidate_resume.id).first() is not None
