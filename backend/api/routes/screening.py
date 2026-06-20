from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
import logging

from core.database import get_db
from core.models import Candidate, Job, ScreeningSession, CompetencyScore
from core.schemas import (
    ScreeningStartRequest,
    ScreeningSessionResponse,
    ScreeningStartResponse,
)
from core.security import create_screening_token
from api.dependencies import verify_screening_read_access, _validate_screening_token
from api.limiter import limiter
from services.sarvam.sarvam_client import transcribe_and_translate, SarvamError
from services.storage.s3_client import upload_audio, upload_resume as s3_upload_resume, key_to_url
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── FILE SIZE LIMITS ─────────────────────────────────────────
MAX_AUDIO_BYTES = 25 * 1024 * 1024    # 25 MB hard cap for audio
MAX_RESUME_BYTES = 10 * 1024 * 1024   # 10 MB hard cap for PDF
ALLOWED_RESUME_MIME = {"application/pdf"}


def _session_with_token(session: ScreeningSession) -> ScreeningStartResponse:
    token = create_screening_token(str(session.candidate_id), str(session.id))
    return ScreeningStartResponse(
        **ScreeningSessionResponse.model_validate(session).model_dump(),
        screening_token=token,
    )


def _assert_session_open(session: ScreeningSession) -> None:
    if session.completed_at:
        raise HTTPException(status_code=400, detail="Session already completed")


# ─── START SCREENING ──────────────────────────────────────────

