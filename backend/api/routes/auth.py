from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import User
from core.schemas import UserCreate, UserResponse, Token
from core.security import hash_password, verify_password, create_access_token

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
        role=payload.role or "hr",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── LOGIN ─────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate and return a JWT access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# ─── ME ────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(
    # Import here to avoid circular import — use the central dependency
    __import__("api.dependencies", fromlist=["get_current_user"]).get_current_user
)):
    """Return the currently authenticated user's profile."""
    return current_user