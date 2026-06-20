from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.models import Candidate, Job, CompetencyScore, ActivityLog
from core.schemas import (
    CandidateResponse, CandidateStatusUpdate, CandidateWithScore,
    CompetencyScoreResponse, DashboardPipelineResponse, PipelineStageSummary,
    PaginatedCandidatesWithScores,
)
from api.dependencies import get_current_user, require_hr_or_admin
from services import email_service
from core.models import User

router = APIRouter()

PIPELINE_STAGES = ["applied", "screened", "shortlisted", "interviewing", "offered", "rejected"]


# ─── PIPELINE OVERVIEW ────────────────────────────────────────

@router.get("/pipeline", response_model=DashboardPipelineResponse)
def get_pipeline(
    job_id: Optional[UUID] = Query(None, description="Filter by job"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a breakdown of candidate counts per pipeline stage.
    Used by the HR dashboard Kanban / funnel view.
    """
    query = db.query(Candidate.status, func.count(Candidate.id).label("count"))
    if job_id:
        query = query.filter(Candidate.job_id == job_id)

    rows = query.group_by(Candidate.status).all()
    stage_map = {row.status: row.count for row in rows}

    total = sum(stage_map.values())
    stages = [
        PipelineStageSummary(status=s, count=stage_map.get(s, 0))
        for s in PIPELINE_STAGES
    ]
    return DashboardPipelineResponse(total_candidates=total, stages=stages)


# ─── CANDIDATE LIST WITH SCORES ───────────────────────────────

@router.get("/candidates", response_model=PaginatedCandidatesWithScores)
def get_candidates(
    job_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return candidates enriched with their latest competency score (paginated).
    """
    q = db.query(Candidate)
    if job_id:
        q = q.filter(Candidate.job_id == job_id)
    if status_filter:
        q = q.filter(Candidate.status == status_filter)
    if search:
        term = f"%{search.strip()}%"
        q = q.filter((Candidate.name.ilike(term)) | (Candidate.email.ilike(term)))

    total = q.count()
    candidates = q.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()

    # ── Bulk-fetch scores in ONE query (eliminates N+1) ───────
    candidate_ids = [c.id for c in candidates]
    if candidate_ids:
        # Subquery: latest score per candidate using a window function approach
        # Simpler: fetch all scores for these IDs, keep only the latest per candidate
        all_scores = (
            db.query(CompetencyScore)
            .filter(CompetencyScore.candidate_id.in_(candidate_ids))
            .order_by(CompetencyScore.candidate_id, CompetencyScore.created_at.desc())
            .all()
        )
        # Keep first (latest) score per candidate
        scores_map: dict = {}
        for s in all_scores:
            if s.candidate_id not in scores_map:
                scores_map[s.candidate_id] = s
    else:
        scores_map = {}

    items = [
        CandidateWithScore(
            candidate=CandidateResponse.model_validate(c),
            score=CompetencyScoreResponse.model_validate(scores_map[c.id]) if c.id in scores_map else None,
        )
        for c in candidates
    ]
    return PaginatedCandidatesWithScores(total=total, items=items)


# ─── UPDATE STATUS (DRAG & DROP in Kanban) ────────────────────

@router.patch("/candidates/{candidate_id}/status", response_model=CandidateResponse)
def update_status(
    candidate_id: UUID,
    payload: CandidateStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    """Move a candidate to a new pipeline stage from the dashboard."""
    if payload.status not in PIPELINE_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {PIPELINE_STAGES}",
        )

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    old_status = candidate.status
    candidate.status = payload.status
    db.add(ActivityLog(
        candidate_id=candidate.id,
        actor_id=current_user.id,
        action="status_changed",
        details={"from": old_status, "to": payload.status},
    ))
    db.commit()
    db.refresh(candidate)

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
        except Exception:
            pass

    return candidate


# ─── TOP CANDIDATES FOR A JOB ─────────────────────────────────

@router.get("/jobs/{job_id}/top-candidates", response_model=List[CandidateWithScore])
def get_top_candidates(
    job_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return top-N candidates for a job ranked by total competency score."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    scores = (
        db.query(CompetencyScore)
        .join(Candidate, CompetencyScore.candidate_id == Candidate.id)
        .filter(Candidate.job_id == job_id)
        .order_by(CompetencyScore.total_score.desc())
        .limit(limit)
        .all()
    )

    # ── Bulk-fetch candidates for these scores (eliminates N+1) ─
    candidate_ids = [s.candidate_id for s in scores]
    candidates_map = {
        c.id: c for c in
        db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    } if candidate_ids else {}

    return [
        CandidateWithScore(
            candidate=CandidateResponse.model_validate(candidates_map[s.candidate_id]),
            score=CompetencyScoreResponse.model_validate(s),
        )
        for s in scores
        if s.candidate_id in candidates_map
    ]