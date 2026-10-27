# SmartHire 2.0 — Live Demonstration & Evaluation Guide

This guide provides a verified, step-by-step 5–7 minute demonstration walkthrough of **SmartHire 2.0**, covering the complete candidate-to-recruiter workflow against the running FastAPI REST backend and React Vite frontend.

---

## 1. Prerequisites & Startup Commands

Ensure you have Python 3.10+ and Node.js 18+ installed. All commands below have been tested and verified on Windows PowerShell.

### Step 1: Environment & Backend Startup

Open a terminal at the project root (`smarthire/`):

```powershell
# 1. Activate Python virtual environment (if using .venv)
# .venv\Scripts\activate  (or source .venv/bin/activate on Linux/macOS)

# 2. Apply database migrations via Alembic (initializes SQLite schema)
alembic upgrade head

# 3. Start the FastAPI REST API server
python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Backend Health Check:** `http://127.0.0.1:8000/health` (returns `{"status":"healthy","database_connected":true}`)
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **ReDoc Reference:** `http://127.0.0.1:8000/redoc`

### Step 2: Frontend SPA Startup

Open a second terminal at the project root:

```powershell
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies (if first time)
npm install

# 3. Launch Vite development server
npm run dev
```

- **Frontend Application URL:** `http://localhost:5173`

*(Optional) Legacy Streamlit Interface:*  
If you wish to demonstrate the original Phase 1 analytical dashboard alongside SmartHire 2.0, open a third terminal and run:
```powershell
streamlit run app/streamlit_app.py
```
This serves the standalone Streamlit analytical app at `http://localhost:8501`.

---

## 2. Structured 5–7 Minute Demo Walkthrough

Follow this scripted flow for live demos, interview presentations, or stakeholder evaluations.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        5-7 MINUTE DEMO TIMELINE                        │
├────────────┬─────────────────────────────┬─────────────────────────────┤
│ Timestamp  │ Stage                       │ Key Highlights              │
├────────────┼─────────────────────────────┼─────────────────────────────┤
│ 0:00 - 1:00│ Candidate Registration      │ Role selection, JWT auth    │
│ 1:00 - 2:30│ Resume Upload & NLP Parser  │ SHA-256 hash, ML category   │
│ 2:30 - 3:45│ Job Compatibility Details   │ 3-factor score, skill tags  │
│ 3:45 - 4:30│ Portfolio & Profile Editing │ Deletion modal, update name │
│ 4:30 - 5:15│ RBAC Security Boundary      │ 403 Forbidden candidate test│
│ 5:15 - 6:30│ Recruiter Pipeline Actions  │ PII masking, Shortlist action│
└────────────┴─────────────────────────────┴─────────────────────────────┘
```

### Phase 1: Candidate Onboarding & Portal Access (0:00 – 1:00)
1. Open your browser and navigate to `http://localhost:5173/auth`.
2. Click **"Register now"** to toggle to the registration form.
3. Select the **"Candidate"** role pill.
4. Enter candidate details:
   - **Full Name:** `Alice Candidate`
   - **Email:** `alice.demo@example.com`
   - **Password:** `DemoPassword123!`
5. Click **"Create Account"**.
6. **Observation:** You are automatically redirected to `http://localhost:5173/dashboard`. The header displays `"Welcome back, Alice Candidate"` with a `"Candidate Portal Active"` badge and a synthetic data warning banner.

### Phase 2: Resume Upload & Classical NLP Parsing (1:00 – 2:30)
1. Click **"Analyze Resume"** in the sidebar navigation or candidate action card (`/resumes/analyze`).
2. Upload a sample resume file (e.g., `frontend/e2e/fixtures/synthetic_resume.txt`) or paste raw resume text:
   ```text
   Senior Python Developer with 6 years of experience in FastAPI, Docker, SQL, and Machine Learning.
   Proven track record designing scalable microservices, building TF-IDF recommendation systems,
   and deploying distributed systems on AWS and Kubernetes.
   ```
