import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="hr")   # hr | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    department = Column(String(100))
    location = Column(String(100))
    description = Column(Text)
    required_skills = Column(JSONB)        # ["LangGraph", "RAG", "Python"]
    competency_weights = Column(JSONB)     # {"technical_depth": 0.3, ...}
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    phone = Column(String(20))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    resume_url = Column(Text)
    detected_language = Column(String(50))
    status = Column(String(50), default="applied")
    # applied → screened → shortlisted → interviewing → offered → rejected
    created_at = Column(TIMESTAMP, server_default=func.now())


class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"))
    intro_audio_url = Column(Text)
    intro_transcript = Column(Text)
    intro_language = Column(String(50))
    followup_questions = Column(JSONB)     # [{question, audio_url, transcript}]
    followup_answers = Column(JSONB)       # [{answer_audio_url, transcript}]
    total_duration_seconds = Column(Integer)
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())


class CompetencyScore(Base):
    __tablename__ = "competency_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("screening_sessions.id"))
    technical_depth = Column(Float)
    first_principles = Column(Float)
    shipping_velocity = Column(Float)
    ownership_signals = Column(Float)
    curiosity_depth = Column(Float)
    multilingual_fluency = Column(Float)
    total_score = Column(Float)
    justifications = Column(JSONB)         # {"technical_depth": "reason..."}
    flags = Column(JSONB)                  # ["low_shipping_velocity", ...]
    hr_summary = Column(Text)
    hr_summary_audio_url = Column(Text)
    raw_105b_response = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100))
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    event_metadata = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())