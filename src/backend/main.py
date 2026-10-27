"""
FastAPI Main Application Factory for SmartHire 2.0.
Configures CORS, middleware, custom error handling, and v1 routes.
"""

import sys
import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backend.config import settings
from src.backend.database import engine, Base
from src.backend.api.v1.api import api_v1_router
from src.backend.api.v1.health import router as root_health_router

# Configure structured logging (ensuring no resume text or credentials logged)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smarthire.backend")


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize storage and tables on startup."""
    logger.info("Initializing database tables for %s...", settings.DATABASE_URL.split("@")[-1])
    Base.metadata.create_all(bind=engine)
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("SmartHire 2.0 Backend initialized successfully.")
    yield


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="SmartHire 2.0 Backend REST API — Classical NLP & Machine Learning Portal",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"]
    )

    # Global Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "details": exc.errors()
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception on %s: %s", request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected server error occurred. Details have been logged securely."
            }
        )

    # Root Level Health Check (GET /health)
    app.include_router(root_health_router)

    # API v1 Router (/api/v1/...)
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.main:app", host="127.0.0.1", port=8000, reload=True)
