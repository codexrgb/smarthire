# SMART HIRE -->
### Resume-to-Job Matching & Career Guidance Engine

> **IMPORTANT NOTICE:**
> **This project uses classical machine learning techniques including TF-IDF, Logistic Regression/Linear SVM, cosine similarity, K-Means, PCA and NMF. No generative AI or LLM is used.**

---

## 📌 Project Overview
**SmartHire** is an end-to-end production-quality academic Machine Learning portal that automates resume categorization, local job recommendation, skill-gap analysis, and job family clustering. The system runs entirely locally without cloud LLM API dependencies.

---

## 📊 Datasets & Schema Normalization

SmartHire is built to work with real public datasets placed in `data/raw/`:
- **UpdatedResumeDataSet.csv**: Resumes across ~25 job categories.
- **naukri_com-job_sample.csv**: Job listings with titles, skills, descriptions, locations, experience, and salary ranges.
- **linkedin_job_postings.csv**: Detailed job postings.

### Dynamic Schema Auto-Detection
Different Kaggle datasets use varying column headers. SmartHire dynamically detects column aliases:
- **Title Aliases:** `title`, `job_title`, `position`, `role`
- **Description Aliases:** `description`, `job_description`, `details`, `summary`
- **Skills Aliases:** `skills`, `key_skills`, `required_skills`
- **Company Aliases:** `company`, `company_name`, `organization`
- **Location Aliases:** `location`, `job_location`, `city`
- **Resume Text Aliases:** `resume_text`, `Resume_str`, `Text`
- **Category Aliases:** `category`, `job_category`, `label`

Datasets are cleaned (removing duplicates, handling missing values, filtering empty records) and normalized into:
- **`data/processed/resumes.csv`**: `[resume_id, resume_text, category, clean_text, source]`
- **`data/processed/jobs.csv`**: `[job_id, title, company, location, skills, experience, salary, description, clean_description, category, source]`

---

## 🛡️ Academic Integrity: Cryptographic Provenance & Mode Classification

SmartHire 2.0 enforces a strict 3-state dataset provenance architecture:
- **Verified Authentic Mode (🟢):** Activated **only** when raw datasets match an authoritative cryptographic checksum manifest (`data/provenance_manifest.json`) recording source, open license, and verified origin.
- **Unverified Mode (🟡):** Activated when non-synthetic datasets are present in `data/raw/` but lack verified cryptographic provenance manifests.
- **Demo / Synthetic Mode (🔴):** Activated automatically whenever template generation signatures (e.g. `Experienced <Category> professional with X years...`) are detected. Displays a prominent warning banner across the web app:
  `"⚠️ DEMO MODE ACTIVE: Synthetic template data detected. These metrics must not be used as final project results."`

> **Critical Provenance Rule:** Filenames alone are never used to infer data authenticity.

---

## 🏗️ Machine Learning Architecture

1. **Resume Text Cleaning**: Removes noise while preserving technical tokens like `C++`, `C#`, `.NET`, `Node.js`, `React.js`.
2. **Resume Classification**: `TfidfVectorizer(max_features=10000, ngram_range=(1,2))` + **Logistic Regression** vs. **LinearSVC** stratified split benchmarking.
3. **Job Recommender**: `TfidfVectorizer(max_features=15000, ngram_range=(1,2))` + **Cosine Similarity** ($\cos(\theta)$).
4. **Transparent ML-Based Fit Score**:
   $$\text{Fit Score} = (0.50 \times \text{TextSimilarity}) + (0.30 \times \text{SkillOverlap}) + (0.20 \times \text{ExperienceMatch}) \times 100$$
5. **Skill Extractor & Skill-Gap**: Regex word-boundary matching against a master technical skill dictionary preventing false positive extractions (e.g., isolating standalone `AI` from words like `mail` or `claim`).
   $$\text{Skill Match \%} = \frac{|\text{Candidate Skills} \cap \text{Required Job Skills}|}{|\text{Required Job Skills}|} \times 100$$
6. **KMeans Job Clustering**: Unsupervised clustering evaluated across $K=2..10$ using Elbow Method (Inertia) and Silhouette Scores.
7. **PCA 2D Visualization Plot**: Reduces TF-IDF space to 2D using `PCA(n_components=2)` strictly for cluster scatter plot generation (`reports/figures/job_clusters_pca.png`).
8. **NMF Topic Modeling**: Non-Negative Matrix Factorization extracting top 10 keywords per topic.

---

## ⚙️ Setup & Training Instructions

### 1. Virtual Environment & Dependencies
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run Training Pipeline
```bash
python train.py
```

### 3. Run Streamlit Web Application
```bash
python run_app.py
```
*Or:*
```bash
streamlit run app/streamlit_app.py
```

### 4. Run Unit & Integration Test Suite
```bash
pytest -v
```
*Executes all 50 tests covering ML features, data provenance, notebook repairs, security sanitization, and FastAPI REST endpoints/RBAC persistence.*

### 5. Run FastAPI REST Backend (SmartHire 2.0)
```bash
uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Full API Reference: `docs/api_documentation.md`

### 6. Database Migrations (PostgreSQL / Alembic)
```bash
# Upgrade to latest schema
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### 7. Run React + TypeScript + Vite Frontend (SmartHire 2.0)
```bash
cd frontend
npm install
npm run dev
```
- Local Development Server: `http://localhost:5173`
- Run Frontend Vitest Suite: `npm test`
- Build Production Bundle: `npm run build`

### 8. Ingest Authentic Dataset & Check Readiness
```bash
python src/data/ingest_dataset.py --check-status
```
*See `docs/dataset_ingestion.md` for the full authentic dataset importation protocol.*

---

## 📈 Metric Reporting & Saved Artifacts

- **Production Models:** `models/classifier.pkl`, `models/tfidf_vectorizer.pkl`, `models/job_vectorizer.pkl`, `models/job_vectors.pkl`, `models/kmeans_clustering.pkl`, `models/pca_2d.pkl`
- **Primary Reports:** `reports/metrics/classifier_metrics.json`, `reports/metrics/clustering_metrics.json`, `reports/metrics/pipeline_status.json`
- **Phase 1 Experimental Reports:**
  - `reports/experiments/baseline_evaluation.md`: Benchmark comparison and label-leakage isolation.
  - `reports/experiments/clustering_evaluation.md`: K=2..15 evaluations, high-dimensional text distance concentration, centroid terms, and external category validation.
- **Figures:** `reports/figures/confusion_matrix.png`, `reports/figures/elbow_curve.png`, `reports/figures/silhouette_scores.png`, `reports/figures/job_clusters_pca.png`
- **Repaired Notebooks:** `notebooks/repaired/` (JSON syntax repaired copies of `02` through `05`).

---

## ⚠️ Limitations & Academic Disclosures

1. **Synthetic Data Benchmark Isolation:** The current raw dataset in `data/raw/` is synthetic template data with label words in the first sentence. 100% reported accuracy reflects template memorization and cannot establish real-world generalization until an authentic, un-templated dataset is ingested.
2. **Heuristic Fit Score Index:** The fit score is a deterministic weighted linear index ($50\%$ text similarity, $30\%$ skill overlap, $20\%$ experience match), NOT a trained, calibrated statistical hiring probability.
3. **Clustering Silhouette Inflation:** In sparse high-dimensional TF-IDF Euclidean space, silhouette scores artificially rise with higher $K$ ($K=10..15$) due to micro-clustering around nearest neighbors on the unit hypersphere.
4. **Skill Extraction Dictionary Dependence:** Skill extraction depends on the extendable technical skill dictionary and alias mapping (`SKILL_ALIAS_MAP`).
