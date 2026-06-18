"""initial_schema

Revision ID: 8eccc1957bd5
Revises:
Create Date: 2026-06-18

Creates all 5 tables for the Sarvam Talent Discovery Engine:
  - users
  - jobs
  - candidates
  - screening_sessions
  - competency_scores
  - analytics_events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8eccc1957bd5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.String(50), server_default='hr'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()')),
    )

    # ── jobs ──────────────────────────────────────────────────
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('department', sa.String(100)),
        sa.Column('location', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('required_skills', postgresql.JSONB),
        sa.Column('competency_weights', postgresql.JSONB),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()')),
    )

    # ── candidates ────────────────────────────────────────────
    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255)),
        sa.Column('email', sa.String(255), unique=True),
        sa.Column('phone', sa.String(20)),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id')),
        sa.Column('resume_url', sa.Text),
        sa.Column('detected_language', sa.String(50)),
        sa.Column('status', sa.String(50), server_default='applied'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()')),
    )

    # ── screening_sessions ────────────────────────────────────
    op.create_table(
        'screening_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id')),
        sa.Column('intro_audio_url', sa.Text),
        sa.Column('intro_transcript', sa.Text),
        sa.Column('intro_language', sa.String(50)),
        sa.Column('followup_questions', postgresql.JSONB),
        sa.Column('followup_answers', postgresql.JSONB),
        sa.Column('total_duration_seconds', sa.Integer),
        sa.Column('completed_at', sa.TIMESTAMP),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()')),
    )

    # ── competency_scores ─────────────────────────────────────
    op.create_table(
        'competency_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('screening_sessions.id')),
        sa.Column('technical_depth', sa.Float),
        sa.Column('first_principles', sa.Float),
        sa.Column('shipping_velocity', sa.Float),
        sa.Column('ownership_signals', sa.Float),
        sa.Column('curiosity_depth', sa.Float),
        sa.Column('multilingual_fluency', sa.Float),
        sa.Column('total_score', sa.Float),
        sa.Column('justifications', postgresql.JSONB),
        sa.Column('flags', postgresql.JSONB),
        sa.Column('hr_summary', sa.Text),
        sa.Column('hr_summary_audio_url', sa.Text),
        sa.Column('raw_105b_response', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()')),
    )

    # ── analytics_events ──────────────────────────────────────
    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(100)),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id')),
        sa.Column('event_metadata', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('analytics_events')
    op.drop_table('competency_scores')
    op.drop_table('screening_sessions')
    op.drop_table('candidates')
    op.drop_table('jobs')
    op.drop_table('users')
