"""add material pipeline ledger

Revision ID: 20260619_add_material_pipeline
Revises: 20260615_add_review_input_stage
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260619_add_material_pipeline"
down_revision: Union[str, None] = "20260615_add_review_input_stage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("material_id", sa.String(length=128), nullable=True),
        sa.Column("source_hash", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="imported"),
        sa.Column("input_bucket", sa.String(length=128), nullable=True),
        sa.Column("input_object", sa.String(length=1024), nullable=True),
        sa.Column("input_sha256", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("stage_status", sa.String(length=32), nullable=False, server_default="input"),
        sa.Column("pipeline_status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column("mineru_manifest_bucket", sa.String(length=128), nullable=True),
        sa.Column("mineru_manifest_object", sa.String(length=1024), nullable=True),
        sa.Column("mineru_run_id", sa.String(length=128), nullable=True),
        sa.Column("popo_manifest_bucket", sa.String(length=128), nullable=True),
        sa.Column("popo_manifest_object", sa.String(length=1024), nullable=True),
        sa.Column("popo_run_id", sa.String(length=128), nullable=True),
        sa.Column("raw_manifest_bucket", sa.String(length=128), nullable=True),
        sa.Column("raw_manifest_object", sa.String(length=1024), nullable=True),
        sa.Column("raw_run_id", sa.String(length=128), nullable=True),
        sa.Column("clean_manifest_bucket", sa.String(length=128), nullable=True),
        sa.Column("clean_manifest_object", sa.String(length=1024), nullable=True),
        sa.Column("clean_run_id", sa.String(length=128), nullable=True),
        sa.Column("review_asset_id", sa.Integer(), nullable=True),
        sa.Column("ignored", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_materials_user_id", "materials", ["user_id"], unique=False)
    op.create_index("ix_materials_material_id", "materials", ["material_id"], unique=False)
    op.create_index("ix_materials_source_hash", "materials", ["source_hash"], unique=False)
    op.create_index("ix_materials_title", "materials", ["title"], unique=False)
    op.create_index("ix_materials_filename", "materials", ["filename"], unique=False)
    op.create_index("ix_materials_source_type", "materials", ["source_type"], unique=False)
    op.create_index("ix_materials_input_sha256", "materials", ["input_sha256"], unique=False)
    op.create_index("ix_materials_stage_status", "materials", ["stage_status"], unique=False)
    op.create_index("ix_materials_pipeline_status", "materials", ["pipeline_status"], unique=False)
    op.create_index("ix_materials_review_asset_id", "materials", ["review_asset_id"], unique=False)
    op.create_index("ix_materials_created_at", "materials", ["created_at"], unique=False)
    op.create_index("idx_material_user_input", "materials", ["user_id", "input_bucket", "input_object"], unique=True)
    op.create_index("idx_material_user_material", "materials", ["user_id", "material_id"], unique=False)

    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="full"),
        sa.Column("command", sa.Text(), nullable=True),
        sa.Column("current_stage", sa.String(length=64), nullable=True),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pipeline_runs_user_id", "pipeline_runs", ["user_id"], unique=False)
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"], unique=False)
    op.create_index("ix_pipeline_runs_created_at", "pipeline_runs", ["created_at"], unique=False)

    op.create_table(
        "pipeline_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("stage", sa.String(length=64), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pipeline_events_run_id", "pipeline_events", ["run_id"], unique=False)
    op.create_index("ix_pipeline_events_user_id", "pipeline_events", ["user_id"], unique=False)
    op.create_index("ix_pipeline_events_created_at", "pipeline_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pipeline_events_created_at", table_name="pipeline_events")
    op.drop_index("ix_pipeline_events_user_id", table_name="pipeline_events")
    op.drop_index("ix_pipeline_events_run_id", table_name="pipeline_events")
    op.drop_table("pipeline_events")
    op.drop_index("ix_pipeline_runs_created_at", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_status", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_user_id", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
    op.drop_index("idx_material_user_material", table_name="materials")
    op.drop_index("idx_material_user_input", table_name="materials")
    op.drop_index("ix_materials_created_at", table_name="materials")
    op.drop_index("ix_materials_review_asset_id", table_name="materials")
    op.drop_index("ix_materials_pipeline_status", table_name="materials")
    op.drop_index("ix_materials_stage_status", table_name="materials")
    op.drop_index("ix_materials_input_sha256", table_name="materials")
    op.drop_index("ix_materials_source_type", table_name="materials")
    op.drop_index("ix_materials_filename", table_name="materials")
    op.drop_index("ix_materials_title", table_name="materials")
    op.drop_index("ix_materials_source_hash", table_name="materials")
    op.drop_index("ix_materials_material_id", table_name="materials")
    op.drop_index("ix_materials_user_id", table_name="materials")
    op.drop_table("materials")
