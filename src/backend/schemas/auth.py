"""
Authentication & User Schemas for SmartHire 2.0.
Uses regex validation for email to eliminate extra package dependencies.
"""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class UserRegister(BaseModel):
    email: str = Field(..., description="Valid user email address")
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="candidate", description="Allowed roles: 'candidate', 'recruiter'")

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean

    @field_validator("role")
    def validate_role(cls, v: str) -> str:
        role_lower = v.strip().lower()
        if role_lower not in ["candidate", "recruiter"]:
            raise ValueError("Role must be 'candidate' or 'recruiter'.")
        return role_lower


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


from pydantic import BaseModel, Field, field_validator, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
