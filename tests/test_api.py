"""
FastAPI Backend & Persistence Test Suite for SmartHire 2.0.
Verifies endpoints, ML reuse, RBAC authorization, upload validation, and database operations.
"""

import io
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.main import app
from src.backend.database import get_db, Base
from src.backend.models.user import User
from src.backend.models.resume import Resume
from src.backend.models.job import Job
from src.backend.models.recruiter_action import RecruiterAction
from src.backend.security.hashing import hash_password
from src.backend.security.auth import create_access_token


# Set up isolated in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Creates database tables for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provides a transactional database session rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
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
def candidate_token(db_session):
    """Creates a candidate user and returns a valid JWT token."""
    user = User(
        email="candidate.test@example.com",
        hashed_password=hash_password("CandidateSecret123!"),
        full_name="Jane Candidate",
        role="candidate",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "full_name": user.full_name}
    )
    return token, user


@pytest.fixture
def recruiter_token(db_session):
    """Creates a recruiter user and returns a valid JWT token."""
    user = User(
        email="recruiter.test@example.com",
        hashed_password=hash_password("RecruiterSecret123!"),
        full_name="John Recruiter",
        role="recruiter",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "full_name": user.full_name}
    )
    return token, user


# --- Test 1: Health & System Endpoints ---

def test_health_check(client):
    """GET /health must return 200 with status=healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert "timestamp" in data
    assert "database_connected" in data


def test_api_v1_health(client):
    """GET /api/v1/health must return 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_models_status(client):
    """GET /api/v1/models/status must expose artifact availability and provenance."""
    response = client.get("/api/v1/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "models_loaded" in data
    assert "best_classifier" in data
    assert "dataset_provenance" in data
    assert "demo_warning_active" in data
    assert isinstance(data["models_loaded"], dict)


# --- Test 2: Heuristic Fit Score & Matching ---

def test_matching_score_valid(client):
    """POST /api/v1/matching/score must compute heuristic index and flag is_probability=False."""
    payload = {
        "resume_text": "Experienced Python Software Engineer with machine learning, SQL, pandas, and cloud architecture.",
        "job_text": "Looking for a Senior Python Developer with machine learning, SQL, and AWS cloud experience.",
        "job_skills": "Python, SQL, Machine Learning, AWS"
    }
    response = client.post("/api/v1/matching/score", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "fit_score" in data
    assert "text_similarity" in data
    assert "skill_overlap" in data
    assert "experience_match" in data
    assert "matched_skills" in data
    assert "missing_skills" in data
    assert 0.0 <= data["fit_score"] <= 100.0

    # Critical requirement: MUST NOT be presented as a hiring probability
    assert data["is_probability"] is False
    assert "Heuristic" in data["score_label"]
    assert "index" in data["explanation"].lower()


def test_matching_score_short_input(client):
    """POST /api/v1/matching/score must reject payloads with <10 characters."""
    payload = {
        "resume_text": "Short",
        "job_text": "Too short"
    }
    response = client.post("/api/v1/matching/score", json=payload)
    assert response.status_code in [400, 422]


# --- Test 3: Job Recommendations ---

def test_job_recommendation_valid(client):
    """POST /api/v1/jobs/recommend ranks jobs against candidate text."""
    payload = {
        "resume_text": "Senior Data Scientist proficient in Python, machine learning, NLP, and deep learning algorithms.",
        "top_n": 5
    }
    response = client.post("/api/v1/jobs/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "total_results" in data
    assert isinstance(data["recommendations"], list)
    if data["total_results"] > 0:
        first = data["recommendations"][0]
        assert "job_id" in first
        assert "title" in first
        assert "fit_score" in first


def test_job_recommendation_short_text(client):
    """POST /api/v1/jobs/recommend rejects short input text."""
    payload = {"resume_text": "Short"}
    response = client.post("/api/v1/jobs/recommend", json=payload)
    assert response.status_code in [400, 422]


def test_jobs_list(client):
    """GET /api/v1/jobs retrieves jobs list."""
    response = client.get("/api/v1/jobs?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# --- Test 4: Resume Parsing & Storage ---

def test_resume_parse_from_text(client, candidate_token):
    """POST /api/v1/resumes/parse with raw text creates a record and extracts features."""
    token, _ = candidate_token
    resume_text = (
        "Alice Smith, Data Engineer with 4 years experience in Python, Apache Spark, "
        "SQL databases, Docker, and AWS pipeline construction."
    )
    response = client.post(
        "/api/v1/resumes/parse",
        data={"raw_text": resume_text, "filename": "alice_resume.txt"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "resume_id" in data
    assert "sha256" in data
    assert "extracted_skills" in data
    assert "predicted_category" in data
    assert "Python" in data["extracted_skills"] or "SQL" in data["extracted_skills"]


def test_resume_parse_file_upload(client):
    """POST /api/v1/resumes/parse with .txt file upload."""
    content = b"John Doe - Senior Software Engineer - Java, Python, Spring Boot, Kubernetes, Git."
    file_obj = io.BytesIO(content)

    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("john_doe_resume.txt", file_obj, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "john_doe_resume.txt"
    assert data["file_size_bytes"] == len(content)
    assert len(data["sha256"]) == 64


def test_resume_parse_invalid_extension(client):
    """POST /api/v1/resumes/parse rejects forbidden file extensions (.exe)."""
    fake_exe = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00")
    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("malicious.exe", fake_exe, "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]


def test_resume_parse_empty_file(client):
    """POST /api/v1/resumes/parse rejects 0-byte file."""
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("empty.txt", empty_file, "text/plain")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_resume_parse_oversized_file(client, monkeypatch):
    """POST /api/v1/resumes/parse rejects files exceeding size limit."""
    from src.backend.config import settings
    # Temporarily set max size to 100 bytes for test
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 100)
    oversized = io.BytesIO(b"A" * 200)

    response = client.post(
        "/api/v1/resumes/parse",
        files={"file": ("big.txt", oversized, "text/plain")}
    )
    assert response.status_code == 413
    assert "exceeds maximum" in response.json()["detail"]


# --- Test 5: Authentication & RBAC Authorization ---

def test_auth_register_and_login(client):
    """User registration and login flow issuing valid JWT."""
    register_payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "full_name": "New User",
        "role": "candidate"
    }
    reg_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "newuser@example.com"
    assert "id" in user_data

    # Duplicate registration should return 409 Conflict
    dup_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert dup_resp.status_code == 409

    # Login
    login_payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!"
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Profile inspection
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "newuser@example.com"


def test_auth_login_invalid_password(client):
    """Login with invalid password must return 401 Unauthorized."""
    payload = {
        "email": "candidate.test@example.com",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_candidate_forbidden_from_recruiter_endpoint(client, candidate_token):
    """Candidate role accessing recruiter endpoints must return 403 Forbidden."""
    token, _ = candidate_token
    response = client.get(
        "/api/v1/recruiter/candidates",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_unauthenticated_forbidden_from_recruiter_endpoint(client):
    """Unauthenticated request to protected endpoint must return 401 Unauthorized."""
    response = client.get("/api/v1/recruiter/candidates")
    assert response.status_code == 401


def test_recruiter_access_allowed(client, recruiter_token):
    """Recruiter role accessing recruiter endpoints must succeed (200 OK)."""
    token, _ = recruiter_token
    response = client.get(
        "/api/v1/recruiter/candidates",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_recruiter_action_audit_logging(client, recruiter_token):
    """Recruiter actions are stored as audit logs."""
    token, _ = recruiter_token
    log_payload = {
        "action_type": "view_candidate",
        "target_entity_type": "resume",
        "target_entity_id": "test-resume-123",
        "details": json.dumps({"note": "Candidate shortlisted for technical round"})
    }
    response = client.post(
        "/api/v1/recruiter/actions",
        json=log_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "view_candidate"
    assert data["target_entity_id"] == "test-resume-123"

    # List actions
    list_resp = client.get(
        "/api/v1/recruiter/actions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
