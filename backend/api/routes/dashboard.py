from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.models import Candidate, Job, CompetencyScore
from core.schemas import (
    CandidateResponse, CandidateStatusUpdate, CandidateWithScore,
    CompetencyScoreResponse, DashboardPipelineResponse, PipelineStageSummary,
)
from api.routes.auth import get_current_user
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

@router.get("/candidates", response_model=List[CandidateWithScore])
def get_candidates(
    job_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return candidates enriched with their latest competency score.
    Ordered by total_score descending (scored candidates first).
    """
    q = db.query(Candidate)
    if job_id:
        q = q.filter(Candidate.job_id == job_id)
    if status_filter:
        q = q.filter(Candidate.status == status_filter)

    candidates = q.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for c in candidates:
        score = (
            db.query(CompetencyScore)
            .filter(CompetencyScore.candidate_id == c.id)
            .order_by(CompetencyScore.created_at.desc())
            .first()
        )
        results.append(
            CandidateWithScore(
                candidate=CandidateResponse.model_validate(c),
                score=CompetencyScoreResponse.model_validate(score) if score else None,
            )
        )
    return results


# ─── UPDATE STATUS (DRAG & DROP in Kanban) ────────────────────

@router.patch("/candidates/{candidate_id}/status", response_model=CandidateResponse)
def update_status(
    candidate_id: UUID,
    payload: CandidateStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    candidate.status = payload.status
    db.commit()
    db.refresh(candidate)
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

    return [
        CandidateWithScore(
            candidate=CandidateResponse.model_validate(
                db.query(Candidate).filter(Candidate.id == s.candidate_id).first()
            ),
            score=CompetencyScoreResponse.model_validate(s),
        )
        for s in scores
    ]