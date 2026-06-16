from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from core.database import get_db
from core.models import Candidate, ScreeningSession, CompetencyScore
from core.schemas import CompetencyScoreResponse
from api.routes.auth import get_current_user
from core.models import User

router = APIRouter()


# ─── GET EVALUATION BY CANDIDATE ──────────────────────────────

@router.get("/{candidate_id}", response_model=CompetencyScoreResponse)
def get_evaluation(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the most recent competency score for a candidate.
    Returns 404 if no evaluation has been run yet (screening not yet completed).
    """
    score = (
        db.query(CompetencyScore)
        .filter(CompetencyScore.candidate_id == candidate_id)
        .order_by(CompetencyScore.created_at.desc())
        .first()
    )
    if not score:
        raise HTTPException(
            status_code=404,
            detail="No evaluation found. Screening may not have been completed yet.",
        )
    return score


# ─── LIST ALL EVALUATIONS FOR A JOB ──────────────────────────

@router.get("/", response_model=list[CompetencyScoreResponse])
def list_evaluations(
    job_id: Optional[UUID] = Query(None, description="Filter evaluations by job"),
    min_score: Optional[float] = Query(None, description="Minimum total_score filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List competency scores, optionally filtered by job or minimum score.
    Useful for ranking candidates across a job opening.
    """
    query = (
        db.query(CompetencyScore)
        .join(Candidate, CompetencyScore.candidate_id == Candidate.id)
    )
    if job_id:
        query = query.filter(Candidate.job_id == job_id)
    if min_score is not None:
        query = query.filter(CompetencyScore.total_score >= min_score)

    return (
        query
        .order_by(CompetencyScore.total_score.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )