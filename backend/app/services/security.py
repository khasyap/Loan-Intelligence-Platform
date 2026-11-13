"""
Security & Authentication Service: Implements Role-Based Access Control (RBAC),
PBKDF2-HMAC-SHA256 password hashing, token validation, and customer data boundary enforcement.
"""

import hashlib
import os
import secrets
import json
import base64
import datetime
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("SECRET_KEY", "LOAN_INTELLIGENCE_PLATFORM_SUPER_SECRET_KEY_2026")

# 4 Primary System Actors
ROLES = ["CUSTOMER", "OPERATIONS_ANALYST", "RISK_REVIEWER", "ADMIN"]

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """PBKDF2-HMAC-SHA256 password hasher with salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verifies a password against the stored salt$hash."""
    try:
        salt, hashed = stored_password.split("$")
        key = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return secrets.compare_digest(key.hex(), hashed)
    except Exception:
        return False


# Curated Demo Accounts for Demonstration
DEMO_USERS = {
    "admin@bank.org": {
        "email": "admin@bank.org",
        "name": "System Administrator",
        "role": "ADMIN",
        "password_hash": hash_password("AdminDemo@2026", "fixed_salt_admin_2026"),
        "applicant_id": None
    },
    "reviewer@bank.org": {
        "email": "reviewer@bank.org",
        "name": "Senior Underwriting Officer",
        "role": "RISK_REVIEWER",
        "password_hash": hash_password("ReviewerDemo@2026", "fixed_salt_reviewer_2026"),
        "applicant_id": None
    },
    "ops@bank.org": {
        "email": "ops@bank.org",
        "name": "Operations Analyst",
        "role": "OPERATIONS_ANALYST",
        "password_hash": hash_password("OpsDemo@2026", "fixed_salt_ops_2026"),
        "applicant_id": None
    },
    "customer@bank.org": {
        "email": "customer@bank.org",
        "name": "Demo Applicant",
        "role": "CUSTOMER",
        "password_hash": hash_password("CustomerDemo@2026", "fixed_salt_cust_2026"),
        "applicant_id": "APP-2026-000001"
    }
}


def create_access_token(user: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Creates a signed bearer token payload."""
    expire = datetime.datetime.now(datetime.timezone.utc) + (expires_delta or datetime.timedelta(hours=24))
    payload = {
        "sub": user["email"],
        "name": user["name"],
        "role": user["role"],
        "applicant_id": user.get("applicant_id"),
        "exp": expire.isoformat()
    }
    payload_json = json.dumps(payload)
    encoded = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")
    sig = hashlib.sha256((encoded + SECRET_KEY).encode("utf-8")).hexdigest()
    return f"{encoded}.{sig}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Validates and decodes signed bearer token."""
    try:
        encoded, sig = token.split(".")
        expected_sig = hashlib.sha256((encoded + SECRET_KEY).encode("utf-8")).hexdigest()
        if not secrets.compare_digest(sig, expected_sig):
            raise ValueError("Invalid signature")
        payload_json = base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)) -> Dict[str, Any]:
    """Extracts authenticated user from Bearer token. Falls back to default admin in demo sandbox if no header."""
    if not credentials:
        # Default unauthenticated fallback in demo mode: Return System Administrator
        return DEMO_USERS["admin@bank.org"]
    token = credentials.credentials
    return decode_access_token(token)


def require_role(allowed_roles: List[str]):
    """Role-based access guard dependency."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles {allowed_roles}, your role is '{user.get('role')}'"
            )
        return user
    return role_checker

