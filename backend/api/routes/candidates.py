from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
import logging

from core.database import get_db
from core.models import Candidate, Job, CompetencyScore, ScreeningSession, AnalyticsEvent
from core.schemas import (
    CandidateCreate, CandidateResponse, CandidateStatusUpdate,
    CompetencyScoreResponse, CandidateWithScore,
)
from api.dependencies import get_current_user, require_admin
from core.models import User
from services import email_service
from services.storage.s3_client import delete_file, url_to_key

router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

VALID_STATUSES = {"applied", "screened", "shortlisted", "interviewing", "offered", "rejected"}

# ─── MAX FILE SIZE CONSTANTS ──────────────────────────────────
MAX_AUDIO_BYTES = 25 * 1024 * 1024   # 25 MB
MAX_RESUME_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_RESUME_MIME = {"application/pdf"}


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


# ─── CREATE CANDIDATE (HR) ────────────────────────────────────

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

    # Prevent duplicate (email, job_id) — same person applying twice to same job
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
        github_url=getattr(payload, "github_url", None),
        job_id=payload.job_id,
        status="applied",
        consent_given=payload.consent_given,
    )
    db.add(candidate)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Candidate already applied for this job")
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

    # Send status update email to candidate
    notify_statuses = {"shortlisted", "offered", "rejected", "interviewing"}
    if payload.status in notify_statuses:
        try:
            job = db.query(Job).filter(Job.id == candidate.job_id).first()
            email_service.send_status_update(
                candidate_name=candidate.name,
                candidate_email=candidate.email,
                job_title=job.title if job else "the position",
                new_status=payload.status,
            )
        except Exception as e:
            # Never fail status update because of email — but do log it
            logger.warning("[Email] Status update email failed for candidate %s: %s", candidate_id, e)

    return candidate


# ─── PUBLIC ENDPOINT: candidate self-registration ─────────────
# No auth required — candidates call this from the public portal.
# Rate-limited to prevent bot flooding + API bill abuse.

@router.post("/public/apply", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
@limiter.limit("20/day")
def public_apply(request: Request, payload: CandidateCreate, db: Session = Depends(get_db)):
    """
    Public endpoint: candidate applies directly from the job portal (no HR auth needed).
    Rate-limited: 5 requests/minute per IP, 20 requests/day per IP.
    """
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
        github_url=getattr(payload, "github_url", None),
        job_id=payload.job_id,
        status="applied",
        consent_given=payload.consent_given,
    )
    db.add(candidate)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="You have already applied for this position")
    db.refresh(candidate)
    return candidate


# ─── GDPR: DATA ERASURE ───────────────────────────────────────
# Requires admin role — candidates (or HR on their behalf) can erase PII.
# Under DPDP Act / GDPR: deletes actual files, not just DB references.

@router.delete("/gdpr-erase/{candidate_id}", status_code=status.HTTP_200_OK)
def gdpr_erase_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),   # FIX: was completely unprotected
):
    """
    Anonymize all PII for a candidate. Requires admin role.
    - Deletes actual audio/resume files from S3/disk
    - Replaces name/email/phone with anonymized placeholders
    - Nulls resume_url, resume_text, github_url
    - Removes screening transcripts from all sessions
    Preserves aggregate score data for analytics.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    anon_id = str(candidate_id)[:8]

    # ── Delete actual files before nulling URLs ────────────────
    if candidate.resume_url:
        try:
            key = url_to_key(candidate.resume_url)
            if key:
                delete_file(key)
        except Exception as e:
            logger.warning("[GDPR] Failed to delete resume file for %s: %s", candidate_id, e)

    # Wipe transcripts + audio from all screening sessions
    sessions = db.query(ScreeningSession).filter(
        ScreeningSession.candidate_id == candidate_id
    ).all()
    for sess in sessions:
        for url in [sess.intro_audio_url]:
            if url:
                try:
                    key = url_to_key(url)
                    if key:
                        delete_file(key)
                except Exception as e:
                    logger.warning("[GDPR] Failed to delete audio file for session %s: %s", sess.id, e)

        # Delete per-answer audio files
        for ans in (sess.followup_answers or []):
            if isinstance(ans, dict) and ans.get("answer_audio_url"):
                try:
                    key = url_to_key(ans["answer_audio_url"])
                    if key:
                        delete_file(key)
                except Exception as e:
                    logger.warning("[GDPR] Failed to delete answer audio: %s", e)

        sess.intro_transcript = "[ERASED]"
        sess.intro_audio_url = None
        sess.followup_answers = []
        sess.followup_questions = []

    # ── Anonymize candidate PII ────────────────────────────────
    candidate.name = f"[Deleted User {anon_id}]"
    candidate.email = f"deleted_{anon_id}@erased.invalid"
    candidate.phone = None
    candidate.resume_url = None
    candidate.resume_text = None
    candidate.github_url = None
    candidate.detected_language = None
    candidate.consent_given = False

    db.commit()
    logger.info("[GDPR] Candidate %s erased by admin %s", candidate_id, current_user.email)
    return {"status": "erased", "candidate_id": str(candidate_id)}


# ─── HARD DELETE CANDIDATE ────────────────────────────────────
@router.delete("/{candidate_id}", status_code=status.HTTP_200_OK)
def delete_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hard delete a candidate and all associated records (scores, sessions, events, files).
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 1. Delete actual files from S3/disk
    if candidate.resume_url:
        try:
            key = url_to_key(candidate.resume_url)
            if key:
                delete_file(key)
        except Exception as e:
            logger.warning("[Delete] Failed to delete resume file: %s", e)

    sessions = db.query(ScreeningSession).filter(
        ScreeningSession.candidate_id == candidate_id
    ).all()
    for sess in sessions:
        # Delete audio files
        for url in [sess.intro_audio_url]:
            if url:
                try:
                    key = url_to_key(url)
                    if key:
                        delete_file(key)
                except Exception as e:
                    logger.warning("[Delete] Failed to delete intro audio file: %s", e)

        for ans in (sess.followup_answers or []):
            if isinstance(ans, dict) and ans.get("answer_audio_url"):
                try:
                    key = url_to_key(ans["answer_audio_url"])
                    if key:
                        delete_file(key)
                except Exception as e:
                    logger.warning("[Delete] Failed to delete answer audio: %s", e)

    # 2. Delete database records in dependency order
    try:
        # Delete competency scores
        db.query(CompetencyScore).filter(CompetencyScore.candidate_id == candidate_id).delete()
        # Delete screening sessions
        db.query(ScreeningSession).filter(ScreeningSession.candidate_id == candidate_id).delete()
        # Delete analytics events
        db.query(AnalyticsEvent).filter(AnalyticsEvent.candidate_id == candidate_id).delete()
        # Delete candidate
        db.query(Candidate).filter(Candidate.id == candidate_id).delete()
        
        db.commit()
        logger.info("[Delete] Candidate %s and all associated data deleted by user %s", candidate_id, current_user.email)
    except Exception as e:
        db.rollback()
        logger.error("[Delete] Failed to delete candidate %s from DB: %s", candidate_id, e)
        raise HTTPException(status_code=500, detail="Failed to delete candidate from database")

    return {"status": "deleted", "candidate_id": str(candidate_id)}