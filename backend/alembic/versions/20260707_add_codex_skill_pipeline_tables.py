"""add codex skill pipeline tables

Revision ID: 20260707_add_codex_skill_pipeline_tables
Revises: 20260705_add_latex_material_stage
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260707_add_codex_skill_pipeline_tables"
down_revision: Union[str, None] = "20260705_add_latex_material_stage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "material_outputs" not in tables:
        op.create_table(
            "material_outputs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("material_pk", sa.Integer(), nullable=True),
            sa.Column("material_id", sa.String(length=128), nullable=False),
            sa.Column("review_asset_id", sa.Integer(), nullable=True),
            sa.Column("output_type", sa.String(length=64), nullable=False),
            sa.Column("origin", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("quality_status", sa.String(length=32), nullable=False),
            sa.Column("is_current", sa.Boolean(), nullable=False),
            sa.Column("manifest_bucket", sa.String(length=128), nullable=False),
            sa.Column("manifest_object", sa.String(length=1024), nullable=False),
            sa.Column("output_run_id", sa.String(length=128), nullable=True),
            sa.Column("popo_run_id", sa.String(length=128), nullable=True),
            sa.Column("skill_name", sa.String(length=128), nullable=True),
            sa.Column("skill_version", sa.String(length=128), nullable=True),
            sa.Column("codex_job_id", sa.Integer(), nullable=True),
            sa.Column("version_label", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("promoted_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "manifest_bucket", "manifest_object", name="uq_material_output_manifest"),
        )
        op.create_index("ix_material_outputs_user_id", "material_outputs", ["user_id"])
        op.create_index("ix_material_outputs_material_pk", "material_outputs", ["material_pk"])
        op.create_index("ix_material_outputs_material_id", "material_outputs", ["material_id"])
        op.create_index("ix_material_outputs_review_asset_id", "material_outputs", ["review_asset_id"])
        op.create_index("ix_material_outputs_output_type", "material_outputs", ["output_type"])
        op.create_index("ix_material_outputs_origin", "material_outputs", ["origin"])
        op.create_index("ix_material_outputs_status", "material_outputs", ["status"])
        op.create_index("ix_material_outputs_quality_status", "material_outputs", ["quality_status"])
        op.create_index("ix_material_outputs_is_current", "material_outputs", ["is_current"])
        op.create_index("ix_material_outputs_output_run_id", "material_outputs", ["output_run_id"])
        op.create_index("ix_material_outputs_popo_run_id", "material_outputs", ["popo_run_id"])
        op.create_index("ix_material_outputs_skill_name", "material_outputs", ["skill_name"])
        op.create_index("ix_material_outputs_codex_job_id", "material_outputs", ["codex_job_id"])
        op.create_index("ix_material_outputs_created_at", "material_outputs", ["created_at"])
        op.create_index("idx_material_output_lookup", "material_outputs", ["user_id", "material_id", "output_type"])

    if "codex_skill_jobs" not in tables:
        op.create_table(
            "codex_skill_jobs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("material_pk", sa.Integer(), nullable=True),
            sa.Column("material_id", sa.String(length=128), nullable=False),
            sa.Column("review_asset_id", sa.Integer(), nullable=True),
            sa.Column("mode", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("requested_skill", sa.String(length=128), nullable=False),
            sa.Column("skill_version", sa.String(length=128), nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("source_popo_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("source_popo_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("baseline_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("baseline_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("output_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("output_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("codex_thread_id", sa.String(length=128), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False),
            sa.Column("staging_dir", sa.String(length=1024), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=True),
            sa.Column("result_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "idempotency_key", name="uq_codex_skill_job_idempotency"),
        )
        op.create_index("ix_codex_skill_jobs_user_id", "codex_skill_jobs", ["user_id"])
        op.create_index("ix_codex_skill_jobs_material_pk", "codex_skill_jobs", ["material_pk"])
        op.create_index("ix_codex_skill_jobs_material_id", "codex_skill_jobs", ["material_id"])
        op.create_index("ix_codex_skill_jobs_review_asset_id", "codex_skill_jobs", ["review_asset_id"])
        op.create_index("ix_codex_skill_jobs_mode", "codex_skill_jobs", ["mode"])
        op.create_index("ix_codex_skill_jobs_status", "codex_skill_jobs", ["status"])
        op.create_index("ix_codex_skill_jobs_idempotency_key", "codex_skill_jobs", ["idempotency_key"])
        op.create_index("ix_codex_skill_jobs_codex_thread_id", "codex_skill_jobs", ["codex_thread_id"])
        op.create_index("ix_codex_skill_jobs_created_at", "codex_skill_jobs", ["created_at"])
        op.create_index("idx_codex_skill_job_material", "codex_skill_jobs", ["user_id", "material_id", "status"])


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "codex_skill_jobs" in tables:
        op.drop_table("codex_skill_jobs")
    if "material_outputs" in tables:
        op.drop_table("material_outputs")
