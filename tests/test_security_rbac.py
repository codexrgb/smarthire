"""
Security & Role-Based Access Control (RBAC) Regression Tests for SmartHire 2.0.
Verifies production secret enforcement, JWT verification & expiration,
candidate cross-tenant isolation (preventing IDOR), recruiter role boundaries,
storage path traversal protection, and password length guardrails.
"""

import io
import json
import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.main import app
from src.backend.config import Settings
from src.backend.database import get_db, Base
from src.backend.models.user import User
from src.backend.models.resume import Resume
from src.backend.security.hashing import hash_password
from src.backend.security.auth import create_access_token
from src.backend.storage.base import storage_service, sanitize_filename


# In-memory isolated database for security tests
SECURITY_TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SECURITY_TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module", autouse=True)
def init_security_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def candidate_a(db_session):
    """Candidate User A."""
    user = User(
        email="candidate.alpha@example.com",
        hashed_password=hash_password("CandidateSecret123!"),
        full_name="Candidate Alpha",
        role="candidate",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "full_name": user.full_name}
    )
    return user, token


@pytest.fixture
def candidate_b(db_session):
    """Candidate User B."""
    user = User(
        email="candidate.beta@example.com",
        hashed_password=hash_password("CandidateSecret123!"),
        full_name="Candidate Beta",
        role="candidate",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "full_name": user.full_name}
    )
    return user, token


@pytest.fixture
def recruiter_user(db_session):
    """Recruiter User."""
    user = User(
        email="recruiter.alpha@example.com",
        hashed_password=hash_password("RecruiterSecret123!"),
        full_name="Recruiter Alpha",
        role="recruiter",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "full_name": user.full_name}
    )
    return user, token


# =====================================================================
# 1. Production Configuration & Secret Enforcement
# =====================================================================

def test_production_secret_guardrail_rejects_default_secret():
    """SmartHire must refuse startup in production mode if default secret key is used."""
    prod_settings = Settings()
    prod_settings.ENVIRONMENT = "production"
    prod_settings.SECRET_KEY = prod_settings.DEV_DEFAULT_SECRET

    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.validate_production_configuration()
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(exc_info.value)
    assert "insecure development default" in str(exc_info.value)


def test_production_secret_guardrail_rejects_short_secret():
    """SmartHire must refuse startup in production mode if secret key is shorter than 32 chars."""
    prod_settings = Settings()
    prod_settings.ENVIRONMENT = "production"
    prod_settings.SECRET_KEY = "short-key-123"

    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.validate_production_configuration()
    assert "shorter than 32 characters" in str(exc_info.value)


def test_production_secret_guardrail_accepts_secure_secret():
    """Production mode with high-entropy secret succeeds."""
    prod_settings = Settings()
    prod_settings.ENVIRONMENT = "production"
    prod_settings.SECRET_KEY = "c8f2b7a9e0123456789abcdef0123456789abcdef0123456789abcdef012345"
    prod_settings.validate_production_configuration()  # Must not raise


# =====================================================================
# 2. JWT Verification, Expiration & Invalid Signature Handling
# =====================================================================

