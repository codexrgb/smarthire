# SmartHire 2.0 — Dataset Ingestion & Provenance Protocol

## 1. Overview
This protocol defines the strict requirements for importing and registering authentic resume and job posting datasets into SmartHire 2.0.

In compliance with Phase 0 audit findings:
- **Never infer authenticity from file names alone.**
- **Synthetic template data will be detected and labeled as demo mode.**
- **No real-world generalization claim may be published without verified, un-templated data.**
- **Personal identifiers (emails, phone numbers) must be redacted before storage and processing.**

---

## 2. Ingestion Prerequisites

### Legal & Licensing Criteria
1. Datasets must possess an explicit, permissive open license permitting modification and academic/commercial research (e.g., CC0, CC-BY-4.0, CC-BY-SA-4.0, MIT, ODC-By).
2. The acquisition source URL, license type, and acquisition date must be recorded in `data/provenance_manifest.json`.

### Schema Requirements
- **Resumes:** Must contain a text column (e.g., `resume_text` or `Resume_str`) and a ground-truth domain category column (`category` or `Category`).
- **Jobs:** Must contain `title`, `company`, `location`, `description`, and `skills`.

---

## 3. Ingestion Procedure

### Step 1: Place Raw Dataset in Staging
Place your downloaded, unmodified CSV file in `data/raw/` (e.g. `data/raw/authentic_resumes.csv`).
**Do not overwrite existing sample files.**

### Step 2: Run the Ingestion & Validation CLI
Execute the validation framework to verify schema integrity, scan for synthetic artifacts, redact PII, and generate cryptographic checksums:

```bash
python src/data/ingest_dataset.py \
    --input "data/raw/authentic_resumes.csv" \
    --source "https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset" \
    --license "CC-BY-SA-4.0" \
    --text-col "Resume" \
    --label-col "Category"
```

### Step 3: Verification & Output
The ingestion pipeline:
1. Rejects any dataset with detected synthetic template signatures.
2. Checks for empty text fields and duplicates.
3. Redacts candidate phone numbers and email addresses.
4. Writes cleaned, verified data to `data/verified_processed/`.
5. Computes the SHA-256 hash of the raw input file and writes a verified record to `data/provenance_manifest.json`.
6. Leaves the raw input file strictly untouched and immutable.

---

## 4. Operational Status & Blockers

To check whether verified authentic data is currently active in the system:
```bash
python src/data/ingest_dataset.py --check-status
```

> **CURRENT STATUS:**  
> **Evaluation on real resumes remains BLOCKED.**  
> The current files in `data/raw/` are synthetic template datasets. All evaluations run on these datasets remain explicitly flagged as `DEMO / SYNTHETIC` in the UI and reports until authentic data is imported using this protocol.
