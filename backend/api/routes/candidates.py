from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.models import Candidate, Job, CompetencyScore
from core.schemas import (
    CandidateCreate, CandidateResponse, CandidateStatusUpdate,
    CompetencyScoreResponse, CandidateWithScore,
)
from api.routes.auth import get_current_user
from core.models import User

router = APIRouter()

VALID_STATUSES = {"applied", "screened", "shortlisted", "interviewing", "offered", "rejected"}


# ─── LIST CANDIDATES ──────────────────────────────────────────

@router.get("/", response_model=List[CandidateResponse])
def list_candidates(
    job_id: Optional[UUID] = Query(None, description="Filter by job"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by pipeline status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List candidates, optionally filtered by job or pipeline status."""
    query = db.query(Candidate)
    if job_id:
        query = query.filter(Candidate.job_id == job_id)
    if status_filter:
        query = query.filter(Candidate.status == status_filter)
    return query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()


# ─── CREATE CANDIDATE ─────────────────────────────────────────

@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new candidate for a job. Called before the screening flow begins."""
    # Validate job exists
    job = db.query(Job).filter(Job.id == payload.job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or inactive")

    # Prevent duplicate email per job
    existing = db.query(Candidate).filter(
        Candidate.email == payload.email,
        Candidate.job_id == payload.job_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Candidate already applied for this job")

    candidate = Candidate(
        name=payload.name,
        email=str(payload.email),
        phone=payload.phone,
        github_url=payload.github_url,
        job_id=payload.job_id,
        status="applied",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


# ─── GET CANDIDATE ────────────────────────────────────────────

@router.get("/{candidate_id}", response_model=CandidateWithScore)
def get_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a candidate with their latest competency score."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    score = (
        db.query(CompetencyScore)
        .filter(CompetencyScore.candidate_id == candidate_id)
        .order_by(CompetencyScore.created_at.desc())
        .first()
    )

    return CandidateWithScore(
        candidate=CandidateResponse.model_validate(candidate),
        score=CompetencyScoreResponse.model_validate(score) if score else None,
    )


# ─── UPDATE STATUS ────────────────────────────────────────────

@router.patch("/{candidate_id}/status", response_model=CandidateResponse)
def update_candidate_status(
    candidate_id: UUID,
    payload: CandidateStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move a candidate to a new pipeline stage."""
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {sorted(VALID_STATUSES)}",
        )

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.status = payload.status
    db.commit()
    db.refresh(candidate)
    return candidate


# ─── PUBLIC ENDPOINT: candidate self-registration ─────────────
# No auth required — candidates call this from the public portal

@router.post("/public/apply", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def public_apply(payload: CandidateCreate, db: Session = Depends(get_db)):
    """Public endpoint: candidate applies directly from the job portal (no HR auth needed)."""
    job = db.query(Job).filter(Job.id == payload.job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or no longer accepting applications")

    existing = db.query(Candidate).filter(
        Candidate.email == payload.email,
        Candidate.job_id == payload.job_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied for this position")

    candidate = Candidate(
        name=payload.name,
        email=str(payload.email),
        phone=payload.phone,
        github_url=payload.github_url,
        job_id=payload.job_id,
        status="applied",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate