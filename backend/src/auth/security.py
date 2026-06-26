"""
Security utilities: JWT creation/verification and bcrypt password hashing.

Uses bcrypt directly (not via passlib) to avoid the passlib/bcrypt 4.x+
incompatibility where passlib's detect_wrap_bug() sends a >72-byte password
to bcrypt which now enforces the 72-byte limit and raises ValueError.
"""
import os
import secrets
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
import re
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth.database import get_db

# ─── Config ──────────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_USE_STRONG_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

bearer_scheme = HTTPBearer(auto_error=False)


# ─── Password helpers ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt directly (bypasses passlib)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─── JWT helpers ─────────────────────────────────────────────────────────────

def create_access_token(subject: int | str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}


# ─── FastAPI dependency ───────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Dependency that extracts and validates the Bearer JWT, returning the User."""
    from src.auth.models import User  # local import to avoid circular

    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise exc

    payload = decode_token(credentials.credentials)
    user_id_str: str = payload.get("sub", "")
    if not user_id_str:
        raise exc

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise exc

    return user


# ─── API Key helpers ──────────────────────────────────────────────────────────

def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (raw_key, key_prefix, key_hash)."""
    raw = "ragdoct_" + secrets.token_urlsafe(32)
    prefix = raw[:16]
    key_hash = hash_password(raw)
    return raw, prefix, key_hash


def verify_api_key(raw: str, key_hash: str) -> bool:
    """Verify a raw API key against its stored bcrypt hash."""
    return verify_password(raw, key_hash)

def check_query_validity(query: str) -> bool:
    """
    Validates the incoming medical RAG query to ensure it is safe,
    non-empty, and free from basic injection attempts.
    """
    if not query or not isinstance(query, str):
        print("[SECURITY] Query validation failed: Input is empty or not a string.")
        return False
    
    clean_query = query.strip()
    if len(clean_query) < 3:
        print("[SECURITY] Query validation failed: Input is too short.")
        return False

    # حماية ضد محاولات الـ Cypher Injection لقاعدة بيانات Neo4j
    forbidden_patterns = [
        r"MATCH\s*\(", 
        r"DROP\s*CONSTRAINT", 
        r"DELETE\s*n", 
        r"REMOVE\s*n"
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, clean_query, re.IGNORECASE):
            print(f"[SECURITY] Query validation failed: Forbidden pattern detected.")
            return False

    return True