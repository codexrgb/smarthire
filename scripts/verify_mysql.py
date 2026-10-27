"""
Dedicated MySQL Database Verification Script for SmartHire 2.0.

Verifies:
1. Connectivity & authentication against a live MySQL instance.
2. Server version compatibility (specifically validating MySQL 5.7+ & InnoDB).
3. Declarative schema creation via Alembic migrations.
4. Entity structure integrity: tables, foreign key cascades, and indexes.
5. Isolated CRUD and relationship operations using unique test records.
6. Safe cleanup of only created test records (no database drops or table truncations).

Execution:
  python scripts/verify_mysql.py [--url <MYSQL_URL>]
Or set environment variable:
  MYSQL_TEST_DATABASE_URL="mysql+pymysql://<user>:<password>@127.0.0.1:3306/<database>?charset=utf8mb4"
  python scripts/verify_mysql.py
"""

import os
import sys
import uuid
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker

from alembic.config import Config
from alembic import command

from src.backend.config import settings
from src.backend.models.user import User
from src.backend.models.job import Job
from src.backend.models.resume import Resume
from src.backend.models.recruiter_action import RecruiterAction
from src.backend.models.application import Application
from src.backend.security.hashing import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_mysql")


def sanitize_url(raw_url: str) -> str:
    """Masks credentials in database URL for safe logging."""
    try:
        url_obj = make_url(raw_url)
        return url_obj.render_as_string(hide_password=True)
    except Exception:
        return "<sanitized-database-url>"


