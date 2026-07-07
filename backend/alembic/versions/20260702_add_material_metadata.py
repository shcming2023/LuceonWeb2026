"""add material metadata table

Revision ID: 20260702_add_material_metadata
Revises: 20260630_add_weknora_chapter_status_fields
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260702_add_material_metadata"
down_revision: Union[str, None] = "20260630_add_weknora_chapter_status_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _table_exists("material_metadata"):
        return
    op.create_table(
        "material_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("material_pk", sa.Integer(), nullable=False),
        sa.Column("original_title", sa.String(length=512), nullable=True),
        sa.Column("publication_date", sa.String(length=64), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("edition", sa.String(length=256), nullable=True),
        sa.Column("subject", sa.String(length=128), nullable=True),
        sa.Column("publication_country", sa.String(length=128), nullable=True),
        sa.Column("series_name", sa.String(length=256), nullable=True),
        sa.Column("publisher", sa.String(length=256), nullable=True),
        sa.Column("isbn", sa.String(length=128), nullable=True),
        sa.Column("language", sa.String(length=128), nullable=True),
        sa.Column("grade_level", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="missing"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("evidence_json", sa.Text(), nullable=True),
        sa.Column("sample_json", sa.Text(), nullable=True),
        sa.Column("extraction_model", sa.String(length=128), nullable=True),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "material_pk", name="uq_material_metadata_user_material"),
    )
    for column in (
        "user_id",
        "material_pk",
        "original_title",
        "publication_year",
        "edition",
        "subject",
        "publication_country",
        "series_name",
        "publisher",
        "isbn",
        "language",
        "grade_level",
        "status",
        "source",
        "manual_override",
        "created_at",
    ):
        op.create_index(f"ix_material_metadata_{column}", "material_metadata", [column], unique=False)


def downgrade() -> None:
    if not _table_exists("material_metadata"):
        return
    for column in (
        "created_at",
        "manual_override",
        "source",
        "status",
        "grade_level",
        "language",
        "isbn",
        "publisher",
        "series_name",
        "publication_country",
        "subject",
        "edition",
        "publication_year",
        "original_title",
        "material_pk",
        "user_id",
    ):
        op.drop_index(f"ix_material_metadata_{column}", table_name="material_metadata")
    op.drop_table("material_metadata")
