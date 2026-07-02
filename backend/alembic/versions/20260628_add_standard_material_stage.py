"""add standard material stage

Revision ID: 20260628_add_standard_material_stage
Revises: 20260619_add_material_pipeline
Create Date: 2026-06-28 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260628_add_standard_material_stage"
down_revision: Union[str, None] = "20260619_add_material_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {column["name"] for column in inspect(op.get_bind()).get_columns("materials")}
    if "standard_manifest_bucket" not in existing:
        op.add_column("materials", sa.Column("standard_manifest_bucket", sa.String(length=128), nullable=True))
    if "standard_manifest_object" not in existing:
        op.add_column("materials", sa.Column("standard_manifest_object", sa.String(length=1024), nullable=True))
    if "standard_run_id" not in existing:
        op.add_column("materials", sa.Column("standard_run_id", sa.String(length=128), nullable=True))
    if "standard_quality_score" not in existing:
        op.add_column("materials", sa.Column("standard_quality_score", sa.Integer(), nullable=True))


def downgrade() -> None:
    existing = {column["name"] for column in inspect(op.get_bind()).get_columns("materials")}
    if "standard_quality_score" in existing:
        op.drop_column("materials", "standard_quality_score")
    if "standard_run_id" in existing:
        op.drop_column("materials", "standard_run_id")
    if "standard_manifest_object" in existing:
        op.drop_column("materials", "standard_manifest_object")
    if "standard_manifest_bucket" in existing:
        op.drop_column("materials", "standard_manifest_bucket")
