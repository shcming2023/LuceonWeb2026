"""add review assets

Revision ID: 20260615_add_review_assets
Revises: 20260613_add_parse_progress_fields
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260615_add_review_assets"
down_revision: Union[str, None] = "20260613_add_parse_progress_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("material_id", sa.String(length=128), nullable=True),
        sa.Column("run_id", sa.String(length=128), nullable=True),
        sa.Column("manifest_bucket", sa.String(length=128), nullable=False),
        sa.Column("manifest_object", sa.String(length=1024), nullable=False),
        sa.Column("source_pdf_bucket", sa.String(length=128), nullable=True),
        sa.Column("source_pdf_object", sa.String(length=1024), nullable=True),
        sa.Column("markdown_bucket", sa.String(length=128), nullable=True),
        sa.Column("markdown_object", sa.String(length=1024), nullable=True),
        sa.Column("page_markdown_bucket", sa.String(length=128), nullable=True),
        sa.Column("page_markdown_object", sa.String(length=1024), nullable=True),
        sa.Column("popo_markdown_bucket", sa.String(length=128), nullable=True),
        sa.Column("popo_markdown_object", sa.String(length=1024), nullable=True),
        sa.Column("middle_json_bucket", sa.String(length=128), nullable=True),
        sa.Column("middle_json_object", sa.String(length=1024), nullable=True),
        sa.Column("manifest_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_assets_user_id", "review_assets", ["user_id"], unique=False)
    op.create_index("ix_review_assets_title", "review_assets", ["title"], unique=False)
    op.create_index("ix_review_assets_material_id", "review_assets", ["material_id"], unique=False)
    op.create_index("ix_review_assets_run_id", "review_assets", ["run_id"], unique=False)
    op.create_index("ix_review_assets_created_at", "review_assets", ["created_at"], unique=False)
    op.create_index(
        "idx_review_user_manifest",
        "review_assets",
        ["user_id", "manifest_bucket", "manifest_object"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_review_user_manifest", table_name="review_assets")
    op.drop_index("ix_review_assets_created_at", table_name="review_assets")
    op.drop_index("ix_review_assets_run_id", table_name="review_assets")
    op.drop_index("ix_review_assets_material_id", table_name="review_assets")
    op.drop_index("ix_review_assets_title", table_name="review_assets")
    op.drop_index("ix_review_assets_user_id", table_name="review_assets")
    op.drop_table("review_assets")
