"""
Database Connection & Session Management for SmartHire 2.0.
Supports PostgreSQL (production) with SQLite support for local integration tests.
"""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.backend.config import settings

# Engine setup: handles SQLite thread restrictions for test suite compatibility
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """Dependency that yields an active database session and ensures clean closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
