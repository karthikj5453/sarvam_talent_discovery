from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.database import get_db
from core.models import Job
from core.schemas import JobCreate, JobUpdate, JobResponse
from api.routes.auth import get_current_user
from core.models import User

router = APIRouter()


# ─── LIST JOBS ────────────────────────────────────────────────

@router.get("/", response_model=List[JobResponse])
def list_jobs(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all jobs. Filter to active-only by default."""
    query = db.query(Job)
    if active_only:
        query = query.filter(Job.is_active == True)
    return query.order_by(Job.created_at.desc()).all()


# ─── CREATE JOB ───────────────────────────────────────────────

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new job posting."""
    job = Job(
        title=payload.title,
        department=payload.department,
        location=payload.location,
        description=payload.description,
        required_skills=payload.required_skills,
        competency_weights=payload.competency_weights,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ─── GET JOB ──────────────────────────────────────────────────

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ─── UPDATE JOB ───────────────────────────────────────────────

@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: UUID,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update a job (title, description, weights, active flag, etc.)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


# ─── DELETE (SOFT) JOB ────────────────────────────────────────

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a job by marking it inactive."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_active = False
    db.commit()


# ─── PUBLIC LIST JOBS ─────────────────────────────────────────
# No auth required — candidates fetch this to see open positions

@router.get("/public", response_model=List[JobResponse])
def list_jobs_public(db: Session = Depends(get_db)):
    """Return all active jobs for the public application form (no HR auth needed)."""
    return db.query(Job).filter(Job.is_active == True).order_by(Job.created_at.desc()).all()