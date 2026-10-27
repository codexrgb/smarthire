# Baseline Classifier Evaluation & Leakage Isolation Report

**Dataset:** `C:\Users\ps331\OneDrive\Desktop\smarthire\data\processed\resumes.csv`  
**Provenance Status:** `demo_synthetic` (Demo: `True`)  
**Split:** 80% Train (768), 20% Test (192), Stratified (`random_state=42`)  

> **ACADEMIC & ENGINEERING DISCLAIMER:**  
> The current dataset is synthetic template data. Evaluations on this dataset measure memorization of synthetic patterns and **CANNOT establish real-world generalization**. Legitimate benchmark reporting remains blocked until an authentic, un-templated resume dataset is imported.

## Benchmark Comparison

| Condition | Model | Accuracy | Macro F1 | Weighted F1 | Macro Precision | Macro Recall |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Full Synthetic Text | LogisticRegression | 100.00% | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Full Synthetic Text | LinearSVC | 100.00% | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Prefix Stripped (No Label Word) | LogisticRegression | 100.00% | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Prefix Stripped (No Label Word) | LinearSVC | 100.00% | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Findings

1. **Condition 1 (Full Synthetic Text):** Both LogisticRegression and LinearSVC achieve 100% test accuracy because the category name is embedded at the start of every resume string.
2. **Condition 2 (Prefix Stripped):** Removing the prefix reveals whether the models still separate categories solely based on the synthetic category skills mapping. Because the synthetic generator sampled skills from disjoint sets per category, accuracy remains high on this synthetic distribution, but still reflects synthetic data artifacts.
3. **Production Model Integrity:** Existing production models in `models/` were preserved intact without retraining.
