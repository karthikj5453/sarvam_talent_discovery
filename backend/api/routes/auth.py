from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from core.models import User
from core.schemas import UserCreate, UserResponse, Token
from core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_refresh_token

from config import settings

router = APIRouter()

# Setup optional oauth2 scheme for registration access control
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ─── REGISTER ──────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
    token: str | None = Depends(optional_oauth2_scheme),
):
    """
    Create a new user account.
    
    If ALLOW_PUBLIC_REGISTRATION is False (default) and there are existing active users,
    only authenticated Admin users can invoke this endpoint to register/invite others.
    If no active users exist (bootstrapping), public registration is permitted.
    """
    user_count = db.query(User).filter(User.is_active == True).count()
    if user_count > 0 and not settings.ALLOW_PUBLIC_REGISTRATION:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Registration is locked. Admin credentials are required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        from api.dependencies import get_current_user
        current_user = get_current_user(token, db)
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can register new user accounts.",
            )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="admin" if user_count == 0 else (payload.role if payload.role != "admin" else "hr"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── LOGIN ─────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate and return a JWT access token. Refresh token is stored in HTTP-only cookie."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Store refresh token as HTTP-only secure cookie (not accessible via JS)
    response.set_cookie(
        key="hr_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV != "development",   # HTTPS only in production
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth/refresh",   # scoped — only sent to the refresh endpoint
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ─── REFRESH ───────────────────────────────────────────────────

@router.post("/refresh", response_model=Token)
def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    hr_refresh_token: Optional[str] = Cookie(None),
):
    """Issue a new access token using the HTTP-only refresh token cookie."""
    if not hr_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = decode_refresh_token(hr_refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account disabled",
        )

    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    # Rotate: set a new refresh token cookie
    response.set_cookie(
        key="hr_refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth/refresh",
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ─── LOGOUT ────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Clear the HTTP-only refresh token cookie."""
    response.delete_cookie(
        key="hr_refresh_token",
        path="/auth/refresh",
        httponly=True,
        secure=settings.APP_ENV != "development",
        samesite="lax",
    )
    return


# ─── ME ────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(
    # Import here to avoid circular import — use the central dependency
    __import__("api.dependencies", fromlist=["get_current_user"]).get_current_user
)):
    """Return the currently authenticated user's profile."""
    return current_user