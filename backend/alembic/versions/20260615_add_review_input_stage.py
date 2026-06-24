"""add review input and stage fields

Revision ID: 20260615_add_review_input_stage
Revises: 20260615_add_review_metadata
Create Date: 2026-06-15 00:00:02.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260615_add_review_input_stage"
down_revision: Union[str, None] = "20260615_add_review_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("review_assets", sa.Column("input_filename", sa.String(length=512), nullable=True))
    op.add_column("review_assets", sa.Column("review_stage", sa.String(length=32), nullable=False, server_default="parse"))
    op.add_column("review_assets", sa.Column("input_pdf_bucket", sa.String(length=128), nullable=True))
    op.add_column("review_assets", sa.Column("input_pdf_object", sa.String(length=1024), nullable=True))
    op.create_index("ix_review_assets_input_filename", "review_assets", ["input_filename"], unique=False)
    op.create_index("ix_review_assets_review_stage", "review_assets", ["review_stage"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_review_assets_review_stage", table_name="review_assets")
    op.drop_index("ix_review_assets_input_filename", table_name="review_assets")
    op.drop_column("review_assets", "input_pdf_object")
    op.drop_column("review_assets", "input_pdf_bucket")
    op.drop_column("review_assets", "review_stage")
    op.drop_column("review_assets", "input_filename")