@router.post("/start", response_model=ScreeningStartResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def start_screening(
    request: Request,
    payload: ScreeningStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new ScreeningSession for a candidate.
    If an incomplete session already exists, resume it.
    Requires candidate.consent_given == True (DPDP Act compliance).
    """
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # ── DPDP / GDPR: require explicit consent before storing voice data ─
    if not candidate.consent_given:
        raise HTTPException(
            status_code=403,
            detail="Candidate has not given consent for data processing. "
                   "Consent must be recorded before screening can begin.",
        )

    existing = (
        db.query(ScreeningSession)
        .filter(
            ScreeningSession.candidate_id == payload.candidate_id,
            ScreeningSession.completed_at == None,
        )
        .first()
    )
    if existing:
        return _session_with_token(existing)

    session = ScreeningSession(candidate_id=payload.candidate_id)
    db.add(session)
    db.commit()
    db.refresh(session)

    # ── Send application confirmation email to candidate ──────
    try:
        from services import email_service
        job = db.query(Job).filter(Job.id == candidate.job_id).first()
        job_title = job.title if job else "the position"
        background_tasks.add_task(
            email_service.send_application_received,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            job_title=job_title,
        )
    except Exception as e:
        logger.warning("[Email] Failed to schedule application received email: %s", e)

    return _session_with_token(session)


# ─── GET SESSION ──────────────────────────────────────────────

@router.get("/{session_id}", response_model=ScreeningSessionResponse)
def get_session(
    session_id: UUID,
    session: ScreeningSession = Depends(verify_screening_read_access),
):
    return session


# ─── UPLOAD RESUME ────────────────────────────────────────────

@router.post("/upload-resume")
@limiter.limit("5/minute")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    candidate_id: UUID = Form(...),
    file: Optional[UploadFile] = File(None),
    x_screening_token: Optional[str] = Header(None, alias="X-Screening-Token"),
    db: Session = Depends(get_db),
):
    """
    Upload a resume PDF (max 10 MB). Requires valid screening token.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    open_session = (
        db.query(ScreeningSession)
        .filter(
            ScreeningSession.candidate_id == candidate_id,
            ScreeningSession.completed_at == None,
        )
        .first()
    )
    if not open_session:
        raise HTTPException(status_code=400, detail="No active screening session")
    _validate_screening_token(open_session, x_screening_token)

    final_url = None
    file_bytes = None

    if file:
        if file.content_type not in ALLOWED_RESUME_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{file.content_type}'. Only PDF files are accepted.",
            )

        file_bytes = await file.read(MAX_RESUME_BYTES + 1)
        if len(file_bytes) > MAX_RESUME_BYTES:
            raise HTTPException(status_code=413, detail="Resume must be under 10 MB.")

        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Invalid PDF file.")

        try:
            s3_key = s3_upload_resume(file_bytes, str(candidate_id))
            final_url = key_to_url(s3_key)
        except Exception as e:
            logger.warning("[Screening] Resume upload failed: %s -- skipping resume URL", e)
            final_url = None

    if final_url:
        candidate.resume_url = final_url

    # ── Extract text from PDF using PyMuPDF ───────────────────
    if file_bytes:
        try:
            import fitz  # PyMuPDF
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                resume_text = "\n".join(page.get_text() for page in doc).strip()
            if resume_text:
                candidate.resume_text = resume_text[:10000]  # cap at 10k chars
                logger.info("[Screening] Extracted %d chars from resume PDF", len(resume_text))
                
                async def _parse_resume_bg(cid: UUID, text: str):
                    from core.database import SessionLocal
                    from services.llm.resume_parser import parse_resume_with_gemini
                    parsed_data = await parse_resume_with_gemini(text)
                    if parsed_data:
                        bg_db = SessionLocal()
                        try:
                            cand = bg_db.query(Candidate).filter(Candidate.id == cid).first()
                            if cand:
                                cand.resume_parsed_data = parsed_data
                                bg_db.commit()
                        except Exception as e:
                            logger.error("[Screening] Failed to save parsed resume data: %s", e)
                        finally:
                            bg_db.close()
                            
                background_tasks.add_task(_parse_resume_bg, candidate_id, candidate.resume_text)
                
        except Exception as e:
            logger.warning("[Screening] PDF text extraction failed: %s", e)

    db.commit()
    return {"status": "ok", "resume_url": final_url}


# ─── UPLOAD INTRO AUDIO ───────────────────────────────────────

@router.post("/upload-intro", response_model=ScreeningSessionResponse)
@limiter.limit("10/minute")
async def upload_intro(
    request: Request,
    session_id: UUID = Form(...),
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    detected_language: Optional[str] = Form(None),
    x_screening_token: Optional[str] = Header(None, alias="X-Screening-Token"),
    db: Session = Depends(get_db),
):
    """
    Process the candidate's intro audio.

    Two modes:
    1. Send raw audio file -> Sarvam STT runs automatically
    2. Send pre-computed transcript text -> stored directly

    After saving the transcript, automatically generates AI follow-up
    questions using Gemini and stores them in session.followup_questions.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _assert_session_open(session)
    _validate_screening_token(session, x_screening_token)

    final_transcript = transcript
    final_language = detected_language
    intro_audio_url = None

    # ── Case 1: Raw audio -> call Sarvam STT ──────────────────
    if file and not transcript:
        # ── Audio size validation ──────────────────────────────
        audio_bytes = await file.read(MAX_AUDIO_BYTES + 1)
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Audio file must be under 25 MB. Please record a shorter introduction.",
            )

        # Upload to storage for record-keeping
        try:
            s3_key = upload_audio(audio_bytes, str(session.candidate_id), label="intro")
            intro_audio_url = key_to_url(s3_key)
            session.intro_audio_url = intro_audio_url
        except Exception as e:
            logger.warning("[Screening] Audio upload failed: %s", e)

        # ── Detect MIME type from magic bytes ─────────────────
        fname = _detect_audio_filename(audio_bytes, file.filename)

        # Call Sarvam STT + Translate
        try:
            result = await transcribe_and_translate(
                audio_bytes=audio_bytes,
                filename=fname,
            )
            final_transcript = result.get("transcript", "")
            final_language = result.get("language_code", "unknown")

            # Validate transcript is not empty/too short
            if len((final_transcript or "").strip()) < 20:
                raise HTTPException(
                    status_code=422,
                    detail="Audio was too short or inaudible. Please re-record and speak clearly for at least 5 seconds.",
                )
            logger.info("[Screening] STT result: lang=%s, chars=%d", final_language, len(final_transcript))
        except SarvamError as e:
            logger.error("[Screening] Sarvam STT failed: %s", e)
            raise HTTPException(status_code=502, detail=f"Sarvam STT failed: {e.detail}")

    # ── Save transcript ────────────────────────────────────────
    session.intro_transcript = final_transcript
    session.intro_language = final_language

    if final_language:
        candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
        if candidate:
            candidate.detected_language = final_language

    # ── Generate follow-up questions via Gemini ───────────────
    if final_transcript:
        try:
            candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
            job = db.query(Job).filter(Job.id == candidate.job_id).first() if candidate else None
            job_title = job.title if job else "Software Engineer"
            required_skills = job.required_skills if job else []

            from services.llm.gemini_client import generate_followup_questions
            questions = await generate_followup_questions(
                intro_transcript=final_transcript,
                job_title=job_title,
                required_skills=required_skills,
                github_url=candidate.github_url if candidate else None,
                n=3,
            )
            session.followup_questions = questions
            logger.info("[Screening] Generated %d follow-up questions via Gemini", len(questions))
        except Exception as e:
            # Don't fail the whole intro upload if question generation fails
            logger.warning("[Screening] Follow-up question generation failed: %s", e)
            session.followup_questions = _default_questions()

    db.commit()
    db.refresh(session)
    return session


def _detect_audio_filename(audio_bytes: bytes, original_filename: Optional[str]) -> str:
    """
    Detect audio format from magic bytes.
    Supports: WebM, Ogg, MP3, M4A/AAC, WAV (default fallback).
    """
    if len(audio_bytes) < 4:
        return original_filename or "audio.wav"

    header = audio_bytes[:12]

    if header[:4] == b'\x1aE\xdf\xa3':
        return "audio.webm"
    if header[:4] == b'OggS':
        return "audio.ogg"
    if header[:3] == b'ID3' or header[:2] == b'\xff\xfb' or header[:2] == b'\xff\xf3':
        return "audio.mp3"
    if header[4:8] == b'ftyp':  # M4A / AAC container
        return "audio.m4a"
    if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
        return "audio.wav"

    # Fall back to original filename hint or WAV
    return original_filename or "audio.wav"


def _default_questions() -> list:
    """Generic fallback questions when AI generation is unavailable."""
    return [
        "Tell me about a challenging technical problem you solved recently.",
        "Describe a project where you had to make an important architectural decision.",
        "How do you approach debugging a production issue you've never seen before?",
    ]


# ─── UPLOAD ANSWER AUDIO ──────────────────────────────────────

@router.post("/upload-answer", response_model=ScreeningSessionResponse)
@limiter.limit("20/minute")
async def upload_answer(
    request: Request,
    session_id: UUID = Form(...),
    question_index: int = Form(...),
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    code: Optional[str] = Form(None),
    x_screening_token: Optional[str] = Header(None, alias="X-Screening-Token"),
    db: Session = Depends(get_db),
):
    """
    Process one follow-up answer audio.
    question_index is 0-based, matching the followup_questions array.
    Like upload-intro: accepts raw audio (-> Sarvam STT) or pre-computed transcript.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _assert_session_open(session)
    _validate_screening_token(session, x_screening_token)

    questions = session.followup_questions or []
    if question_index < 0 or (questions and question_index >= len(questions)):
        raise HTTPException(status_code=400, detail="Invalid question index")

    final_transcript = transcript
    answer_audio_url = None

    # ── Case 1: Raw audio -> Sarvam STT ───────────────────────
    if file and not transcript:
        # ── Audio size validation ──────────────────────────────
        audio_bytes = await file.read(MAX_AUDIO_BYTES + 1)
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Audio file must be under 25 MB.",
            )

        try:
            s3_key = upload_audio(audio_bytes, str(session.candidate_id), label=f"answer_{question_index}")
            answer_audio_url = key_to_url(s3_key)
        except Exception as e:
            logger.warning("[Screening] S3 answer upload failed: %s", e)

        try:
            fname = _detect_audio_filename(audio_bytes, file.filename)
            result = await transcribe_and_translate(
                audio_bytes=audio_bytes,
                filename=fname,
            )
            final_transcript = result.get("transcript", "")
        except SarvamError as e:
            logger.error("[Screening] Sarvam STT (answer) failed: %s", e)
            raise HTTPException(status_code=502, detail=f"Sarvam STT failed: {e.detail}")

    # ── Update answers list ────────────────────────────────────
    answers: list = list(session.followup_answers or [])
    while len(answers) <= question_index:
        answers.append({})

    answers[question_index] = {
        "transcript": final_transcript,
        "answer_audio_url": answer_audio_url,
        "code": code,
    }

    session.followup_answers = answers
    db.commit()
    db.refresh(session)
    return session


