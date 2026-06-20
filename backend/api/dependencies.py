"""
Shared FastAPI dependencies.
Import from here — not from api/routes/auth.py — to avoid circular imports.
"""
import logging
from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User, ScreeningSession
from core.security import decode_access_token, decode_screening_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT and return the authenticated user. Raises 401 if invalid."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = decode_access_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account disabled",
        )
    return user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return authenticated user or None — for endpoints that accept either auth mode."""
    if not token:
        return None
    email = decode_access_token(token)
    if not email:
        return None
    return db.query(User).filter(User.email == email, User.is_active == True).first()


def _validate_screening_token(session: ScreeningSession, token: Optional[str]) -> None:
    """Raise 403 if token doesn't match session."""
    decoded = decode_screening_token(token or "")
    if (
        not decoded
        or decoded.get("session_id") != str(session.id)
        or decoded.get("candidate_id") != str(session.candidate_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid screening token required",
        )


def verify_screening_read_access(
    session_id: UUID,
    x_screening_token: Optional[str] = Header(None, alias="X-Screening-Token"),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ScreeningSession:
    """Allow read via screening token (candidate) or HR JWT (dashboard)."""
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Screening session not found")

    if x_screening_token:
        try:
            _validate_screening_token(session, x_screening_token)
            return session
        except HTTPException:
            pass

    if token:
        email = decode_access_token(token)
        if email:
            user = db.query(User).filter(User.email == email, User.is_active == True).first()
            if user:
                return session

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Valid screening token or HR credentials required",
    )


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Raise 403 unless the user has the 'admin' role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

def require_hr_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Raise 403 if the user is only an interviewer. Allows hr and admin."""
    if current_user.role not in ("admin", "hr"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR or Admin access required",
        )
    return current_user
