from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# ─── JOB SCHEMAS ─────────────────────────────────────────────

class JobBase(BaseModel):
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = []
    competency_weights: Optional[Dict[str, float]] = {
        "technical_depth": 0.25,
        "first_principles": 0.20,
        "shipping_velocity": 0.20,
        "ownership_signals": 0.15,
        "curiosity_depth": 0.10,
        "multilingual_fluency": 0.10,
    }

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    competency_weights: Optional[Dict[str, float]] = None
    is_active: Optional[bool] = None

class JobResponse(JobBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── CANDIDATE SCHEMAS ────────────────────────────────────────

class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    github_url: Optional[str] = None
    job_id: UUID
    consent_given: bool = False

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: UUID
    resume_url: Optional[str] = None
    github_url: Optional[str] = None
    detected_language: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class CandidateStatusUpdate(BaseModel):
    status: str  # applied | screened | shortlisted | interviewing | offered | rejected

class PaginatedCandidates(BaseModel):
    total: int
    items: List[CandidateResponse]


# ─── SCREENING SCHEMAS ────────────────────────────────────────

class FollowUpQuestion(BaseModel):
    question: str
    audio_url: Optional[str] = None
    transcript: Optional[str] = None

class FollowUpAnswer(BaseModel):
    answer_audio_url: Optional[str] = None
    transcript: Optional[str] = None

class ScreeningSessionResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    intro_transcript: Optional[str] = None
    intro_language: Optional[str] = None
    followup_questions: Optional[List[Any]] = []   # list of strings or dicts from DB
    followup_answers: Optional[List[Any]] = []     # list of {transcript, audio_url} dicts
    proctoring_flags: Optional[Dict[str, Any]] = None
    total_duration_seconds: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ScreeningStartRequest(BaseModel):
    candidate_id: UUID

class ScreeningUploadIntroRequest(BaseModel):
    session_id: UUID
    transcript: Optional[str] = None        # filled once Sarvam STT is wired
    detected_language: Optional[str] = None

class ScreeningUploadAnswerRequest(BaseModel):
    session_id: UUID
    question_index: int
    transcript: Optional[str] = None


# ─── COMPETENCY SCHEMAS ───────────────────────────────────────

class CompetencyScoreResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    session_id: UUID
    technical_depth: Optional[float] = None
    first_principles: Optional[float] = None
    shipping_velocity: Optional[float] = None
    ownership_signals: Optional[float] = None
    curiosity_depth: Optional[float] = None
    multilingual_fluency: Optional[float] = None
    total_score: Optional[float] = None
    justifications: Optional[Dict[str, str]] = {}
    flags: Optional[List[str]] = []
    hr_summary: Optional[str] = None
    hr_summary_audio_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── DASHBOARD SCHEMAS ────────────────────────────────────────

class PipelineStageSummary(BaseModel):
    status: str
    count: int

class DashboardPipelineResponse(BaseModel):
    total_candidates: int
    stages: List[PipelineStageSummary]

class CandidateWithScore(BaseModel):
    candidate: CandidateResponse
    score: Optional[CompetencyScoreResponse] = None


# ─── ANALYTICS SCHEMAS ────────────────────────────────────────

class AnalyticsEventCreate(BaseModel):
    event_type: str
    candidate_id: Optional[UUID] = None
    job_id: Optional[UUID] = None
    event_metadata: Optional[Dict[str, Any]] = {}

class FunnelItem(BaseModel):
    stage: str
    count: int

class DropOffItem(BaseModel):
    from_stage: str
    to_stage: str
    drop_off_rate: float


# ─── AUTH SCHEMAS ─────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─── USER SCHEMAS ─────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "hr"

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True