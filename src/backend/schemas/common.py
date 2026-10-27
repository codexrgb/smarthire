"""
Common & System Schemas for SmartHire 2.0.
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    database_connected: bool


class ModelStatusResponse(BaseModel):
    models_loaded: Dict[str, bool]
    best_classifier: str
    dataset_provenance: Dict[str, Any]
    demo_warning_active: bool
