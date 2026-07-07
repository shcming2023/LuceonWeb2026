"""add latex material stage

Revision ID: 20260705_add_latex_material_stage
Revises: 20260702_add_material_metadata
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260705_add_latex_material_stage"
down_revision: Union[str, None] = "20260702_add_material_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing = {column["name"] for column in inspect(op.get_bind()).get_columns("materials")}
    if "latex_manifest_bucket" not in existing:
        op.add_column("materials", sa.Column("latex_manifest_bucket", sa.String(length=128), nullable=True))
    if "latex_manifest_object" not in existing:
        op.add_column("materials", sa.Column("latex_manifest_object", sa.String(length=1024), nullable=True))
    if "latex_run_id" not in existing:
        op.add_column("materials", sa.Column("latex_run_id", sa.String(length=128), nullable=True))


def downgrade() -> None:
    existing = {column["name"] for column in inspect(op.get_bind()).get_columns("materials")}
    if "latex_run_id" in existing:
        op.drop_column("materials", "latex_run_id")
    if "latex_manifest_object" in existing:
        op.drop_column("materials", "latex_manifest_object")
    if "latex_manifest_bucket" in existing:
        op.drop_column("materials", "latex_manifest_bucket")
