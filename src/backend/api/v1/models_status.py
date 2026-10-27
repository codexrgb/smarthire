"""
Model status & Provenance inspection route for SmartHire 2.0 API.
"""

from fastapi import APIRouter
from src.config import MODELS_DIR, RAW_DATA_DIR, METRICS_DIR
from src.backend.schemas.common import ModelStatusResponse
from src.data.provenance import assess_repository_datasets

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/status", response_model=ModelStatusResponse)
def get_models_status():
    """Returns load status of trained models, feature parameters, and dataset provenance."""
    expected_models = [
        "classifier.pkl",
        "tfidf_vectorizer.pkl",
        "job_vectorizer.pkl",
        "job_vectors.pkl",
        "kmeans_clustering.pkl",
        "pca_2d.pkl"
    ]
    models_loaded = {fname: (MODELS_DIR / fname).exists() for fname in expected_models}

    # Provenance assessment
    prov = assess_repository_datasets(RAW_DATA_DIR)

    return ModelStatusResponse(
        models_loaded=models_loaded,
        best_classifier="LogisticRegression",
        dataset_provenance={
            "overall_status": prov["overall_status"],
            "is_demo_mode": prov["is_demo_mode"],
            "ui_badge": prov["ui_badge"],
            "banner_message": prov["banner_message"],
            "files": prov["file_assessments"]
        },
        demo_warning_active=prov["is_demo_mode"]
    )
