"""add final review tables

Revision ID: 20260628_add_final_review_tables
Revises: 20260628_add_standard_material_stage
Create Date: 2026-06-28 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260628_add_final_review_tables"
down_revision: Union[str, None] = "20260628_add_standard_material_stage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _table_exists("final_review_sessions"):
        op.create_table(
            "final_review_sessions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("review_asset_id", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.String(length=128), nullable=False),
            sa.Column("standard_run_id", sa.String(length=128), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("summary_json", sa.Text(), nullable=True),
            sa.Column("submitted_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_final_review_sessions_user_id", "final_review_sessions", ["user_id"], unique=False)
        op.create_index("ix_final_review_sessions_review_asset_id", "final_review_sessions", ["review_asset_id"], unique=False)
        op.create_index("ix_final_review_sessions_material_id", "final_review_sessions", ["material_id"], unique=False)
        op.create_index("ix_final_review_sessions_standard_run_id", "final_review_sessions", ["standard_run_id"], unique=False)
        op.create_index("ix_final_review_sessions_status", "final_review_sessions", ["status"], unique=False)
        op.create_index("ix_final_review_sessions_created_at", "final_review_sessions", ["created_at"], unique=False)
        op.create_index(
            "idx_final_review_session_asset",
            "final_review_sessions",
            ["user_id", "review_asset_id", "standard_run_id"],
            unique=False,
        )

    if not _table_exists("final_review_annotations"):
        op.create_table(
            "final_review_annotations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("issue_type", sa.String(length=64), nullable=False),
            sa.Column("severity", sa.String(length=16), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("human_note", sa.Text(), nullable=True),
            sa.Column("anchors_json", sa.Text(), nullable=True),
            sa.Column("evidence_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_final_review_annotations_session_id", "final_review_annotations", ["session_id"], unique=False)
        op.create_index("ix_final_review_annotations_user_id", "final_review_annotations", ["user_id"], unique=False)
        op.create_index("ix_final_review_annotations_issue_type", "final_review_annotations", ["issue_type"], unique=False)
        op.create_index("ix_final_review_annotations_severity", "final_review_annotations", ["severity"], unique=False)
        op.create_index("ix_final_review_annotations_status", "final_review_annotations", ["status"], unique=False)
        op.create_index("ix_final_review_annotations_created_at", "final_review_annotations", ["created_at"], unique=False)
        op.create_index(
            "idx_final_review_annotation_session",
            "final_review_annotations",
            ["session_id", "status"],
            unique=False,
        )

    if not _table_exists("final_review_verifications"):
        op.create_table(
            "final_review_verifications",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("annotation_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("root_cause_stage", sa.String(length=64), nullable=False),
            sa.Column("root_cause_label", sa.String(length=64), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("evidence_json", sa.Text(), nullable=True),
            sa.Column("proposed_action_json", sa.Text(), nullable=True),
            sa.Column("model_info_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_final_review_verifications_annotation_id", "final_review_verifications", ["annotation_id"], unique=False)
        op.create_index("ix_final_review_verifications_user_id", "final_review_verifications", ["user_id"], unique=False)
        op.create_index("ix_final_review_verifications_status", "final_review_verifications", ["status"], unique=False)
        op.create_index("ix_final_review_verifications_root_cause_stage", "final_review_verifications", ["root_cause_stage"], unique=False)
        op.create_index("ix_final_review_verifications_root_cause_label", "final_review_verifications", ["root_cause_label"], unique=False)
        op.create_index("ix_final_review_verifications_created_at", "final_review_verifications", ["created_at"], unique=False)

    if not _table_exists("final_review_decisions"):
        op.create_table(
            "final_review_decisions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("annotation_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("decision", sa.String(length=64), nullable=False),
            sa.Column("reviewer_note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_final_review_decisions_annotation_id", "final_review_decisions", ["annotation_id"], unique=False)
        op.create_index("ix_final_review_decisions_user_id", "final_review_decisions", ["user_id"], unique=False)
        op.create_index("ix_final_review_decisions_decision", "final_review_decisions", ["decision"], unique=False)
        op.create_index("ix_final_review_decisions_created_at", "final_review_decisions", ["created_at"], unique=False)


def downgrade() -> None:
    if _table_exists("final_review_decisions"):
        op.drop_index("ix_final_review_decisions_created_at", table_name="final_review_decisions")
        op.drop_index("ix_final_review_decisions_decision", table_name="final_review_decisions")
        op.drop_index("ix_final_review_decisions_user_id", table_name="final_review_decisions")
        op.drop_index("ix_final_review_decisions_annotation_id", table_name="final_review_decisions")
        op.drop_table("final_review_decisions")
    if _table_exists("final_review_verifications"):
        op.drop_index("ix_final_review_verifications_created_at", table_name="final_review_verifications")
        op.drop_index("ix_final_review_verifications_root_cause_label", table_name="final_review_verifications")
        op.drop_index("ix_final_review_verifications_root_cause_stage", table_name="final_review_verifications")
        op.drop_index("ix_final_review_verifications_status", table_name="final_review_verifications")
        op.drop_index("ix_final_review_verifications_user_id", table_name="final_review_verifications")
        op.drop_index("ix_final_review_verifications_annotation_id", table_name="final_review_verifications")
        op.drop_table("final_review_verifications")
    if _table_exists("final_review_annotations"):
        op.drop_index("idx_final_review_annotation_session", table_name="final_review_annotations")
        op.drop_index("ix_final_review_annotations_created_at", table_name="final_review_annotations")
        op.drop_index("ix_final_review_annotations_status", table_name="final_review_annotations")
        op.drop_index("ix_final_review_annotations_severity", table_name="final_review_annotations")
        op.drop_index("ix_final_review_annotations_issue_type", table_name="final_review_annotations")
        op.drop_index("ix_final_review_annotations_user_id", table_name="final_review_annotations")
        op.drop_index("ix_final_review_annotations_session_id", table_name="final_review_annotations")
        op.drop_table("final_review_annotations")
    if _table_exists("final_review_sessions"):
        op.drop_index("idx_final_review_session_asset", table_name="final_review_sessions")
        op.drop_index("ix_final_review_sessions_created_at", table_name="final_review_sessions")
        op.drop_index("ix_final_review_sessions_status", table_name="final_review_sessions")
        op.drop_index("ix_final_review_sessions_standard_run_id", table_name="final_review_sessions")
        op.drop_index("ix_final_review_sessions_material_id", table_name="final_review_sessions")
        op.drop_index("ix_final_review_sessions_review_asset_id", table_name="final_review_sessions")
        op.drop_index("ix_final_review_sessions_user_id", table_name="final_review_sessions")
        op.drop_table("final_review_sessions")
