"""
V1 API Router Aggregator for SmartHire 2.0.
"""

from fastapi import APIRouter
from src.backend.api.v1.health import router as health_router
from src.backend.api.v1.models_status import router as models_router
from src.backend.api.v1.resumes import router as resumes_router
from src.backend.api.v1.matching import router as matching_router
from src.backend.api.v1.jobs import router as jobs_router
from src.backend.api.v1.auth import router as auth_router
from src.backend.api.v1.recruiter import router as recruiter_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(resumes_router)
api_v1_router.include_router(matching_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(recruiter_router)
