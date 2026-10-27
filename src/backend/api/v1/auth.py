"""
Authentication Routes (Register, Login, Profile) for SmartHire 2.0 API.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.config import settings
from src.backend.database import get_db
from src.backend.models.user import User
from src.backend.schemas.auth import UserRegister, UserLogin, UserOut, TokenResponse
from src.backend.security.hashing import hash_password, verify_password
from src.backend.security.auth import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    """Registers a new candidate or recruiter account with a securely hashed password."""
    # Check if email is already registered
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )

    hashed_pw = hash_password(payload.password)
    user = User(
        email=payload.email.lower().strip(),
        hashed_password=hashed_pw,
        full_name=payload.full_name.strip(),
        role=payload.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticates user credentials and returns a signed JWT access token."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive."
        )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name
    }
    token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the authenticated user's profile."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