def test_expired_jwt_token_rejected_with_401(client, candidate_a):
    """Expired JWT access token must return HTTP 401 Unauthorized."""
    user, _ = candidate_a
    expired_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=-5)  # Expired 5 minutes ago
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_tampered_jwt_signature_rejected_with_401(client, candidate_a):
    """Tampered or invalid JWT signature must return HTTP 401 Unauthorized."""
    _, valid_token = candidate_a
    parts = valid_token.split(".")
    tampered_sig = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_malformed_jwt_payload_rejected_with_401(client):
    """JWT token missing sub or role claims must return HTTP 401 Unauthorized."""
    from src.backend.config import settings
    import jwt
    # Token without 'sub' and 'role'
    bad_token = jwt.encode({"random_claim": "hello"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {bad_token}"}
    )
    assert response.status_code == 401


# =====================================================================
# 3. Cross-Tenant Candidate Isolation & Resume Privacy
# =====================================================================

def test_cross_tenant_isolation_job_recommendations(client, db_session, candidate_a, candidate_b):
    """
    Candidate B must be FORBIDDEN (403) from accessing Candidate A's resume in job recommendations.
    Prevents Insecure Direct Object Reference (IDOR).
    """
    user_a, token_a = candidate_a
    user_b, token_b = candidate_b

    # Create resume owned by Candidate A
    resume_a = Resume(
        candidate_id=user_a.id,
        original_filename="candidate_a_secret_resume.pdf",
        storage_path="mock/path/a.pdf",
        file_size_bytes=1024,
        sha256="a" * 64,
        clean_text="Python machine learning engineer with deep expertise in neural networks.",
        predicted_category="Data Science",
        category_confidence=0.95,
        extracted_skills=json.dumps(["Python", "Machine Learning"])
    )
    db_session.add(resume_a)
    db_session.commit()
    db_session.refresh(resume_a)

    # 1. Unauthenticated request to Candidate A's resume -> 401 Unauthorized
    unauth_resp = client.post("/api/v1/jobs/recommend", json={"resume_id": resume_a.id, "top_n": 3})
    assert unauth_resp.status_code == 401

    # 2. Candidate B (different user) attempting to use Candidate A's resume_id -> 403 Forbidden
    cand_b_resp = client.post(
        "/api/v1/jobs/recommend",
        json={"resume_id": resume_a.id, "top_n": 3},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert cand_b_resp.status_code == 403
    assert "Access denied" in cand_b_resp.json()["detail"]

    # 3. Candidate A (owner) accessing own resume -> 200 OK
    cand_a_resp = client.post(
        "/api/v1/jobs/recommend",
        json={"resume_id": resume_a.id, "top_n": 3},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert cand_a_resp.status_code == 200
    assert "recommendations" in cand_a_resp.json()


def test_cross_tenant_isolation_matching_score(client, db_session, candidate_a, candidate_b):
    """Candidate B must be FORBIDDEN (403) from matching against Candidate A's resume."""
    user_a, token_a = candidate_a
    user_b, token_b = candidate_b

    resume_a = Resume(
        candidate_id=user_a.id,
        original_filename="candidate_a_portfolio.pdf",
        storage_path="mock/path/a2.pdf",
        file_size_bytes=1024,
        sha256="b" * 64,
        clean_text="Senior Java Backend Architect with Spring Boot and Kubernetes.",
        predicted_category="Java Developer",
        category_confidence=0.92,
        extracted_skills=json.dumps(["Java", "Spring Boot"])
    )
    db_session.add(resume_a)
    db_session.commit()
    db_session.refresh(resume_a)

    payload = {
        "resume_id": resume_a.id,
        "job_text": "Senior Java developer position with Spring Boot and AWS.",
        "job_skills": "Java, Spring Boot, AWS"
    }

    # Candidate B blocked
    response_b = client.post(
        "/api/v1/matching/score",
        json=payload,
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response_b.status_code == 403

    # Candidate A allowed
    response_a = client.post(
        "/api/v1/matching/score",
        json=payload,
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response_a.status_code == 200
    assert response_a.json()["is_probability"] is False


def test_recruiter_access_to_candidate_resume(client, db_session, candidate_a, recruiter_user):
    """Recruiters are authorized to run recommendations and score matches against candidate resumes."""
    user_a, _ = candidate_a
    _, recruiter_token = recruiter_user

    resume_a = Resume(
        candidate_id=user_a.id,
        original_filename="reviewed_resume.pdf",
        storage_path="mock/path/a3.pdf",
        file_size_bytes=1024,
        sha256="c" * 64,
        clean_text="DevOps Cloud Engineer with Docker, Kubernetes, Terraform, and CI/CD.",
        predicted_category="DevOps Engineer",
        category_confidence=0.88,
        extracted_skills=json.dumps(["Docker", "Kubernetes", "Terraform"])
    )
    db_session.add(resume_a)
    db_session.commit()
    db_session.refresh(resume_a)

    # Recruiter running recommendation on Candidate A's resume succeeds
    rec_resp = client.post(
        "/api/v1/jobs/recommend",
        json={"resume_id": resume_a.id, "top_n": 3},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_resp.status_code == 200


def test_guest_unowned_resume_publicly_recommendable(client, db_session):
    """Guest / anonymous resumes (candidate_id is None) can be scored by any client without authentication."""
    guest_resume = Resume(
        candidate_id=None,
        original_filename="guest_demo_resume.txt",
        storage_path="mock/path/guest.txt",
        file_size_bytes=512,
        sha256="d" * 64,
        clean_text="Software intern with JavaScript, React, HTML, CSS, and Git.",
        predicted_category="Web Development",
        category_confidence=0.85,
        extracted_skills=json.dumps(["JavaScript", "React", "Git"])
    )
    db_session.add(guest_resume)
    db_session.commit()
    db_session.refresh(guest_resume)

    response = client.post("/api/v1/jobs/recommend", json={"resume_id": guest_resume.id, "top_n": 2})
    assert response.status_code == 200


# =====================================================================
# 4. Candidate My-Resumes, Detail & Delete Isolation
# =====================================================================

def test_my_resumes_endpoint_strict_isolation(client, db_session, candidate_a, candidate_b):
    """Candidate A and Candidate B only see their own resumes via GET /resumes/my-resumes."""
    user_a, token_a = candidate_a
    user_b, token_b = candidate_b

    res_a = Resume(
        candidate_id=user_a.id,
        original_filename="a_resume.pdf",
        storage_path="mock/a.pdf",
        file_size_bytes=500,
        sha256="e" * 64,
        clean_text="Resume A text",
        predicted_category="Data Science",
        category_confidence=0.9,
        extracted_skills="[]"
    )
    res_b = Resume(
        candidate_id=user_b.id,
        original_filename="b_resume.pdf",
        storage_path="mock/b.pdf",
        file_size_bytes=600,
        sha256="f" * 64,
        clean_text="Resume B text",
        predicted_category="Java Developer",
        category_confidence=0.9,
        extracted_skills="[]"
    )
    db_session.add_all([res_a, res_b])
    db_session.commit()

    # Candidate A gets only A's resumes
    resp_a = client.get("/api/v1/resumes/my-resumes", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a.status_code == 200
    ids_a = [item["id"] for item in resp_a.json()]
    assert res_a.id in ids_a
    assert res_b.id not in ids_a

    # Candidate B gets only B's resumes
    resp_b = client.get("/api/v1/resumes/my-resumes", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 200
    ids_b = [item["id"] for item in resp_b.json()]
    assert res_b.id in ids_b
    assert res_a.id not in ids_b


def test_resume_detail_and_delete_authorization(client, db_session, candidate_a, candidate_b):
    """Candidate B cannot view or delete Candidate A's resume."""
    user_a, token_a = candidate_a
    _, token_b = candidate_b

    res_a = Resume(
        candidate_id=user_a.id,
        original_filename="a_private_doc.pdf",
        storage_path="mock/a_priv.pdf",
        file_size_bytes=1000,
        sha256="1" * 64,
        clean_text="Highly confidential candidate details",
        predicted_category="Operations",
        category_confidence=0.9,
        extracted_skills=json.dumps(["Management"])
    )
    db_session.add(res_a)
    db_session.commit()
    db_session.refresh(res_a)

    # 1. Candidate B cannot view Candidate A's resume
    view_resp_b = client.get(f"/api/v1/resumes/{res_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert view_resp_b.status_code == 403

    # 2. Candidate B cannot delete Candidate A's resume
    del_resp_b = client.delete(f"/api/v1/resumes/{res_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_resp_b.status_code == 403

    # 3. Candidate A can view own resume
    view_resp_a = client.get(f"/api/v1/resumes/{res_a.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert view_resp_a.status_code == 200
    assert view_resp_a.json()["id"] == res_a.id

    # 4. Candidate A can delete own resume
    del_resp_a = client.delete(f"/api/v1/resumes/{res_a.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_resp_a.status_code == 200

    # 5. Verify deleted from DB
    assert db_session.query(Resume).filter(Resume.id == res_a.id).first() is None


# =====================================================================
# 5. Storage Path Traversal Prevention
# =====================================================================

def test_private_file_storage_blocks_path_traversal():
    """PrivateFileStorage must reject traversal attacks attempting to read or delete outside storage dir."""
    with pytest.raises(PermissionError):
        storage_service.get_file("../../etc/passwd")

    with pytest.raises(PermissionError):
        storage_service.delete_file("../../../windows/system32/cmd.exe")


def test_sanitize_filename_cleans_traversal_and_null_bytes():
    """Filename sanitizer strips dangerous directory characters and null bytes."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\secret.pdf") == "secret.pdf"
    assert sanitize_filename("doc\x00_malicious.txt") == "doc_malicious.txt"
    assert sanitize_filename("...hidden.pdf") == "hidden.pdf"


# =====================================================================
# 6. Password Length Limit & Validation
# =====================================================================

def test_password_longer_than_72_chars_rejected(client):
    """Passwords exceeding 72 characters must be rejected to prevent silent bcrypt truncation."""
    oversized_password = "P" * 75 + "1!Aa"
    payload = {
        "email": "toolong@example.com",
        "password": oversized_password,
        "full_name": "Too Long",
        "role": "candidate"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