3. Click **"Run Analysis"**.
4. **Observation:**
   - **Verification Fingerprint:** Displays the unique SHA-256 checksum (e.g. `2403d1c9...`).
   - **Predicted Job Category:** Classical ML classifier predicts `Data Science` or `Python Developer` with a model confidence score (e.g. `94.1%`).
   - **Extracted Technical Skills:** Clean, normalized skill chips (`Python`, `Docker`, `SQL`, `Machine Learning`, `AWS`, `FastAPI`).
   - **Ranked Job Recommendations:** Returns real-time recommendations ranked by cosine similarity against the job posting corpus.

### Phase 3: Transparent 3-Factor Job Match Details (2:30 – 3:45)
1. Under **"Top Ranked Job Recommendations for this Resume"**, click the **"Details"** button on the first job card.
2. **Observation on `/matching`:**
   - **Overall Alignment Score:** Transparent heuristic compatibility index (e.g. `78.5%`).
   - **3-Factor Breakdown Cards:**
     - **Text Similarity (50%):** TF-IDF Cosine Similarity score.
     - **Skill Overlap (30%):** Lexical Jaccard intersection of technical skills.
     - **Experience Match (20%):** Normalized years of experience heuristic.
   - **Skills Comparison:** Visual green chips for **Matched Skills** and gray chips for **Missing Skills (Skill Gap)**.
   - **Academic Guardrail Notice:** Clearly highlights that this score is an empirical weighted heuristic (`is_probability: false`) and does not represent an interview or hiring probability.

### Phase 4: Candidate Portfolio & Profile Management (3:45 – 4:30)
1. Navigate back to `/resumes/analyze`, upload a temporary file (e.g. `frontend/e2e/fixtures/temporary_resume.txt`), and click **"Run Analysis"**.
2. Navigate to **"Dashboard"** (`/dashboard`).
3. Scroll to **"Your Uploaded Resumes"**:
   - Both uploaded resumes appear with file size, category badge, and upload timestamp.
4. Click the **Delete** button (trash icon) next to `temporary_resume.txt`.
5. In the native browser confirmation prompt, click **"OK"**.
6. **Observation:** A success toast confirms deletion; `temporary_resume.txt` is removed from both the UI and private sharded storage, while `synthetic_resume.txt` remains intact.
7. Navigate to **"Settings"** (`/settings`):
   - Click **"Edit Profile"**, update Full Name to `Alice Candidate Updated`, and click **"Save Changes"**.
   - The user profile refreshes immediately across the UI.

### Phase 5: RBAC Security Boundary Demonstration (4:30 – 5:15)
1. While still logged in as Alice (Candidate), attempt to manually navigate to the recruiter candidate pipeline URL:
   `http://localhost:5173/recruiter/candidates`
2. **Observation:**
   - The route guard intercepts the request immediately.
   - Displays a clean **403 Forbidden** security screen:
     > *"Operation requires recruiter or administrator privileges. Candidate accounts cannot view recruiter records."*
   - Zero candidate records or database rows are leaked.
3. Navigate to **"Settings"** and click **"Sign Out"**.

### Phase 6: Recruiter Command Center & Pipeline Evaluation (5:15 – 6:30)
1. Navigate to `/auth`, click **"Register now"**, and select the **"Recruiter"** role pill:
   - **Full Name:** `Bob Recruiter`
   - **Email:** `bob.recruiter@example.com`
   - **Password:** `RecruiterPass123!`
2. Click **"Create Account"**.
3. **Observation on `/recruiter/dashboard`:**
   - Displays the **Recruiter Command Center** with live pipeline metrics: Total Candidates, Active Resumes, and Action Audits.
