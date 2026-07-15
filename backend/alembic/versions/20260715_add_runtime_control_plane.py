"""add durable runtime backup jobs

Revision ID: 20260715_runtime_control_plane
Revises: 20260715_add_domain_workspaces
Create Date: 2026-07-15 18:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260715_runtime_control_plane"
down_revision: Union[str, None] = "20260715_add_domain_workspaces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "backup_jobs" in set(inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "backup_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requested_by_user_id", sa.String(length=64), nullable=False),
        sa.Column("parent_job_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("mode", sa.String(length=16), nullable=False, server_default="manifest"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("target_snapshot_json", sa.Text(), nullable=False),
        sa.Column("bucket_scope_json", sa.Text(), nullable=False),
        sa.Column("include_legacy", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_objects", sa.Integer(), nullable=False, server_default="500000"),
        sa.Column("worker_id", sa.String(length=128), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("object_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("copied_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bytes_copied", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("truncated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("alert_level", sa.String(length=16), nullable=True),
        sa.Column("alert_message", sa.Text(), nullable=True),
        sa.Column("alert_acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_backup_jobs_idempotency_key"),
    )
    for column in ("requested_by_user_id", "parent_job_id", "status", "mode", "worker_id", "lease_expires_at", "created_at"):
        op.create_index(f"ix_backup_jobs_{column}", "backup_jobs", [column], unique=False)


def downgrade() -> None:
    if "backup_jobs" in set(inspect(op.get_bind()).get_table_names()):
        op.drop_table("backup_jobs")
