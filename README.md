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

## 🛡️ Academic Integrity: Real Data Mode vs. Demo Mode

- **Real Data Mode:** When the required real datasets exist in `data/raw/`, SmartHire trains models on actual data and reports genuine evaluation metrics saved in `reports/metrics/`.
- **Demo Mode:** If raw datasets are missing, SmartHire prints `"Required datasets are missing from data/raw/. Add the datasets and run training again."`, activates development fallback demo data, and displays a prominent warning banner across the web app:
  `"DEMO MODE: Synthetic data is being used. These metrics must not be used as final project results."`

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

### 4. Run Unit Tests
```bash
pytest -q
```

---

## 📈 Metric Reporting & Saved Artifacts

- **`models/`**: `classifier.pkl`, `tfidf_vectorizer.pkl`, `job_vectorizer.pkl`, `job_vectors.pkl`, `kmeans_clustering.pkl`
- **`reports/metrics/`**: `classifier_metrics.json`, `clustering_metrics.json`, `pipeline_status.json`
- **`reports/figures/`**: `confusion_matrix.png`, `elbow_curve.png`, `silhouette_scores.png`, `job_clusters_pca.png`

---

## ⚠️ Limitations & Future Work

1. **Skill Extraction Dictionary Dependence:** Skill extraction depends on the extendable technical skill dictionary and alias mapping (`SKILL_ALIAS_MAP`).
2. **Lack of Ground-Truth Hiring Data:** Public job datasets do not provide historical candidate-job hiring ground truth labels.
3. **Transparent Fit Score Labeling:** Fit scores therefore represent transparent matching scores based on text, skill, and experience features, not actual hiring probabilities.
4. **Dataset Coverage:** Recommendation quality depends on the quality, coverage, and detail of the supplied local job datasets.
