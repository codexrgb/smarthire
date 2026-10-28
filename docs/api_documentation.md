# SmartHire 2.0 — FastAPI REST Backend & Multi-Database Integration Guide

## 1. Overview & Architecture

The SmartHire 2.0 backend is built with **FastAPI**, **SQLAlchemy ORM**, and **Alembic**. It exposes modular REST endpoints that reuse validated classical NLP and machine learning pipelines without duplicating business logic.

```
                              ┌─────────────────────────────────────────┐
                              │  Client Requests (Vite / Streamlit UI)  │
                              └───────────────────┬─────────────────────┘
                                                  │ HTTPS / JWT
                                                  ▼
                              ┌─────────────────────────────────────────┐
                              │          FastAPI Application            │
                              │    CORS Middleware / RBAC Security      │
                              └───────┬──────────────────────┬──────────┘
                                      │                      │
             ┌────────────────────────┴────────┐    ┌────────┴────────────────────────┐
             │       Persisted Entities        │    │      Classical NLP / ML         │
             │   PostgreSQL / SQLAlchemy ORM   │    │      Feature Engineering        │
             │  (Users, Jobs, Resumes, Logs)   │    │  (Classification, TF-IDF Cosine)│
             └────────────────┬────────────────┘    └────────────────┬────────────────┘
                              │                                      │
                              ▼                                      ▼
             ┌─────────────────────────────────┐    ┌─────────────────────────────────┐
             │     Private File Storage        │    │    Models & Reports Cache       │
             │   (Collision-Free SHA-256)      │    │  (joblib pkls, provenance tags) │
             └─────────────────────────────────┘    └─────────────────────────────────┘
```

---

## 2. Environment Setup & Configuration

1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```
2. Configure environment variables in `.env`:
   - `SECRET_KEY`: Minimum 32-character hex secret for signing JWTs.
   - `DATABASE_URL`: Connection string. Supported configurations:
     - **SQLite (Development Default — Verified):** `sqlite:///./smarthire_dev.db`
     - **MySQL (Live Verified on MySQL 5.7+):** `mysql+pymysql://<user>:<password>@<host>:3306/<dbname>?charset=utf8mb4`
     - **PostgreSQL (Alembic Schema Ready — Unverified):** `postgresql://<user>:<password>@<host>:5432/<dbname>`
   - `CORS_ORIGINS`: Comma-separated list of allowed web origins (e.g., `http://localhost:3000,http://localhost:5173,http://localhost:8501`).
   - `STORAGE_DIR`: Path to the directory where resume binaries are stored out of public web access.

---

## 3. Database Migrations (Alembic)

SmartHire 2.0 uses Alembic for declarative schema versioning and zero-downtime migrations.

### Applying Migrations
To upgrade the database to the latest schema:
```bash
alembic upgrade head
```

### Rolling Back Migrations
To revert the most recent migration step:
```bash
alembic downgrade -1
```

To revert all migrations back to an empty base state:
```bash
alembic downgrade base
```

### Creating New Revisions
When updating SQLAlchemy models in `src/backend/models/`:
```bash
alembic revision --autogenerate -m "describe_changes_here"
```

### Dedicated MySQL Verification Workflow
To verify database migrations, schema structure, foreign keys, indexes, and isolated CRUD operations against a live MySQL instance without modifying production data:
```bash
python scripts/verify_mysql.py --url "mysql+pymysql://<user>:<password>@127.0.0.1:3306/<database>?charset=utf8mb4"
```
*(Or set the `MYSQL_TEST_DATABASE_URL` environment variable before running the script).*

---

## 4. REST API Endpoint Reference

### Health & Diagnostics

#### `GET /health` and `GET /api/v1/health`
Checks backend responsiveness and active database connection.
- **Auth:** None
- **Response `200 OK`:**
  ```json
  {
    "status": "healthy",
    "version": "2.0.0",
    "timestamp": "2026-10-26T22:46:40.779Z",
    "database_connected": true
  }
  ```