# ─── COMPLETE SCREENING ───────────────────────────────────────

@router.post("/complete/{session_id}", response_model=ScreeningSessionResponse)
@limiter.limit("5/minute")
async def complete_screening(
    request: Request,
    session_id: UUID,
    background_tasks: BackgroundTasks,
    proctoring_flags: Optional[dict] = None,
    x_screening_token: Optional[str] = Header(None, alias="X-Screening-Token"),
    db: Session = Depends(get_db),
):
    """
    Mark the session complete -> update candidate status -> fire AI evaluation.

    Evaluation mode (set via ASYNC_EVAL in .env):
      - ASYNC_EVAL=false (default): runs evaluation in background after response.
      - ASYNC_EVAL=true:            queues a Celery task and returns immediately.

    Emails (candidate + all HR users) are sent INSIDE the background task,
    AFTER evaluation is complete, so the score is always available.
    """
    session = db.query(ScreeningSession).filter(ScreeningSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _assert_session_open(session)
    _validate_screening_token(session, x_screening_token)

    if not session.intro_transcript:
        raise HTTPException(status_code=400, detail="Intro recording required before completing")

    existing_score = db.query(CompetencyScore).filter(
        CompetencyScore.session_id == session_id
    ).first()
    if existing_score:
        return session

    session.completed_at = datetime.now(timezone.utc)
    if proctoring_flags:
        session.proctoring_flags = proctoring_flags

    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
    if candidate:
        candidate.status = "screened"

    db.commit()
    db.refresh(session)

    # ── Fire evaluation in background (non-blocking) ──────────
    async def _run_eval_bg(sid, candidate_id):
        """Background evaluation + post-eval emails — runs after /complete returned."""
        from core.database import SessionLocal
        bg_db = SessionLocal()
        try:
            from services.pipeline.evaluator import run_evaluation
            score = await run_evaluation(sid, bg_db)

            if score:
                logger.info("[Screening] BG evaluation done, score=%.2f", score.total_score,
                            extra={"session_id": str(sid)})
            else:
                logger.warning("[Screening] BG evaluation returned None",
                               extra={"session_id": str(sid)})
        except Exception as e:
            logger.error("[Screening] BG evaluation error: %s", e, exc_info=True)
        finally:
            bg_db.close()

    if settings.ASYNC_EVAL:
        try:
            from services.background.tasks import evaluate_candidate_task
            evaluate_candidate_task.delay(str(session_id))
            logger.info("[Screening] Celery task queued", extra={"session_id": str(session_id)})
        except Exception as e:
            logger.warning("[Screening] Celery unavailable, falling back to BG task: %s", e)
            background_tasks.add_task(_run_eval_bg, session.id, session.candidate_id)
    else:
        background_tasks.add_task(_run_eval_bg, session.id, session.candidate_id)

    return session


# ─── SECURE PUBLIC ROUTE TO FETCH JOB OF AN ACTIVE SESSION ───
@router.get("/{session_id}/job", status_code=status.HTTP_200_OK)
def get_session_job(
    session_id: UUID,
    session: ScreeningSession = Depends(verify_screening_read_access),
    db: Session = Depends(get_db),
):
    """Return job details for a screening session (requires screening token or HR auth)."""
    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = db.query(Job).filter(Job.id == candidate.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": str(job.id),
        "title": job.title,
        "department": job.department,
        "required_skills": job.required_skills,
    }