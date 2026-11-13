from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any
from backend.app.services.security import (
    DEMO_USERS, verify_password, create_access_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    applicant_id: str | None = None

@router.post("/login", response_model=TokenResponse)
@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest):
    """Authenticate with credentials and obtain signed RBAC bearer token."""
    user = DEMO_USERS.get(payload.email)
    if not user or not verify_password(user["password_hash"], payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        role=user["role"],
        name=user["name"],
        applicant_id=user.get("applicant_id")
    )

class UserProfileResponse(BaseModel):
    email: str
    name: str
    role: str
    applicant_id: str | None = None

@router.get("/me", response_model=UserProfileResponse)
def get_current_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve profile of currently authenticated user session (never exposes credentials)."""
    return UserProfileResponse(
        email=user.get("email") or user.get("sub") or "",
        name=user.get("name") or "",
        role=user.get("role") or "",
        applicant_id=user.get("applicant_id")
    )