#### `GET /api/v1/models/status`
Returns loading status of ML model artifacts and dataset provenance markers.
- **Auth:** None
- **Response `200 OK`:**
  ```json
  {
    "models_loaded": {
      "classifier.pkl": true,
      "tfidf_vectorizer.pkl": true,
      "job_vectorizer.pkl": true,
      "job_vectors.pkl": true,
      "kmeans_clustering.pkl": true,
      "pca_2d.pkl": true
    },
    "best_classifier": "LogisticRegression",
    "dataset_provenance": {
      "overall_status": "demo_synthetic",
      "is_demo_mode": true,
      "ui_badge": "DEMO DATA MODE (SYNTHETIC)",
      "banner_message": "Warning: Using synthetic data. Results cannot establish real-world generalization."
    },
    "demo_warning_active": true
  }
  ```

---

### Resume Validation & Ingestion

#### `POST /api/v1/resumes/validate`
Dedicated multi-signal document validator that accurately distinguishes legitimate resumes from research papers, academic assignments, invoices, standalone certificates, and unreadable files. Does NOT persist records or files to storage.
- **Auth:** Optional
- **Form Data:**
  - `file`: Multipart binary document (`.pdf`, `.docx`, `.txt`).
  - `raw_text`: Direct text string.
  - `filename`: Optional document display name.
- **Response `200 OK`:**
  ```json
  {
    "is_valid": true,
    "confidence_category": "HIGH",
    "confidence_score": 0.95,
    "score_label": "Heuristic Validation Index",
    "is_calibrated_probability": false,
    "document_type": "resume",
    "rejection_reason": null,
    "user_message": "Resume validated successfully.",
    "detected_sections": ["Experience", "Education", "Skills"],
    "structural_signals": {
      "contact": { "has_email": true, "has_phone": true, "has_links": true },
      "sections": { "detected_sections": ["Experience", "Education", "Skills"], "section_count": 3 },
      "career": { "date_ranges_count": 2, "job_titles_count": 2 }
    }
  }
  ```

#### `POST /api/v1/resumes/parse`
Parses candidate resumes from uploaded documents (`.pdf`, `.docx`, `.txt`) or raw text strings.
**Crucial Validation Gate:** Enforces multi-signal document validation BEFORE saving to private storage, BEFORE creating database records, and BEFORE running ML classification or triggering job matching. If validation fails, returns `400 Bad Request` with structured feedback and persists nothing.
- **Auth:** Optional (`Bearer <token>`). If authenticated, associates record with candidate account.
- **Form Data:**
  - `file`: Multipart binary document (max 10MB; validated for `.pdf`, `.docx`, `.txt`).
  - `raw_text`: Direct text string (min 10 characters).
  - `filename`: Optional document display name.
