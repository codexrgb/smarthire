"""
Unit test suite for SmartHire ML pipeline components.
Tests preprocessing, skill extraction, skill gap calculation, recommendations, clustering, and resume parsing.
"""

import pytest
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

from src.data.preprocess import clean_text
from src.features.text_features import (
    extract_skills, normalize_skill, extract_normalized_skills, calculate_skill_match, generate_skill_gap
)
from src.features.match_features import compute_pair_match_features
from src.models.recommender import recommend_jobs, build_job_recommender
from src.models.clustering import find_optimal_k, cluster_jobs, create_cluster_visualization
from src.parsing.resume_parser import extract_resume_text


def test_clean_text_basic():
    text = "Visit https://example.com or contact info@smarthire.org! Call +1-800-555-0199."
    cleaned = clean_text(text)
    assert "https" not in cleaned
    assert "info@smarthire.org" not in cleaned
    assert "800-555-0199" not in cleaned


def test_clean_text_preserve_technical_tokens():
    text = "We require C++, C#, .NET, Node.js, and React.js."
    cleaned = clean_text(text)
    assert "cplusplus" in cleaned
    assert "csharp" in cleaned
    assert "dotnet" in cleaned
    assert "nodejs" in cleaned
    assert "reactjs" in cleaned


def test_normalize_skill():
    assert normalize_skill("js") == "JavaScript"
    assert normalize_skill("ml") == "Machine Learning"
    assert normalize_skill("ai") == "Artificial Intelligence"
    assert normalize_skill("sklearn") == "Scikit-learn"
    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("spring boot") == "Spring Boot"
    assert normalize_skill("springboot") == "Spring Boot"
    assert normalize_skill("SpringBoot") == "Spring Boot"
    assert normalize_skill("Spring") == "Spring"


def test_spring_boot_skill_match_consistency():
    cand_skills = extract_skills("Candidate skills: Git, Java, MySQL")
    req_skills = extract_skills("Required skills: Git, Java, MySQL, Spring Boot")
    gap = calculate_skill_match(cand_skills, req_skills)
    assert gap["matched_skills"] == ["Git", "Java", "MySQL"]
    assert gap["missing_skills"] == ["Spring Boot"]
    assert gap["match_percentage"] == 75.0


def test_extract_skills_word_boundary_ai():
    # Should extract Artificial Intelligence from standalone AI, but NOT from words like mail, claim, tail
    text_false_positives = "I check my mail and claim details again."
    skills_fp = extract_skills(text_false_positives)
    assert "Artificial Intelligence" not in skills_fp

    text_true_positive = "Specialist in Artificial Intelligence and AI research."
    skills_tp = extract_skills(text_true_positive)
    assert "Artificial Intelligence" in skills_tp


def test_calculate_skill_match():
    candidate_skills = ["Python", "SQL", "Pandas"]
    required_skills = ["Python", "SQL", "Pandas", "Tableau", "Power BI"]

    res = calculate_skill_match(candidate_skills, required_skills)
    assert res["matched_skills"] == ["Pandas", "Python", "SQL"]
    assert res["missing_skills"] == ["Power BI", "Tableau"]
    assert res["match_percentage"] == 60.0

    # Empty required skills test
    res_empty = calculate_skill_match(candidate_skills, [])
    assert res_empty["match_percentage"] == 0.0
    assert "unavailable" in res_empty["explanation"].lower()


def test_compute_pair_match_features():
    resume = "Python Developer with 5 years experience in SQL."
    job = "Python Developer role requiring 3 years experience and SQL."
    feats = compute_pair_match_features(resume, job, job_skills_str="Python, SQL", text_sim_score=0.85)

    assert feats["text_similarity"] == 0.85
    assert feats["skill_overlap"] == 1.0
    assert feats["experience_match"] == 1.0
    assert feats["fit_score"] > 80.0
    assert feats["score_label"] == "ML-Based Fit Score"


def test_recommend_jobs():
    jobs = pd.DataFrame([
        {
            "job_id": "JOB_001",
            "title": "Data Scientist",
            "company": "TechCorp",
            "location": "Remote",
            "skills": "Python, SQL, Pandas, Scikit-learn",
            "experience": "3-5 years",
            "salary": "$120k",
            "category": "Data Science",
            "description": "Data Scientist needed with Python and SQL experience.",
            "clean_description": "data scientist needed with python and sql experience"
        }
    ])

    vec, vecs = build_job_recommender(jobs, save_models=False)
    recs = recommend_jobs("Python Data Scientist with SQL skills", jobs, vectorizer=vec, job_vectors=vecs)

    assert len(recs) == 1
    assert recs.iloc[0]["title"] == "Data Scientist"
    assert recs.iloc[0]["ml_fit_score"] > 0.0


def test_clustering_functions():
    X = csr_matrix(np.random.rand(20, 10))
    k_eval = find_optimal_k(X, k_range=range(2, 6), save_plots=False)
    assert len(k_eval["inertias"]) == 4
    assert len(k_eval["silhouette_scores"]) == 4
    assert len(k_eval["k_details"]) == 4
    assert "best_silhouette_k" in k_eval
    assert "selected_elbow_k" in k_eval
    assert "Elbow Method and Silhouette Score" in k_eval["explanation"]

    sils = k_eval["silhouette_scores"]
    ks = k_eval["k_values"]
    expected_best_idx = int(np.argmax(sils))

    assert k_eval["max_silhouette_score"] == round(max(sils), 4)
    assert k_eval["best_silhouette_k"] == ks[expected_best_idx]

    kmeans, labels, inertia, sil = cluster_jobs(X, n_clusters=3)
    assert len(labels) == 20
    assert inertia > 0.0

    coords = create_cluster_visualization(X, labels, save_figure=False)
    assert coords.shape == (20, 2)


def test_clustering_silhouette_max_regression():
    X = csr_matrix(np.random.rand(30, 15))
    k_eval = find_optimal_k(X, k_range=range(2, 7), save_plots=False)

    sils = np.asarray(k_eval["silhouette_scores"], dtype=float)
    k_vals = np.asarray(k_eval["k_values"], dtype=int)

    best_index = int(np.argmax(sils))

    assert k_eval["max_silhouette_score"] == round(float(max(sils)), 4)
    assert k_eval["best_silhouette_k"] == int(k_vals[best_index])


def test_resume_parser():
    txt, msg = extract_resume_text(b"", "resume.txt")
    assert txt == ""
    assert "empty" in msg.lower()

    valid_content = "Jane Doe\nSoftware Engineer\nSkills: Python, Java".encode("utf-8")
    txt, msg = extract_resume_text(valid_content, "resume.txt")
    assert msg == "Success"
    assert "Jane Doe" in txt
