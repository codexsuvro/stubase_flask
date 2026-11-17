"""Add PDF metadata to assignment submissions

Revision ID: 73ad8b112c4f
Revises: 5b5b0f8a4968
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa


revision = "73ad8b112c4f"
down_revision = "5b5b0f8a4968"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "assignment_submissions",
        sa.Column("pdf_object_key", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "assignment_submissions",
        sa.Column("pdf_filename", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("assignment_submissions", "pdf_filename")
    op.drop_column("assignment_submissions", "pdf_object_key")
