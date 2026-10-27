# SmartHire 2.0 — Visual Regression & Application Screenshot Gallery

This directory contains authentic screenshots of the running **SmartHire 2.0** application captured automatically during the Playwright browser end-to-end (E2E) testing suite (`frontend/e2e/smarthire_flows.spec.ts`).

> [!NOTE]
> All screenshots are genuine visual captures of the running React/Vite frontend and FastAPI/MySQL backend. No fabricated mockups or post-processed graphics are used. All test accounts, resumes, emails, and phone numbers are strictly synthetic demo data. Zero personal information, secrets, access tokens, or credentials are stored or displayed.

---

## 📸 Screenshot Catalog

| Filename | Description | Demonstrated Feature | Theme |
|---|---|---|---|
| [`01_auth_register_candidate.png`](./01_auth_register_candidate.png) | Registration Screen | User onboarding form with role selection (Candidate / Recruiter) | Light |
| [`02_candidate_dashboard.png`](./02_candidate_dashboard.png) | Candidate Dashboard (First Login) | First-time welcome greeting (`Welcome, Alice!`) and introductory onboarding guide | Light |
| [`02b_candidate_dashboard_dark.png`](./02b_candidate_dashboard_dark.png) | Candidate Dashboard (Dark Mode) | Dark theme with high-contrast text, slate styling, and stat widgets | Dark |
| [`02c_candidate_dashboard_returning.png`](./02c_candidate_dashboard_returning.png) | Candidate Dashboard (Returning) | Returning user welcome greeting (`Welcome back, Alice!`) and analytical subtext | Light |
| [`03_resume_analyzer_parsed.png`](./03_resume_analyzer_parsed.png) | Resume Parser & NLP Classifier | SHA-256 fingerprint, domain prediction, confidence score, extracted skills, and recommendations | Light |
| [`04_job_match_details.png`](./04_job_match_details.png) | 3-Factor Job Match Breakdown | Explainable score (Text 50%, Skills 30%, Exp 20%), matched/missing chips, and non-probabilistic guardrail | Light |
| [`04b_skill_gap_analysis.png`](./04b_skill_gap_analysis.png) | Technical Skill Gap Analysis | Overlap percentage, matched competencies (green), missing requirements (rose), and learning resources | Light |
| [`05_candidate_profile_edited.png`](./05_candidate_profile_edited.png) | Candidate Profile Management | Self-service profile editing under Settings with confirmation alert | Light |
| [`06_candidate_resume_deleted.png`](./06_candidate_resume_deleted.png) | Resume Portfolio Deletion | Safe single-resume deletion workflow with native confirmation dialog | Light |
| [`07_authorization_failure_blocked.png`](./07_authorization_failure_blocked.png) | RBAC Security Enforcement | 403 Forbidden intercept when Candidate attempts to view recruiter routes | Light |
| [`08_recruiter_dashboard.png`](./08_recruiter_dashboard.png) | Recruiter Command Center | Pipeline statistics, candidate metrics, audit logs, and navigation shortcuts | Light |
| [`09_recruiter_candidate_inspected.png`](./09_recruiter_candidate_inspected.png) | Candidate Profile Inspection Modal | PII-sanitized resume preview (`[EMAIL MASKED]`, `[PHONE MASKED]`) and extracted skill chips | Light |
| [`10_recruiter_candidate_shortlisted.png`](./10_recruiter_candidate_shortlisted.png) | Recruiter Candidate Shortlisting | Candidate table with one-click Shortlist action and immediate audit logging | Light |

---

## 🛠️ Automated Capture Instructions

To reproduce these captures locally using real-browser headless Chromium:

### 1. Ensure Local Services Are Running
```powershell
# Terminal 1: Backend API (port 8000)
python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend SPA (port 5173)
npm --prefix frontend run dev
```

### 2. Execute Playwright E2E Suite
```powershell
# In project root or frontend directory:
npm --prefix frontend run test:e2e
```

The test runner will execute all 3 E2E test suites (15 candidate/recruiter steps), verify all assertions, and overwrite the image files in this directory with current visual output.

---

## 🔒 Privacy & Data Provenance Notice
- Resumes evaluated during automated capture are loaded from [`frontend/e2e/fixtures/synthetic_resume.txt`](../../frontend/e2e/fixtures/synthetic_resume.txt) and contain fabricated professional summaries.
- User accounts (`Alice Candidate E2E`, `Bob Recruiter E2E`) are ephemeral test records created with pseudo-random timestamps and cleaned or isolated after test execution.
- No real resumes, PII, API keys, or production tokens are contained in any screenshot file.
