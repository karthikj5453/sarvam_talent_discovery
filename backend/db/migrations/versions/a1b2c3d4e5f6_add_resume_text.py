"""add resume_text to candidates

Revision ID: a1b2c3d4e5f6
Revises: 8eccc1957bd5
Create Date: 2026-06-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = '8eccc1957bd5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'candidates',
        sa.Column('resume_text', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('candidates', 'resume_text')
