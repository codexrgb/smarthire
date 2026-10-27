"""Schemas package."""
from src.backend.schemas.auth import UserRegister, UserLogin, UserOut, TokenResponse
from src.backend.schemas.resume import ResumeParseResponse
from src.backend.schemas.match import MatchScoreRequest, MatchScoreResponse
from src.backend.schemas.job import JobRecommendRequest, JobRecommendItem, JobRecommendResponse
from src.backend.schemas.common import HealthResponse, ModelStatusResponse

__all__ = [
    "UserRegister",
    "UserLogin",
    "UserOut",
    "TokenResponse",
    "ResumeParseResponse",
    "MatchScoreRequest",
    "MatchScoreResponse",
    "JobRecommendRequest",
    "JobRecommendItem",
    "JobRecommendResponse",
    "HealthResponse",
    "ModelStatusResponse"
]
