from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
import logging

from core.database import get_db
from core.models import Candidate, ScreeningSession, CompetencyScore
from core.schemas import (
    ScreeningStartRequest,
    ScreeningSessionResponse,
    ScreeningUploadIntroRequest,
    ScreeningUploadAnswerRequest,
)
from services.sarvam.sarvam_client import transcribe_and_translate, SarvamError
from services.storage.s3_client import upload_audio, upload_resume as s3_upload_resume, key_to_url

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── START SCREENING ──────────────────────────────────────────

@router.post("/start", response_model=ScreeningSessionResponse, status_code=status.HTTP_201_CREATED)
def start_screening(payload: ScreeningStartRequest, db: Session = Depends(get_db)):
    """
    Create a new ScreeningSession for a candidate.
    If an incomplete session already exists, resume it.
    """
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    existing = (
        db.query(ScreeningSession)
        .filter(
            ScreeningSession.candidate_id == payload.candidate_id,
            ScreeningSession.completed_at == None,
        )
        .first()
    )
    if existing:
        return existing

    session = ScreeningSession(candidate_id=payload.candidate_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ─── GET SESSION ──────────────────────────────────────────────

@router.get("/{session_id}", response_model=ScreeningSessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Screening session not found")
    return session


# ─── UPLOAD RESUME ────────────────────────────────────────────

@router.post("/upload-resume")
async def upload_resume(
    candidate_id: UUID = Form(...),
    file: Optional[UploadFile] = File(None),
    resume_url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a resume. Accepts either:
      - A direct file upload (PDF) → uploads to S3 automatically
      - A pre-uploaded S3 URL string (if client uploaded directly to S3)
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    final_url = resume_url

    if file and not resume_url:
        try:
            file_bytes = await file.read()
            s3_key = s3_upload_resume(file_bytes, str(candidate_id))
            final_url = key_to_url(s3_key)
        except Exception as e:
            logger.warning(f"[Screening] S3 upload failed: {e} — skipping resume URL")
            final_url = None

    if final_url:
        candidate.resume_url = final_url
        db.commit()

    return {"status": "ok", "resume_url": final_url}


# ─── UPLOAD INTRO AUDIO ───────────────────────────────────────

@router.post("/upload-intro", response_model=ScreeningSessionResponse)
async def upload_intro(
    session_id: UUID = Form(...),
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    detected_language: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Process the candidate's intro audio.

    Two modes:
    1. Send raw audio file → Sarvam STT runs automatically
    2. Send pre-computed transcript text → stored directly

    Sarvam STT-Translate auto-detects language and returns
    both the original transcript and an English translation.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    final_transcript = transcript
    final_language = detected_language
    intro_audio_url = None

    # ── Case 1: Raw audio → call Sarvam STT ──────────────────
    if file and not transcript:
        audio_bytes = await file.read()

        # Upload to S3 for record-keeping
        try:
            s3_key = upload_audio(audio_bytes, str(session.candidate_id), label="intro")
            intro_audio_url = key_to_url(s3_key)
            session.intro_audio_url = intro_audio_url
        except Exception as e:
            logger.warning(f"[Screening] S3 audio upload failed: {e}")

        # Call Sarvam STT + Translate
        try:
            result = await transcribe_and_translate(
                audio_bytes=audio_bytes,
                filename=file.filename or "intro.wav",
            )
            final_transcript = result.get("transcript", "")
            final_language = result.get("language_code", "unknown")
            logger.info(f"[Screening] STT result: lang={final_language}, chars={len(final_transcript)}")
        except SarvamError as e:
            logger.error(f"[Screening] Sarvam STT failed: {e}")
            raise HTTPException(status_code=502, detail=f"Sarvam STT failed: {e.detail}")

    # ── Save results ──────────────────────────────────────────
    session.intro_transcript = final_transcript
    session.intro_language = final_language

    if final_language:
        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
        if candidate:
            candidate.detected_language = final_language

    db.commit()
    db.refresh(session)
    return session


# ─── UPLOAD ANSWER AUDIO ──────────────────────────────────────

@router.post("/upload-answer", response_model=ScreeningSessionResponse)
async def upload_answer(
    session_id: UUID = Form(...),
    question_index: int = Form(...),
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Process one follow-up answer audio.
    question_index is 0-based, matching the followup_questions array.
    Like upload-intro: accepts raw audio (→ Sarvam STT) or pre-computed transcript.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    final_transcript = transcript
    answer_audio_url = None

    # ── Case 1: Raw audio → Sarvam STT ───────────────────────
    if file and not transcript:
        audio_bytes = await file.read()

        try:
            s3_key = upload_audio(audio_bytes, str(session.candidate_id), label=f"answer_{question_index}")
            answer_audio_url = key_to_url(s3_key)
        except Exception as e:
            logger.warning(f"[Screening] S3 answer upload failed: {e}")

        try:
            result = await transcribe_and_translate(
                audio_bytes=audio_bytes,
                filename=file.filename or "answer.wav",
            )
            final_transcript = result.get("transcript", "")
        except SarvamError as e:
            logger.error(f"[Screening] Sarvam STT (answer) failed: {e}")
            raise HTTPException(status_code=502, detail=f"Sarvam STT failed: {e.detail}")

    # ── Update answers list ───────────────────────────────────
    answers: list = list(session.followup_answers or [])
    while len(answers) <= question_index:
        answers.append({})

    answers[question_index] = {
        "transcript": final_transcript,
        "answer_audio_url": answer_audio_url,
    }

    session.followup_answers = answers
    db.commit()
    db.refresh(session)
    return session


# ─── COMPLETE SCREENING ───────────────────────────────────────

@router.post("/complete", response_model=ScreeningSessionResponse)
def complete_screening(session_id: UUID, db: Session = Depends(get_db)):
    """
    Mark the session complete → update candidate status → fire AI evaluation.
    The evaluation runs async via Celery so this endpoint returns immediately.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.completed_at:
        raise HTTPException(status_code=400, detail="Session already completed")

    session.completed_at = datetime.now(timezone.utc)

    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
    if candidate:
        candidate.status = "screened"

    db.commit()
    db.refresh(session)

    # ── Fire background evaluation task ──────────────────────
    try:
        from services.background.tasks import evaluate_candidate_task
        evaluate_candidate_task.delay(str(session_id))
        logger.info(f"[Screening] Evaluation task queued for session {session_id}")
    except Exception as e:
        # Celery/Redis might not be running in dev — log but don't fail the request
        logger.warning(f"[Screening] Could not queue evaluation task: {e}")

    return session