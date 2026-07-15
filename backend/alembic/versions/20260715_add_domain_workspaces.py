"""add durable pipeline items, stage attempts, and metadata jobs

Revision ID: 20260715_add_domain_workspaces
Revises: 20260707_add_codex_skill_pipeline_tables
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260715_add_domain_workspaces"
down_revision: Union[str, None] = "20260707_add_codex_skill_pipeline_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())

    if "materials" in tables and "page_count" not in _columns("materials"):
        op.add_column("materials", sa.Column("page_count", sa.Integer(), nullable=True))

    if "pipeline_runs" in tables:
        columns = _columns("pipeline_runs")
        additions = (
            ("idempotency_key", sa.Column("idempotency_key", sa.String(length=128), nullable=True)),
            ("queue_slot", sa.Column("queue_slot", sa.String(length=32), nullable=True)),
            ("request_json", sa.Column("request_json", sa.Text(), nullable=True)),
            ("worker_id", sa.Column("worker_id", sa.String(length=128), nullable=True)),
            ("attempt_count", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0")),
            ("heartbeat_at", sa.Column("heartbeat_at", sa.DateTime(), nullable=True)),
            ("lease_expires_at", sa.Column("lease_expires_at", sa.DateTime(), nullable=True)),
        )
        for name, column in additions:
            if name not in columns:
                op.add_column("pipeline_runs", column)
        indexes = {index["name"] for index in inspect(op.get_bind()).get_indexes("pipeline_runs")}
        for name, column in (
            ("ix_pipeline_runs_idempotency_key", "idempotency_key"),
            ("ix_pipeline_runs_worker_id", "worker_id"),
            ("ix_pipeline_runs_lease_expires_at", "lease_expires_at"),
        ):
            if name not in indexes:
                op.create_index(name, "pipeline_runs", [column], unique=False)
        if "uq_pipeline_runs_queue_slot" not in indexes:
            active_ids = [
                row[0]
                for row in op.get_bind().execute(
                    sa.text("SELECT id FROM pipeline_runs WHERE status IN ('queued', 'running') ORDER BY id")
                )
            ]
            if len(active_ids) == 1:
                op.get_bind().execute(
                    sa.text("UPDATE pipeline_runs SET queue_slot = 'gpu' WHERE id = :run_id"),
                    {"run_id": active_ids[0]},
                )
            op.create_index("uq_pipeline_runs_queue_slot", "pipeline_runs", ["queue_slot"], unique=True)
        op.execute(
            sa.text(
                "UPDATE pipeline_runs SET request_json = "
                "'{\"history_status\":\"legacy_unverified\"}' WHERE request_json IS NULL"
            )
        )

    if "pipeline_run_items" not in tables:
        op.create_table(
            "pipeline_run_items",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("run_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("material_pk", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.String(length=128), nullable=False),
            sa.Column("input_bucket", sa.String(length=128), nullable=False),
            sa.Column("input_object", sa.String(length=1024), nullable=False),
            sa.Column("input_sha256", sa.String(length=128), nullable=True),
            sa.Column("filename", sa.String(length=512), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
            sa.Column("current_stage", sa.String(length=64), nullable=False, server_default="queued"),
            sa.Column("mineru_run_id", sa.String(length=128), nullable=True),
            sa.Column("mineru_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("mineru_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("popo_run_id", sa.String(length=128), nullable=True),
            sa.Column("popo_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("popo_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("error_code", sa.String(length=128), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("run_id", "material_pk", name="uq_pipeline_run_item_material"),
        )
        for column in (
            "run_id",
            "user_id",
            "material_pk",
            "material_id",
            "input_sha256",
            "status",
            "current_stage",
            "mineru_run_id",
            "popo_run_id",
            "created_at",
        ):
            op.create_index(f"ix_pipeline_run_items_{column}", "pipeline_run_items", [column], unique=False)
        op.create_index("idx_pipeline_run_item_status", "pipeline_run_items", ["run_id", "status"], unique=False)

    if "pipeline_stage_attempts" not in tables:
        op.create_table(
            "pipeline_stage_attempts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("run_item_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("stage", sa.String(length=64), nullable=False),
            sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
            sa.Column("external_batch_id", sa.String(length=128), nullable=True),
            sa.Column("external_run_id", sa.String(length=128), nullable=True),
            sa.Column("input_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("input_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("output_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("output_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("error_code", sa.String(length=128), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("evidence_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("run_item_id", "stage", "attempt", name="uq_pipeline_stage_attempt"),
        )
        for column in (
            "run_item_id",
            "user_id",
            "stage",
            "status",
            "external_batch_id",
            "external_run_id",
            "created_at",
        ):
            op.create_index(f"ix_pipeline_stage_attempts_{column}", "pipeline_stage_attempts", [column], unique=False)

    if "metadata_jobs" not in tables:
        op.create_table(
            "metadata_jobs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("material_pk", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("source_manifest_bucket", sa.String(length=128), nullable=True),
            sa.Column("source_manifest_object", sa.String(length=1024), nullable=True),
            sa.Column("source_manifest_sha256", sa.String(length=128), nullable=True),
            sa.Column("model", sa.String(length=128), nullable=True),
            sa.Column("prompt_version", sa.String(length=128), nullable=False, server_default="material-metadata-v1"),
            sa.Column("force", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("worker_id", sa.String(length=128), nullable=True),
            sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
            sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("result_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "idempotency_key", name="uq_metadata_job_idempotency"),
        )
        for column in (
            "user_id",
            "material_pk",
            "material_id",
            "status",
            "idempotency_key",
            "source_manifest_sha256",
            "worker_id",
            "lease_expires_at",
            "created_at",
        ):
            op.create_index(f"ix_metadata_jobs_{column}", "metadata_jobs", [column], unique=False)


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    for table in ("metadata_jobs", "pipeline_stage_attempts", "pipeline_run_items"):
        if table in tables:
            op.drop_table(table)

    if "pipeline_runs" in tables:
        columns = _columns("pipeline_runs")
        indexes = {index["name"] for index in inspect(op.get_bind()).get_indexes("pipeline_runs")}
        for name in (
            "ix_pipeline_runs_lease_expires_at",
            "ix_pipeline_runs_worker_id",
            "ix_pipeline_runs_idempotency_key",
            "uq_pipeline_runs_queue_slot",
        ):
            if name in indexes:
                op.drop_index(name, table_name="pipeline_runs")
        for column in (
            "lease_expires_at",
            "heartbeat_at",
            "attempt_count",
            "worker_id",
            "request_json",
            "idempotency_key",
            "queue_slot",
        ):
            if column in columns:
                op.drop_column("pipeline_runs", column)

    if "materials" in tables and "page_count" in _columns("materials"):
        op.drop_column("materials", "page_count")
