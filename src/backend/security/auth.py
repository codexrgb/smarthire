"""
JWT Authentication & Role-Based Access Control (RBAC) Module for SmartHire 2.0.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.backend.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token. Raises HTTPException on failure."""
    if not settings.ALGORITHM or settings.ALGORITHM.lower() == "none":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Insecure JWT configuration detected."
        )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except (jwt.InvalidTokenError, jwt.PyJWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Extracts and authenticates current user from Bearer token.
    Works with both OAuth2PasswordBearer and direct Authorization header.
    """
    auth_token = token
    if not auth_token and authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(auth_token)
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    if user_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "id": user_id,
        "email": email,
        "role": role,
        "full_name": payload.get("full_name", "")
    }


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Extracts and authenticates current user if a Bearer token is present.
    Returns None if no token is provided.
    Raises HTTPException (401) if an invalid or expired token is presented.
    """
    auth_token = token
    if not auth_token and authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]

    if not auth_token:
        return None

    payload = decode_access_token(auth_token)
    user_id = payload.get("sub")
    role = payload.get("role")

    if user_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": role,
        "full_name": payload.get("full_name", "")
    }


def verify_resume_access(resume: Any, current_user: Optional[Dict[str, Any]]) -> bool:
    """
    Enforces ownership and role-based access control on candidate resumes.
    - Unowned guest resumes (candidate_id is None) are publicly accessible for demo matching.
    - Candidate-owned resumes (candidate_id is not None) require authentication:
      - Only the owning candidate (user id match) OR a recruiter/admin may access the resume.
      - Other candidates are denied with 403 Forbidden.
      - Unauthenticated requests are denied with 401 Unauthorized.
    """
    if resume.candidate_id is None:
        return True

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this candidate's resume.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Recruiter or administrator access
    if current_user.get("role") in ["recruiter", "admin"]:
        return True

    # Owner access
    if str(current_user.get("id")) == str(resume.candidate_id):
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You do not have permission to access another candidate's resume."
    )


def require_role(allowed_roles: List[str]):
    """Role-based authorization dependency factory."""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Operation requires one of the following roles: {allowed_roles}."
            )
        return current_user
    return role_checker
