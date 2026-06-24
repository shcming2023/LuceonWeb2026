"""add review metadata

Revision ID: 20260615_add_review_metadata
Revises: 20260615_add_review_assets
Create Date: 2026-06-15 00:00:01.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260615_add_review_metadata"
down_revision: Union[str, None] = "20260615_add_review_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("review_assets", sa.Column("review_status", sa.String(length=32), nullable=False, server_default="pending"))
    op.add_column("review_assets", sa.Column("review_tags", sa.Text(), nullable=True))
    op.add_column("review_assets", sa.Column("review_note", sa.Text(), nullable=True))
    op.add_column("review_assets", sa.Column("report_text", sa.Text(), nullable=True))
    op.add_column("review_assets", sa.Column("report_generated_at", sa.DateTime(), nullable=True))
    op.create_index("ix_review_assets_review_status", "review_assets", ["review_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_review_assets_review_status", table_name="review_assets")
    op.drop_column("review_assets", "report_generated_at")
    op.drop_column("review_assets", "report_text")
    op.drop_column("review_assets", "review_note")
    op.drop_column("review_assets", "review_tags")
    op.drop_column("review_assets", "review_status")
