from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.models import Candidate, AnalyticsEvent, Job
from core.schemas import AnalyticsEventCreate, FunnelItem, DropOffItem
from api.routes.auth import get_current_user
from core.models import User

router = APIRouter()

PIPELINE_STAGES = ["applied", "screened", "shortlisted", "interviewing", "offered", "rejected"]


# ─── RECORD AN EVENT ──────────────────────────────────────────

@router.post("/event", status_code=201)
def record_event(
    payload: AnalyticsEventCreate,
    db: Session = Depends(get_db),
):
    """
    Record an analytics event (public — called from candidate portal or backend).
    Examples: screening_started, resume_uploaded, session_completed, etc.
    """
    event = AnalyticsEvent(
        event_type=payload.event_type,
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        event_metadata=payload.event_metadata,
    )
    db.add(event)
    db.commit()
    return {"status": "recorded", "event_type": payload.event_type}


# ─── FUNNEL ───────────────────────────────────────────────────

@router.get("/funnel", response_model=List[FunnelItem])
def get_funnel(
    job_id: Optional[UUID] = Query(None, description="Limit funnel to one job"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a count per pipeline stage ordered top-to-bottom.
    Gives the HR team a quick view of conversion through the hiring funnel.
    """
    query = db.query(Candidate.status, func.count(Candidate.id).label("count"))
    if job_id:
        query = query.filter(Candidate.job_id == job_id)

    rows = query.group_by(Candidate.status).all()
    stage_map = {row.status: row.count for row in rows}

    return [
        FunnelItem(stage=stage, count=stage_map.get(stage, 0))
        for stage in PIPELINE_STAGES
    ]


# ─── DROP-OFF ─────────────────────────────────────────────────

@router.get("/drop-off", response_model=List[DropOffItem])
def get_dropoff(
    job_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate the drop-off rate between consecutive pipeline stages.
    e.g. applied→screened: 60% of applicants proceed to screening.
    """
    query = db.query(Candidate.status, func.count(Candidate.id).label("count"))
    if job_id:
        query = query.filter(Candidate.job_id == job_id)

    rows = query.group_by(Candidate.status).all()
    stage_map = {row.status: row.count for row in rows}

    result = []
    for i in range(len(PIPELINE_STAGES) - 1):
        from_stage = PIPELINE_STAGES[i]
        to_stage = PIPELINE_STAGES[i + 1]
        from_count = stage_map.get(from_stage, 0)
        to_count = stage_map.get(to_stage, 0)

        if from_count == 0:
            drop_off_rate = 0.0
        else:
            drop_off_rate = round(1.0 - (to_count / from_count), 4)

        result.append(DropOffItem(
            from_stage=from_stage,
            to_stage=to_stage,
            drop_off_rate=drop_off_rate,
        ))

    return result


# ─── EVENT LOG ────────────────────────────────────────────────

@router.get("/events")
def list_events(
    job_id: Optional[UUID] = Query(None),
    candidate_id: Optional[UUID] = Query(None),
    event_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List raw analytics events with optional filters."""
    query = db.query(AnalyticsEvent)
    if job_id:
        query = query.filter(AnalyticsEvent.job_id == job_id)
    if candidate_id:
        query = query.filter(AnalyticsEvent.candidate_id == candidate_id)
    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)

    events = query.order_by(AnalyticsEvent.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "candidate_id": str(e.candidate_id) if e.candidate_id else None,
            "job_id": str(e.job_id) if e.job_id else None,
            "event_metadata": e.event_metadata,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]