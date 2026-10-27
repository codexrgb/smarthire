"""
Configuration and Environment Settings for SmartHire 2.0 Backend.
Reads configuration from environment variables or .env files with secure defaults.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Ensure .env is loaded if present
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings:
    PROJECT_NAME: str = "SmartHire API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment mode
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()

    # Security & Tokens
    # Default secret key for development only; production MUST set a unique SECRET_KEY env var
    DEV_DEFAULT_SECRET: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    SECRET_KEY: str = os.getenv("SECRET_KEY", DEV_DEFAULT_SECRET)
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    def validate_production_configuration(self) -> None:
        """Validates that unsafe defaults are never active in production environments."""
        if self.ENVIRONMENT in ("production", "prod"):
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == self.DEV_DEFAULT_SECRET
                or len(self.SECRET_KEY) < 32
            ):
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: SmartHire is running in production mode, "
                    "but SECRET_KEY is unset, matches the insecure development default, or is shorter than 32 characters. "
                    "Production deployments must provide a high-entropy SECRET_KEY via environment variables."
                )
            if not self.ALGORITHM or self.ALGORITHM.lower() == "none":
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: ALGORITHM cannot be empty or 'none' in production."
                )

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{PROJECT_ROOT / 'smarthire_dev.db'}"
    )

    # CORS
    raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8501")
    CORS_ORIGINS: List[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

    # File Storage
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(PROJECT_ROOT / "storage" / "resumes")))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Allowed Upload Content Types
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/octet-stream"
    ]


settings = Settings()
settings.validate_production_configuration()
