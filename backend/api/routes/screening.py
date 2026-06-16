from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from core.database import get_db
from core.models import Candidate, ScreeningSession, CompetencyScore
from core.schemas import (
    ScreeningStartRequest,
    ScreeningSessionResponse,
    ScreeningUploadIntroRequest,
    ScreeningUploadAnswerRequest,
)

router = APIRouter()


# ─── START SCREENING ──────────────────────────────────────────

@router.post("/start", response_model=ScreeningSessionResponse, status_code=status.HTTP_201_CREATED)
def start_screening(payload: ScreeningStartRequest, db: Session = Depends(get_db)):
    """
    Create a new ScreeningSession for a candidate.
    Called by the candidate portal at the beginning of the audio flow.
    No auth — this is a public/candidate-facing endpoint.
    """
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Check if an incomplete session already exists
    existing = (
        db.query(ScreeningSession)
        .filter(
            ScreeningSession.candidate_id == payload.candidate_id,
            ScreeningSession.completed_at == None,
        )
        .first()
    )
    if existing:
        return existing  # Resume the existing session

    session = ScreeningSession(candidate_id=payload.candidate_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ─── GET SESSION ──────────────────────────────────────────────

@router.get("/{session_id}", response_model=ScreeningSessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    """Fetch a screening session by ID."""
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Screening session not found")
    return session


# ─── UPLOAD RESUME ────────────────────────────────────────────

@router.post("/upload-resume")
async def upload_resume(
    candidate_id: UUID = Form(...),
    resume_url: str = Form(..., description="S3 URL of the uploaded resume (client uploads directly to S3)"),
    db: Session = Depends(get_db),
):
    """
    Record the resume URL on the candidate.
    In Phase 2, this will also trigger async resume parsing via Sarvam.
    For now: client uploads to S3 and sends us the URL.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.resume_url = resume_url
    db.commit()
    return {"status": "ok", "resume_url": resume_url}


# ─── UPLOAD INTRO AUDIO ───────────────────────────────────────

@router.post("/upload-intro", response_model=ScreeningSessionResponse)
def upload_intro(payload: ScreeningUploadIntroRequest, db: Session = Depends(get_db)):
    """
    Save the intro transcript + detected language on the session.
    In Phase 2 this will call Sarvam STT. For now, the client sends the transcript.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.intro_transcript = payload.transcript
    session.intro_language = payload.detected_language

    # Update candidate's detected language
    if payload.detected_language:
        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
        if candidate:
            candidate.detected_language = payload.detected_language

    db.commit()
    db.refresh(session)
    return session


# ─── UPLOAD ANSWER AUDIO ──────────────────────────────────────

@router.post("/upload-answer", response_model=ScreeningSessionResponse)
def upload_answer(payload: ScreeningUploadAnswerRequest, db: Session = Depends(get_db)):
    """
    Append an answer transcript to the session's followup_answers list.
    question_index is 0-based and must match an existing followup_questions entry.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    answers: list = list(session.followup_answers or [])

    # Extend list to accommodate the index if needed
    while len(answers) <= payload.question_index:
        answers.append({})

    answers[payload.question_index] = {
        "transcript": payload.transcript,
        "answer_audio_url": None,   # set in Phase 2 after S3 upload
    }

    session.followup_answers = answers
    db.commit()
    db.refresh(session)
    return session


# ─── COMPLETE SCREENING ───────────────────────────────────────

@router.post("/complete", response_model=ScreeningSessionResponse)
def complete_screening(session_id: UUID, db: Session = Depends(get_db)):
    """
    Mark the session as complete and update candidate status to 'screened'.
    In Phase 2, this will trigger the async AI evaluation pipeline.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.completed_at:
        raise HTTPException(status_code=400, detail="Session is already completed")

    session.completed_at = datetime.now(timezone.utc)

    # Move candidate to 'screened'
    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
    if candidate:
        candidate.status = "screened"

    db.commit()
    db.refresh(session)

    # TODO (Phase 2): fire background task → run_evaluation(session.id, candidate.job_id)

    return session