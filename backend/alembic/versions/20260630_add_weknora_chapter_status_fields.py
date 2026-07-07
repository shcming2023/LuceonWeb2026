"""compatibility stamp for legacy WeKnora chapter status revision

Revision ID: 20260630_add_weknora_chapter_status_fields
Revises: 20260628_add_final_review_tables
Create Date: 2026-06-30 00:00:00.000000

This LuceonWeb review baseline does not define WeKnora chapter status
columns, but some local review databases were stamped with this revision
while sharing runtime data with the WeKnora lab. Keep the revision known so
`alembic upgrade head` can validate the current DB without mutating schema.
"""
from typing import Sequence, Union


revision: str = "20260630_add_weknora_chapter_status_fields"
down_revision: Union[str, None] = "20260628_add_final_review_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
