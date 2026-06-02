from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .service import JobStore, JobManager


SERVICE_VERSION = os.environ.get("POPO_SERVICE_VERSION", "mineru-popo-adapter.v0.2-async")
JOB_DIR = Path(os.environ.get("POPO_JOB_DIR", "runtime/jobs")).resolve()

app = FastAPI(title="MinerU-Popo Luceon CleanService (Async)", version=SERVICE_VERSION)
job_store = JobStore(JOB_DIR)
job_manager = JobManager(job_store)


def _has_model() -> bool:
    model_path = os.environ.get("POPO_MODEL_PATH", "").strip()
    return bool(model_path and Path(model_path).exists())


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "toc-rebuild",
        "engine": "mineru-popo",
        "version": SERVICE_VERSION,
        "protocol_version": "v1",
        "model_configured": _has_model(),
        "job_dir": str(JOB_DIR),
        "busy": job_manager.is_busy(),
    }


@app.post("/api/v1/jobs")
async def submit_job(request: Request) -> JSONResponse:
    payload = await request.json()
    job_id = payload.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise HTTPException(status_code=422, detail="job_id is required")

    # Idempotent for active/completed jobs. Recoverable full-background jobs may
    # be resumed after timeout/failure using the same job_id and work directory.
    if job_store.exists(job_id):
        existing = job_store.read(job_id)
        options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
        recoverable = options.get("recoverable") is True or str(options.get("toc_rebuild_mode") or "") in {"full-background", "full"}
        terminal_resume_state = str(existing.get("status") or "").lower() in {"timeout", "failed", "canceled"}
        if not (recoverable and terminal_resume_state):
            return JSONResponse(existing)

    if job_manager.is_busy():
        raise HTTPException(status_code=409, detail="已有目录重建任务运行中")

    # Mark as queued/running and start background task
    try:
        initial_state = job_manager.start_job(payload)
        return JSONResponse(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/v1/jobs/{job_id}:cancel")
async def cancel_job(job_id: str) -> JSONResponse:
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")

    if job_manager.cancel_job(job_id):
        return JSONResponse({"ok": True, "message": f"Job {job_id} canceled successfully"})
    else:
        return JSONResponse({"ok": False, "message": f"Job {job_id} is not running or could not be canceled"})


@app.get("/api/v1/jobs/{job_id}")
async def query_job(job_id: str) -> JSONResponse:
    if not job_store.exists(job_id):
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")

    data = job_store.read(job_id)

    with job_manager.lock:
        if job_id in job_manager.active_jobs:
            active_state = job_manager.active_jobs[job_id]
            from .service import _get_live_progress
            prog = _get_live_progress(active_state)
            data["progress"] = prog
            data["current_step"] = prog["current_step"]

    return JSONResponse(data)


@app.get("/api/v1/jobs")
async def list_jobs() -> dict[str, Any]:
    return {"jobs": job_store.list_ids()}
