"""production_hardening

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-20

Production hardening migration — all ops are idempotent (safe to re-run).
  1. Add composite unique index (email, job_id) on candidates
  2. Add updated_at to all tables
  3. Add performance indexes
  4. Add soft-delete columns to jobs
  5. Add missing columns where absent
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect, text

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    """Check if a column already exists in a table."""
    conn = op.get_bind()
    inspector = inspect(conn)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def _index_exists(index_name: str) -> bool:
    """Check if an index already exists."""
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
        {"name": index_name},
    )
    return result.fetchone() is not None


def _constraint_exists(table: str, constraint_name: str) -> bool:
    """Check if a constraint exists."""
    conn = op.get_bind()
    result = conn.execute(
        text(
            "SELECT 1 FROM information_schema.table_constraints "
            "WHERE table_name = :table AND constraint_name = :name"
        ),
        {"table": table, "name": constraint_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    # ── 1. Drop old global unique constraint on candidates.email ──
    # Try multiple possible constraint names that Postgres may have generated.
    for cname in ("candidates_email_key", "uq_candidates_email"):
        if _constraint_exists("candidates", cname):
            op.drop_constraint(cname, "candidates", type_="unique")
            break

    # ── 2. Add composite unique index (email, job_id) ─────────────
    if not _index_exists("ix_candidates_email_job_id"):
        op.create_index(
            "ix_candidates_email_job_id",
            "candidates",
            ["email", "job_id"],
            unique=True,
        )

    # ── 3. Add updated_at to all tables ───────────────────────────
    for table in ("users", "jobs", "candidates", "screening_sessions", "competency_scores"):
        if not _column_exists(table, "updated_at"):
            op.add_column(table, sa.Column("updated_at", sa.TIMESTAMP, nullable=True))

    # ── 4. Performance indexes ────────────────────────────────────
    idx_map = {
        "ix_candidates_status":               ("candidates",         ["status"]),
        "ix_candidates_job_id":               ("candidates",         ["job_id"]),
        "ix_competency_scores_total_score":   ("competency_scores",  ["total_score"]),
        "ix_competency_scores_candidate_id":  ("competency_scores",  ["candidate_id"]),
        "ix_screening_sessions_candidate_id": ("screening_sessions", ["candidate_id"]),
    }
    for idx_name, (table, cols) in idx_map.items():
        if not _index_exists(idx_name):
            op.create_index(idx_name, table, cols)

    # ── 5. Soft-delete columns on jobs ────────────────────────────
    if not _column_exists("jobs", "deactivated_at"):
        op.add_column("jobs", sa.Column("deactivated_at", sa.TIMESTAMP, nullable=True))
    if not _column_exists("jobs", "deactivated_by"):
        op.add_column("jobs", sa.Column(
            "deactivated_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ))

    # ── 6. Missing columns ────────────────────────────────────────
    missing_cols = [
        ("competency_scores",  "eq_score",      sa.Column("eq_score", sa.Float, nullable=True)),
        ("screening_sessions", "proctoring_flags", sa.Column("proctoring_flags", postgresql.JSONB, nullable=True)),
        ("candidates",         "github_url",    sa.Column("github_url", sa.String(255), nullable=True)),
        ("candidates",         "consent_given", sa.Column("consent_given", sa.Boolean, server_default="false", nullable=True)),
    ]
    for table, col_name, col_def in missing_cols:
        if not _column_exists(table, col_name):
            op.add_column(table, col_def)


def downgrade() -> None:
    # Remove indexes
    for idx_name in (
        "ix_candidates_email_job_id",
        "ix_candidates_status",
        "ix_candidates_job_id",
        "ix_competency_scores_total_score",
        "ix_competency_scores_candidate_id",
        "ix_screening_sessions_candidate_id",
    ):
        if _index_exists(idx_name):
            op.drop_index(idx_name)

    # Restore global unique constraint
    if not _constraint_exists("candidates", "candidates_email_key"):
        op.create_unique_constraint("candidates_email_key", "candidates", ["email"])

    # Remove added columns
    for table, col in (
        ("users", "updated_at"),
        ("jobs", "updated_at"),
        ("jobs", "deactivated_at"),
        ("jobs", "deactivated_by"),
        ("candidates", "updated_at"),
        ("candidates", "consent_given"),
        ("candidates", "github_url"),
        ("screening_sessions", "updated_at"),
        ("screening_sessions", "proctoring_flags"),
        ("competency_scores", "updated_at"),
        ("competency_scores", "eq_score"),
    ):
        if _column_exists(table, col):
            op.drop_column(table, col)