- **Response `200 OK`:**
  ```json
  {
    "resume_id": "7bf31be8-f686-44ce-939e-26f58f4a2110",
    "original_filename": "alice_resume.pdf",
    "file_size_bytes": 48120,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "extracted_skills": ["Python", "Machine Learning", "SQL", "FastAPI"],
    "predicted_category": "Data Science",
    "category_confidence": 0.9412,
    "category_probabilities": {
      "Data Science": 0.9412,
      "Python Developer": 0.0381
    },
    "status_message": "Resume parsed successfully.",
    "extracted_text_preview": "Alice Smith, Software Engineer...",
    "validation": {
      "is_valid": true,
      "confidence_category": "HIGH",
      "confidence_score": 0.95,
      "score_label": "Heuristic Validation Index",
      "is_calibrated_probability": false,
      "document_type": "resume",
      "user_message": "Resume validated successfully.",
      "detected_sections": ["Experience", "Education", "Skills"]
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: When document validation fails (e.g. research papers, invoices, assignments, unreadable scans, corrupted files). Includes descriptive `detail` and prevents database insertion or storage.
- **Security & Privacy:** The raw document binary is saved to private storage using SHA-256 sharded subpaths only AFTER passing validation. No raw resume text, email addresses, or phone numbers are ever output to database logs or stdout.

---

### Matching & Job Recommendations

#### `POST /api/v1/matching/score`
Calculates transparent multi-factor compatibility score between a resume and job description.
- **Auth:** None
- **Request Body:**
  ```json
  {
    "resume_text": "Experienced Python engineer with SQL and machine learning...",
    "job_text": "Seeking Python engineer with machine learning and cloud...",
    "job_skills": "Python, SQL, Machine Learning, AWS",
    "text_similarity": 0.72
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "text_similarity": 0.72,
    "skill_overlap": 0.75,
    "experience_match": 0.80,
    "fit_score": 74.5,
    "matched_skills": ["Python", "SQL", "Machine Learning"],
    "missing_skills": ["AWS"],
    "score_label": "Heuristic Compatibility Index",
    "is_probability": false,
    "explanation": "Compatibility index computed from 50% text similarity, 30% skill overlap, and 20% experience compatibility. This is an empirical ranking index, not an interview probability."
  }
  ```
- **Scientific Integrity Guardrail:** The `fit_score` is explicitly defined as a multi-factor linear heuristic (`0.50 * text_similarity + 0.30 * skill_overlap + 0.20 * experience_match`). It is explicitly marked `is_probability: false` to ensure clients and user interfaces never misrepresent it as a hiring probability.

#### `POST /api/v1/jobs/recommend`
Ranks available job listings against candidate resume text using TF-IDF cosine similarity.
- **Auth:** None
- **Request Body:**
  ```json
  {
    "resume_text": "Full stack developer with React, TypeScript, Python, and PostgreSQL experience.",
    "top_n": 5,
    "category_filter": null
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "total_results": 5,
    "recommendations": [
      {
        "job_id": "JOB-104",
        "title": "Full Stack Engineer",
        "company": "TechCorp",
        "location": "Remote",
        "skills": "React, Python, PostgreSQL",
        "experience": "3+ years",
        "salary": "$110,000 - $130,000",
        "category": "Software Engineering",
        "similarity_score": 0.8124,
        "skill_match_pct": 85.0,
        "fit_score": 82.5
      }
    ]
  }
  ```

#### `GET /api/v1/jobs`
Lists job postings from the repository with optional filtering by title or location substring.
- **Parameters:** `title` (str), `location` (str), `limit` (int, default 20).

---

### Authentication & Role-Based Access Control (RBAC)

#### `POST /api/v1/auth/register`
Creates a candidate or recruiter account. Passwords hashed using bcrypt.
- **Request Body:**
  ```json
  {
    "email": "recruiter@example.com",
    "password": "StrongPassword123!",
    "full_name": "Alex Recruiter",
    "role": "recruiter"
  }
  ```
- **Response `201 Created`:** User profile without sensitive fields.

#### `POST /api/v1/auth/login`
Authenticates credentials and returns a signed HS256 JWT access token.
- **Request Body:**
  ```json
  {
    "email": "recruiter@example.com",
    "password": "StrongPassword123!"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "user": { ... }
  }
  ```

#### `GET /api/v1/auth/me`
Retrieves authenticated user profile.
- **Auth:** `Bearer <token>`

---

### Protected Recruiter Routes

#### `GET /api/v1/recruiter/candidates`
Lists candidate resumes. Strictly protected; unauthorized access returns `401 Unauthorized`, candidate role access returns `403 Forbidden`.
- **Auth:** `Bearer <token>` (Recruiter or Admin role only)
- **Audit Logging:** Every query automatically records an audit entry in `recruiter_actions`.

#### `POST /api/v1/recruiter/actions`
Logs recruiter workflow actions (shortlisting, rejecting, reviewing).
- **Auth:** `Bearer <token>` (Recruiter or Admin role only)

#### `GET /api/v1/recruiter/actions`
Retrieves chronological audit log of recruiter actions for compliance reviews.
- **Auth:** `Bearer <token>` (Recruiter or Admin role only)

---

## 5. Running the Backend Server

Start the FastAPI application via uvicorn:
```bash
uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is automatically available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON schema: `http://127.0.0.1:8000/openapi.json`
