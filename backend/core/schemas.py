from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from datetime import datetime

VALID_ROLES = ("hr", "interviewer", "admin")
VALID_STATUSES = ("applied", "screened", "shortlisted", "interviewing", "offered", "rejected")


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
        "shipping_velocity": 0.18,
        "ownership_signals": 0.14,
        "curiosity_depth": 0.10,
        "multilingual_fluency": 0.08,
        "eq_score": 0.05,
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
    resume_parsed_data: Optional[Dict[str, Any]] = None
    github_url: Optional[str] = None
    detected_language: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class CandidateStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {sorted(VALID_STATUSES)}")
        return v

class PaginatedCandidates(BaseModel):
    total: int
    items: List[CandidateResponse]

class PaginatedCandidatesWithScores(BaseModel):
    total: int
    items: List["CandidateWithScore"]


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
    intro_audio_url: Optional[str] = None
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

class ScreeningStartResponse(ScreeningSessionResponse):
    screening_token: str

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
    eq_score: Optional[float] = None
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
    refresh_token: Optional[str] = None  # Kept for backward compat; actual token is in HTTP-only cookie


class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─── USER SCHEMAS ─────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = "hr"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> str:
        role = v or "hr"
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {VALID_ROLES}")
        return role


class RecruiterNoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    is_pinned: bool = False


class RecruiterNoteResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    author_id: UUID
    author_name: Optional[str] = None
    content: str
    is_pinned: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    actor_name: Optional[str] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


PaginatedCandidatesWithScores.model_rebuild()