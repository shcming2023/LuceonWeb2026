from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.workflow_v2.models import WorkflowBase
from app.workflow_v2.golden_set import ensure_golden_set


REQUIRED_WORKFLOW_TABLES = frozenset(WorkflowBase.metadata.tables)
REQUIRED_WORKFLOW_COLUMNS = {
    "stage_runs": {"heartbeat_at"},
    "model_calls": {"result_json"},
}


def _schema_status(engine: Engine) -> tuple[bool, str]:
    existing = set(inspect(engine).get_table_names())
    missing = sorted(REQUIRED_WORKFLOW_TABLES - existing)
    if missing:
        return False, f"missing workflow tables: {', '.join(missing)}"
    for table, required_columns in REQUIRED_WORKFLOW_COLUMNS.items():
        actual_columns = {row["name"] for row in inspect(engine).get_columns(table)}
        missing_columns = sorted(required_columns - actual_columns)
        if missing_columns:
            return False, f"missing {table} columns: {', '.join(missing_columns)}"
    return True, "ok"


def workflow_database_url() -> str:
    return os.getenv("WORKFLOW_DATABASE_URL", "").strip()


@lru_cache(maxsize=1)
def workflow_engine() -> Engine:
    url = workflow_database_url()
    if not url:
        raise RuntimeError("WORKFLOW_DATABASE_URL is not configured")
    options = {"pool_pre_ping": True, "pool_recycle": 1800}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **options)


@lru_cache(maxsize=1)
def workflow_session_factory():
    return sessionmaker(bind=workflow_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def initialize_workflow_database() -> dict[str, str | bool]:
    if not workflow_database_url():
        return {"configured": False, "ready": False, "detail": "WORKFLOW_DATABASE_URL is not configured"}
    try:
        WorkflowBase.metadata.create_all(bind=workflow_engine())
        _apply_compatible_migrations(workflow_engine())
        db = workflow_session_factory()()
        try:
            ensure_golden_set(db)
            db.commit()
        finally:
            db.close()
        with workflow_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        ready, detail = _schema_status(workflow_engine())
        return {"configured": True, "ready": ready, "detail": detail}
    except Exception as exc:
        return {"configured": True, "ready": False, "detail": str(exc)}


def _apply_compatible_migrations(engine: Engine) -> None:
    columns = {row["name"] for row in inspect(engine).get_columns("model_calls")}
    with engine.begin() as connection:
        if "result_json" not in columns:
            if engine.dialect.name == "mysql":
                connection.execute(text("ALTER TABLE model_calls ADD COLUMN result_json TEXT NULL"))
                connection.execute(text("UPDATE model_calls SET result_json = '{}' WHERE result_json IS NULL"))
                connection.execute(text("ALTER TABLE model_calls MODIFY result_json TEXT NOT NULL"))
            else:
                connection.execute(text("ALTER TABLE model_calls ADD COLUMN result_json TEXT NOT NULL DEFAULT '{}'"))
        if engine.dialect.name == "mysql":
            repair_columns = {row["name"]: row for row in inspect(engine).get_columns("repair_attempts")}
            length = getattr(repair_columns["repair_kind"]["type"], "length", 0) or 0
            if length < 64:
                connection.execute(text("ALTER TABLE repair_attempts MODIFY repair_kind VARCHAR(64) NOT NULL"))
        stage_columns = {row["name"] for row in inspect(engine).get_columns("stage_runs")}
        if "heartbeat_at" not in stage_columns:
            connection.execute(text("ALTER TABLE stage_runs ADD COLUMN heartbeat_at DATETIME NULL"))
            connection.execute(text("CREATE INDEX ix_stage_runs_heartbeat_at ON stage_runs (heartbeat_at)"))
        if engine.dialect.name == "mysql":
            stage_columns_by_name = {row["name"]: row for row in inspect(engine).get_columns("stage_runs")}
            length = getattr(stage_columns_by_name["stage_version"]["type"], "length", 0) or 0
            if length < 128:
                connection.execute(text("ALTER TABLE stage_runs MODIFY stage_version VARCHAR(128) NOT NULL"))


def workflow_database_health() -> dict[str, str | bool]:
    if not workflow_database_url():
        return {"configured": False, "ready": False, "dialect": "", "detail": "WORKFLOW_DATABASE_URL is not configured"}
    try:
        engine = workflow_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        ready, detail = _schema_status(engine)
        return {"configured": True, "ready": ready, "dialect": engine.dialect.name, "detail": detail}
    except Exception as exc:
        return {"configured": True, "ready": False, "dialect": "", "detail": str(exc)}


def get_workflow_db():
    try:
        factory = workflow_session_factory()
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
    db: Session = factory()
    try:
        yield db
    finally:
        db.close()