4. Navigate to **"Candidate Pipeline"** (`/recruiter/candidates`).
5. **Inspect Candidate Modal:**
   - Click the **"Inspect"** button on Alice's candidate row.
   - The inspection modal reveals extracted skills and a **PII-Sanitized Text Preview** where email addresses and phone numbers are automatically redacted (`[EMAIL MASKED]`, `[PHONE MASKED]`).
   - Close the modal.
6. **Candidate Workflow Actions:**
   - Click **"Shortlist"** on Alice's row.
   - **Observation:** A success notification appears, and the status badge updates instantly to **"Shortlisted"**. An immutable audit record is stored in `recruiter_actions`.
   - Click **"Decline"** on another row to demonstrate immediate pipeline triage.

---

## 3. Automated 1-Click Verification (Playwright E2E)

If you prefer to execute this entire 10-flow demonstration automatically in a headless browser:

```powershell
cd frontend
npx playwright test
```

- Automatically boots FastAPI and Vite servers.
- Executes all 10 candidate and recruiter flows in Chromium in ~30 seconds.
- Captures fresh visual regression screenshots in `reports/screenshots/`.

---

## 4. Technical Guardrails & Disclosures

### 1. Synthetic Data & Provenance Disclosure
- The current datasets in `data/raw/` contain synthetic templates where domain keywords appear in the opening sentences.
- Model accuracy scores on this data reflect template memorization and cannot guarantee real-world generalization.
- To verify authentic data ingestion status, run:
  ```powershell
  python src/data/ingest_dataset.py --check-status
  ```
- See `docs/dataset_ingestion.md` for instructions on registering authentic open-source datasets.

### 2. Heuristic Match Score Formula
- The fit score is computed using a deterministic weighted linear index:
  $$\text{Fit Score} = (0.50 \times \text{TextSimilarity}) + (0.30 \times \text{SkillOverlap}) + (0.20 \times \text{ExperienceMatch}) \times 100$$
- The API explicitly returns `is_probability: false`.
- **Notice:** This index is an empirical ranking metric and must never be portrayed as a statistical probability of interview invitation or employment.

### 3. Guest Resume Retention Policy & Execution Model
- **Policy:** Resumes uploaded without an authenticated session (`candidate_id IS NULL`) are classified as guest uploads and become eligible for deletion after 24 hours (`uploaded_at < UTC now - 24 hours`). Resumes uploaded by registered candidates (`candidate_id IS NOT NULL`) are permanently preserved until explicitly deleted by the owner.
- **Implemented & Verified:** The retention service (`src/backend/services/retention.py`), cutoff calculation, candidate record preservation, deduplication reference checks, file unlinking, and dry-run CLI reporting are fully implemented and verified with 7 automated tests (`tests/test_retention.py`).
- **Operational Distinction:** Cleanup is executed on-demand or triggered via an external scheduled task / cron job; it does not run as an internal in-process background daemon inside the web server.
- To inspect or trigger the retention cleanup service:
  ```powershell
  # Dry-run inspection (non-destructive)
  python -m src.backend.services.retention --dry-run

  # Execute cleanup
  python -m src.backend.services.retention
  ```

### 4. Multi-Database Architecture & Verification Status
- **SQLite (Development Default — Verified):** The primary local development database (`sqlite:///./smarthire_dev.db`). The automated 92-test backend test suite runs hermetically and passes against in-memory SQLite (`sqlite:///:memory:`).
- **MySQL (Live Verified on MySQL 5.7+):** Fully verified against a live local MySQL instance (`MySQL57` on port 3306) via `PyMySQL` and connection recycling (`pool_recycle=3600`). All Alembic migrations, foreign key cascades, indexes, isolated CRUD operations, and full Playwright browser E2E workflows have been tested and verified passing on the dedicated `smarthire_test` database.
- **PostgreSQL (Alembic Schema Ready — Unverified):** The database schema, SQLAlchemy models, and Alembic migrations are designed for PostgreSQL compatibility, but integration against a live PostgreSQL server remains explicitly UNVERIFIED due to the absence of a running PostgreSQL service on the local host.