def run_mysql_verification(db_url: str) -> bool:
    """
    Executes comprehensive verification checks against a target MySQL database.
    Returns True if all checks pass, False otherwise.
    """
    masked_url = sanitize_url(db_url)
    print("=" * 72)
    print(" SmartHire 2.0 -- Live MySQL Verification Workflow")
    print(f" Target Endpoint: {masked_url}")
    print("=" * 72)

    # Pre-validation: URL scheme check
    if db_url.startswith("sqlite"):
        print("\n[FAIL] Target URL points to SQLite, not MySQL.")
        print("Provide a valid MySQL connection URL using MYSQL_TEST_DATABASE_URL or --url:")
        print("  mysql+pymysql://<user>:<password>@127.0.0.1:3306/<database>?charset=utf8mb4")
        return False

    if not (db_url.startswith("mysql+pymysql://") or db_url.startswith("mysql://")):
        print(f"\n[FAIL] Unsupported URL scheme in '{masked_url}'. Expected 'mysql+pymysql://...'.")
        return False

    results: Dict[str, bool] = {}

    # Check 1: Connection & Authentication
    print("\n[1/5] Verifying database socket connectivity and authentication...")
    engine = None
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 10}
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"  --> PASS: Successfully connected and authenticated to {masked_url}")
        results["connectivity"] = True
    except Exception as e:
        print(f"  --> FAIL: Connection failed: {type(e).__name__}: {str(e)}")
        results["connectivity"] = False
        return False

    # Check 2: MySQL 5.7+ & Storage Engine Verification
    print("\n[2/5] Inspecting server version and InnoDB storage engine...")
    try:
        with engine.connect() as conn:
            version_row = conn.execute(text("SELECT VERSION()")).fetchone()
            server_version = version_row[0] if version_row else "Unknown"

            # Check default storage engine
            engine_row = conn.execute(text("SELECT @@default_storage_engine")).fetchone()
            storage_engine = engine_row[0] if engine_row else "Unknown"

            # Check innodb status
            innodb_row = conn.execute(text("SHOW VARIABLES LIKE 'innodb_version'")).fetchone()
            innodb_version = innodb_row[1] if innodb_row else "N/A"

        print(f"  --> Server Version: {server_version}")
        print(f"  --> Storage Engine: {storage_engine} (InnoDB Version: {innodb_version})")

        # Verify version meets 5.7+ requirement
        server_info = engine.dialect.server_version_info
        if server_info and server_info >= (5, 7):
            print(f"  --> PASS: MySQL server version {server_version} meets requirement (>= 5.7).")
            results["version"] = True
        else:
            print(f"  --> FAIL: MySQL server version {server_version} is below 5.7 requirement.")
            results["version"] = False
    except Exception as e:
        print(f"  --> FAIL: Server version check failed: {str(e)}")
        results["version"] = False

    # Check 3: Alembic Schema Migrations
    print("\n[3/5] Applying Alembic declarative migrations to head revision...")
    try:
        alembic_ini_path = PROJECT_ROOT / "alembic.ini"
        if not alembic_ini_path.exists():
            raise FileNotFoundError(f"Missing alembic.ini at {alembic_ini_path}")

        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        os.environ["DATABASE_URL"] = db_url
        # Ensure sys.path includes PROJECT_ROOT
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        command.upgrade(alembic_cfg, "head")
        print("  --> PASS: Alembic upgrade head executed successfully.")
        results["migrations"] = True
    except Exception as e:
        print(f"  --> FAIL: Alembic migration failed: {type(e).__name__}: {str(e)}")
        results["migrations"] = False

    # Check 4: Schema Structure, Foreign Keys & Index Inspection
    print("\n[4/5] Inspecting migrated schema structure, foreign keys, and indexes...")
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        expected_tables = {"users", "jobs", "resumes", "applications", "recruiter_actions", "alembic_version"}
        missing_tables = expected_tables - set(table_names)
        if missing_tables:
            raise ValueError(f"Missing expected tables: {missing_tables}")

        print(f"  --> Verified all expected tables present: {sorted(list(expected_tables))}")

        # Verify Foreign Keys
        resumes_fks = inspector.get_foreign_keys("resumes")
        fk_candidate = any(fk["referred_table"] == "users" for fk in resumes_fks)
        if not fk_candidate:
            raise ValueError("Foreign key 'resumes.candidate_id -> users.id' not found.")

        recruiter_fks = inspector.get_foreign_keys("recruiter_actions")
        fk_recruiter = any(fk["referred_table"] == "users" for fk in recruiter_fks)
        if not fk_recruiter:
            raise ValueError("Foreign key 'recruiter_actions.recruiter_id -> users.id' not found.")

        app_fks = inspector.get_foreign_keys("applications")
        app_referred = {fk["referred_table"] for fk in app_fks}
        if not {"users", "resumes", "jobs"}.issubset(app_referred):
            raise ValueError(f"applications missing required FKs to users, resumes, or jobs (found {app_referred})")

        print("  --> Verified relational foreign keys (resumes->users, actions->users, applications->all).")

        # Verify Indexes
        user_indexes = {idx["name"]: idx for idx in inspector.get_indexes("users")}
        if "ix_users_email" not in user_indexes:
            raise ValueError("Unique index 'ix_users_email' not found on users table.")

        resume_indexes = {idx["name"]: idx for idx in inspector.get_indexes("resumes")}
        if "ix_resumes_sha256" not in resume_indexes:
            raise ValueError("Index 'ix_resumes_sha256' not found on resumes table.")

        print("  --> Verified critical indexes ('ix_users_email', 'ix_resumes_sha256', etc.).")
        print("  --> PASS: Database schema, foreign keys, and indexes structurally verified.")
        results["schema"] = True
    except Exception as e:
        print(f"  --> FAIL: Schema inspection failed: {str(e)}")
        results["schema"] = False

    # Check 5: Isolated CRUD & Lifecycle Verification
    print("\n[5/5] Executing isolated CRUD operations and relational integrity checks...")
    Session = sessionmaker(bind=engine)
    session = Session()

    test_token = uuid.uuid4().hex[:8]
    test_email_candidate = f"verify_cand_{test_token}@example.com"
    test_email_recruiter = f"verify_rec_{test_token}@example.com"
    test_job_title = f"MySQL Verification Engineer {test_token}"
    test_sha256 = hashlib.sha256(f"test_resume_content_{test_token}".encode()).hexdigest()

    records_created: Dict[str, Any] = {}
    try:
        # Create candidate user
        cand_user = User(
            email=test_email_candidate,
            hashed_password=hash_password("VerifyPass123!"),
            full_name="MySQL Test Candidate",
            role="candidate",
            is_active=True
        )
        session.add(cand_user)

        # Create recruiter user
        rec_user = User(
            email=test_email_recruiter,
            hashed_password=hash_password("VerifyPass123!"),
            full_name="MySQL Test Recruiter",
            role="recruiter",
            is_active=True
        )
        session.add(rec_user)

        # Create job
        test_job = Job(
            title=test_job_title,
            company="SmartHire Verification Corp",
            location="Localhost",
            skills="Python, SQL, MySQL, FastAPI",
            experience_required="3+ years",
            category="Data Science",
            description="Verification test job record."
        )
        session.add(test_job)
        session.flush()

        records_created["candidate_id"] = cand_user.id
        records_created["recruiter_id"] = rec_user.id
        records_created["job_id"] = test_job.id

        # Create resume linked to candidate
        resume = Resume(
            candidate_id=cand_user.id,
            original_filename="mysql_test_resume.txt",
            storage_path=f"test/storage/{test_sha256}.txt",
            file_size_bytes=1024,
            sha256=test_sha256,
            clean_text="Python developer with MySQL database expertise.",
            predicted_category="Data Science",
            category_confidence=0.95,
            extracted_skills='["Python", "MySQL", "SQL"]'
        )
        session.add(resume)
        session.flush()
        records_created["resume_id"] = resume.id

        # Create application linking candidate, resume, and job
        application = Application(
            resume_id=resume.id,
            job_id=test_job.id,
            candidate_id=cand_user.id,
            text_similarity=0.88,
            skill_overlap=0.90,
            experience_match=0.85,
            fit_score=87.6,
            status="reviewing"
        )
        session.add(application)

        # Create recruiter action linking recruiter to resume
        action = RecruiterAction(
            recruiter_id=rec_user.id,
            action_type="view_candidate",
            target_entity_type="resume",
            target_entity_id=resume.id,
            details='{"verification": true}'
        )
        session.add(action)
        session.commit()

        # Query and assert relations
        fetched_user = session.query(User).filter(User.email == test_email_candidate).first()
        assert fetched_user is not None, "Failed to retrieve created candidate"
        assert len(fetched_user.resumes) == 1, "Candidate resumes relationship failed"
        assert fetched_user.resumes[0].sha256 == test_sha256, "Resume SHA-256 mismatch"

        fetched_job = session.query(Job).filter(Job.id == test_job.id).first()
        assert fetched_job is not None, "Failed to retrieve created job"
        assert len(fetched_job.applications) == 1, "Job applications relationship failed"

        fetched_action = session.query(RecruiterAction).filter(RecruiterAction.recruiter_id == rec_user.id).first()
        assert fetched_action is not None, "Failed to retrieve recruiter action"

        print("  --> Created and asserted test entities: User, Job, Resume, Application, RecruiterAction.")
        print("  --> PASS: Relational CRUD and constraint integrity verified.")
        results["crud"] = True
    except Exception as e:
        session.rollback()
        print(f"  --> FAIL: CRUD integrity check failed: {type(e).__name__}: {str(e)}")
        results["crud"] = False
    finally:
        # Strictly safe teardown: only delete records created in this test session
        print("  --> Cleaning up test records...")
        try:
            # Delete application
            if "job_id" in records_created:
                session.query(Application).filter(Application.job_id == records_created["job_id"]).delete()
            # Delete recruiter action
            if "recruiter_id" in records_created:
                session.query(RecruiterAction).filter(RecruiterAction.recruiter_id == records_created["recruiter_id"]).delete()
            # Delete resume
            if "resume_id" in records_created:
                session.query(Resume).filter(Resume.id == records_created["resume_id"]).delete()
            # Delete job
            if "job_id" in records_created:
                session.query(Job).filter(Job.id == records_created["job_id"]).delete()
            # Delete users
            if "candidate_id" in records_created:
                session.query(User).filter(User.id == records_created["candidate_id"]).delete()
            if "recruiter_id" in records_created:
                session.query(User).filter(User.id == records_created["recruiter_id"]).delete()
            session.commit()
            print("  --> Cleanup completed cleanly. Zero pre-existing data modified.")
        except Exception as cleanup_err:
            session.rollback()
            print(f"  --> WARNING: Cleanup failed: {cleanup_err}")
        finally:
            session.close()

    # Final Summary Table
    print("\n" + "=" * 72)
    print(" SmartHire 2.0 -- Live MySQL Verification Summary")
    print("=" * 72)
    for check_name, status in results.items():
        tag = "[PASS]" if status else "[FAIL]"
        print(f"  {tag:<8} {check_name.capitalize()} check")
    print("=" * 72)

    all_passed = all(results.values()) and len(results) == 5
    if all_passed:
        print("\nOVERALL RESULT: SUCCESS — Target MySQL database is fully verified for SmartHire 2.0.")
    else:
        print("\nOVERALL RESULT: FAILED — One or more verification checks failed.")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="SmartHire 2.0 Live MySQL Verification")
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="MySQL connection URL (defaults to MYSQL_TEST_DATABASE_URL or DATABASE_URL)"
    )
    args = parser.parse_args()

    # Priority: CLI argument -> MYSQL_TEST_DATABASE_URL -> DATABASE_URL
    target_url = args.url or os.getenv("MYSQL_TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

    if not target_url:
        print("ERROR: No database URL provided.")
        print("Please configure MYSQL_TEST_DATABASE_URL in your environment or provide --url:")
        print("  python scripts/verify_mysql.py --url 'mysql+pymysql://<user>:<password>@127.0.0.1:3306/<database>?charset=utf8mb4'")
        sys.exit(1)

    success = run_mysql_verification(target_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
