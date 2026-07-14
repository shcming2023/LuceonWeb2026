#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
DEFAULT_DB = REPO_ROOT / "runtime" / "backend" / "mineru.db"
DEFAULT_STAGING_ROOT = REPO_ROOT / "runtime" / "backend" / "codex-skill-work"
DEFAULT_LOG_ROOT = REPO_ROOT / "runtime" / "backend" / "codex-worker-control"

os.environ.setdefault("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")
os.environ.setdefault("PYTHONPATH", str(BACKEND_ROOT))
os.environ.setdefault("MINIO_ENDPOINT", "192.168.31.33:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "admin")
os.environ.setdefault("MINIO_SECRET_KEY", "admin123456")
os.environ.setdefault("MINIO_BUCKET", "mineru-files")
os.environ.setdefault("LUCEON_PUBLIC_API_BASE_URL", "http://host.docker.internal:28080")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.models.material import CodexSkillJob
from app.services.codex_skill_jobs import retry_codex_skill_job
from app.services.worker_v1_policy import v1_auto_retry_enabled


TERMINAL_STATES = {"published", "failed"}
ACTIVE_STATES = {"queued", "running", "publishing"}


@dataclass
class WorkerTask:
    job_id: int
    state: str
    message: str = ""
    db_status: str = ""
    started_at: str = ""
    finished_at: str = ""
    returncode: int | None = None
    log_path: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["job_id"] = str(self.job_id)
        data["running"] = self.state in ACTIVE_STATES
        return data


class WorkerController:
    def __init__(self, *, staging_root: Path, log_root: Path, timeout: int, max_quality_retries: int) -> None:
        self.staging_root = staging_root
        self.log_root = log_root
        self.timeout = timeout
        self.max_quality_retries = max(0, max_quality_retries) if v1_auto_retry_enabled() else 0
        self.tasks: dict[int, WorkerTask] = {}
        self.lock = threading.Lock()
        self.log_root.mkdir(parents=True, exist_ok=True)
        self.staging_root.mkdir(parents=True, exist_ok=True)

    def health(self) -> dict:
        return {
            "ok": True,
            "service": "codex-worker-controller",
            "codex_bin": shutil.which("codex") or "",
            "database_url": os.environ.get("DATABASE_URL", ""),
            "staging_root": str(self.staging_root),
            "timeout": self.timeout,
            "max_quality_retries": self.max_quality_retries,
        }

    def get_status(self, job_id: int) -> dict:
        with self.lock:
            task = self.tasks.get(job_id)
        db_job = self._db_job(job_id)
        if task:
            if db_job:
                task.db_status = str(db_job.get("status") or "")
                task_dict = task.to_dict()
                task_dict["job"] = db_job
                task_dict["material_output_id"] = self._material_output_id(db_job)
                task_dict["output_manifest"] = db_job.get("output_manifest")
                return task_dict
            return task.to_dict()
        if not db_job:
            return {"job_id": str(job_id), "state": "missing", "running": False, "message": "job not found"}
        db_status = str(db_job.get("status") or "")
        state = self._state_from_db(db_status)
        return {
            "job_id": str(job_id),
            "state": state,
            "running": db_status in {"running", "validating"},
            "db_status": db_status,
            "message": str(db_job.get("error_message") or ""),
            "started_at": db_job.get("started_at"),
            "finished_at": db_job.get("finished_at"),
            "job": db_job,
            "material_output_id": self._material_output_id(db_job),
            "output_manifest": db_job.get("output_manifest"),
        }

    def start(self, job_id: int) -> dict:
        db_job = self._db_job(job_id)
        if not db_job:
            return {"job_id": str(job_id), "state": "missing", "running": False, "message": "job not found"}
        db_status = str(db_job.get("status") or "")
        if db_status == "published":
            return self.get_status(job_id)

        with self.lock:
            current = self.tasks.get(job_id)
            if current and current.state in ACTIVE_STATES:
                return self.get_status(job_id)
            log_path = self.log_root / f"job-{job_id}.log"
            task = WorkerTask(
                job_id=job_id,
                state="queued",
                message="worker queued",
                db_status=db_status,
                started_at=datetime.utcnow().isoformat(),
                log_path=str(log_path),
            )
            self.tasks[job_id] = task

        self._mark_db_running(job_id)
        thread = threading.Thread(target=self._run_task, args=(job_id,), daemon=True)
        thread.start()
        return self.get_status(job_id)

    def _run_task(self, job_id: int) -> None:
        task = self.tasks[job_id]
        log_path = Path(task.log_path)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BACKEND_ROOT)
        env.setdefault("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")
        command_base = [
            sys.executable,
            str(BACKEND_ROOT / "scripts" / "codex_skill_worker.py"),
            "--job-id",
            str(job_id),
            "--staging-root",
            str(self.staging_root),
        ]

        try:
            with log_path.open("a", encoding="utf-8") as log:
                self._write_log(log, f"start job {job_id}")
                for quality_pass in range(self.max_quality_retries + 1):
                    label = "running Codex skill" if quality_pass == 0 else f"running quality repair {quality_pass}"
                    self._set_task(job_id, state="running", message=label)
                    run_cmd = [*command_base, "--run-codex"]
                    if self.timeout > 0:
                        run_cmd.extend(["--timeout", str(self.timeout)])
                    run_code = self._run_command(run_cmd, env, log)
                    if run_code != 0:
                        self._set_task(job_id, state="failed", message=f"Codex run failed: {run_code}", returncode=run_code)
                        return

                    self._set_task(job_id, state="publishing", message="validating and publishing staging output")
                    publish_code = self._run_command([*command_base, "--publish-staging"], env, log)
                    if publish_code == 0:
                        self._set_task(job_id, state="published", message="published", returncode=0)
                        self._write_log(log, f"job {job_id} published")
                        return
                    if quality_pass >= self.max_quality_retries:
                        self._set_task(job_id, state="failed", message=f"publish failed: {publish_code}", returncode=publish_code)
                        return
                    self._run_deterministic_repair(job_id, env, log)
                    if not self._retry_print_quality_failure(job_id):
                        self._set_task(job_id, state="failed", message=f"publish failed: {publish_code}", returncode=publish_code)
                        return
                    self._write_log(log, f"print-quality gate blocked job {job_id}; starting repair pass {quality_pass + 1}")
        except Exception as exc:
            self._set_task(job_id, state="failed", message=str(exc), returncode=1)
        finally:
            self._refresh_task_db_status(job_id)

    def _run_command(self, command: list[str], env: dict[str, str], log) -> int:
        self._write_log(log, "$ " + " ".join(command))
        completed = subprocess.run(
            command,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._write_log(log, f"exit {completed.returncode}")
        return completed.returncode

    def _set_task(self, job_id: int, **updates) -> None:
        with self.lock:
            task = self.tasks[job_id]
            for key, value in updates.items():
                setattr(task, key, value)
            if task.state in TERMINAL_STATES:
                task.finished_at = datetime.utcnow().isoformat()

    def _refresh_task_db_status(self, job_id: int) -> None:
        db_job = self._db_job(job_id)
        if not db_job:
            return
        with self.lock:
            task = self.tasks.get(job_id)
            if task:
                task.db_status = str(db_job.get("status") or "")

    def _write_log(self, log, line: str) -> None:
        log.write(f"[{datetime.utcnow().isoformat()}] {line}\n")
        log.flush()

    def _db_job(self, job_id: int) -> dict | None:
        db = SessionLocal()
        try:
            job = db.query(CodexSkillJob).filter(CodexSkillJob.id == job_id).first()
            return job.to_dict() if job else None
        finally:
            db.close()

    def _mark_db_running(self, job_id: int) -> None:
        db = SessionLocal()
        try:
            job = db.query(CodexSkillJob).filter(CodexSkillJob.id == job_id).first()
            if not job or job.status == "published":
                return
            job.status = "running"
            job.started_at = job.started_at or datetime.utcnow()
            job.finished_at = None
            db.commit()
        finally:
            db.close()

    def _material_output_id(self, db_job: dict) -> str:
        result = db_job.get("result") if isinstance(db_job.get("result"), dict) else {}
        return str(result.get("material_output_id") or "")

    def _retry_print_quality_failure(self, job_id: int) -> bool:
        db = SessionLocal()
        try:
            job = db.query(CodexSkillJob).filter(CodexSkillJob.id == job_id).first()
            if not job or job.status != "failed":
                return False
            if not str(job.error_message or "").startswith("逐页打印质量审查未通过"):
                return False
            retry_codex_skill_job(job)
            db.commit()
            return True
        finally:
            db.close()

    def _run_deterministic_repair(self, job_id: int, env: dict[str, str], log) -> None:
        db_job = self._db_job(job_id) or {}
        staging_dir = str(db_job.get("staging_dir") or (self.staging_root / f"job-{job_id}"))
        command = [
            sys.executable,
            str(BACKEND_ROOT / "scripts" / "codex_workbook_repair.py"),
            "--staging-dir",
            staging_dir,
        ]
        self._set_task(job_id, state="running", message="applying deterministic workbook repairs")
        code = self._run_command(command, env, log)
        if code != 0:
            self._write_log(log, f"deterministic workbook repair skipped after exit {code}")

    def _state_from_db(self, db_status: str) -> str:
        if db_status == "published":
            return "published"
        if db_status == "failed":
            return "failed"
        if db_status in {"running", "validating"}:
            return "running"
        if db_status == "dry_run_succeeded":
            return "queued"
        return db_status or "unknown"


class RequestHandler(BaseHTTPRequestHandler):
    controller: WorkerController

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/codex-worker/health":
            self._send_json(self.controller.health())
            return
        job_id = self._job_id(path)
        if job_id is not None:
            self._send_json(self.controller.get_status(job_id))
            return
        self._send_json({"detail": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        job_id = self._job_id(path, suffix="/run")
        if job_id is not None:
            status = self.controller.start(job_id)
            code = HTTPStatus.NOT_FOUND if status.get("state") == "missing" else HTTPStatus.ACCEPTED
            self._send_json(status, code)
            return
        self._send_json({"detail": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        return

    def _job_id(self, path: str, suffix: str = "") -> int | None:
        prefix = "/api/codex-worker/jobs/"
        if suffix and not path.endswith(suffix):
            return None
        if suffix:
            path = path[: -len(suffix)]
        if not path.startswith(prefix):
            return None
        raw = path[len(prefix):]
        if not raw.isdigit():
            return None
        return int(raw)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Host-side controller for local Codex worker execution.")
    parser.add_argument("--host", default=os.getenv("CODEX_WORKER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("CODEX_WORKER_PORT", "28082")))
    parser.add_argument("--staging-root", default=os.getenv("CODEX_WORKER_STAGING_ROOT", str(DEFAULT_STAGING_ROOT)))
    parser.add_argument("--log-root", default=os.getenv("CODEX_WORKER_LOG_ROOT", str(DEFAULT_LOG_ROOT)))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("CODEX_WORKER_TIMEOUT", "1800")))
    parser.add_argument(
        "--max-quality-retries",
        type=int,
        default=int(os.getenv("CODEX_WORKER_QUALITY_RETRIES", "0")),
    )
    parser.add_argument("--daemon", action="store_true", help="Detach and run in the background on the host.")
    parser.add_argument("--pid-file", default=os.getenv("CODEX_WORKER_PID_FILE", str(DEFAULT_LOG_ROOT / "server.pid")))
    args = parser.parse_args()

    log_root = Path(args.log_root)
    log_root.mkdir(parents=True, exist_ok=True)
    if args.daemon:
        _daemonize(log_root / "server.log", Path(args.pid_file))

    RequestHandler.controller = WorkerController(
        staging_root=Path(args.staging_root),
        log_root=log_root,
        timeout=args.timeout,
        max_quality_retries=args.max_quality_retries,
    )
    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"codex worker controller listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


def _daemonize(log_path: Path, pid_file: Path) -> None:
    if os.fork() > 0:
        os._exit(0)
    os.setsid()
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    if os.fork() > 0:
        os._exit(0)

    os.chdir(REPO_ROOT)
    os.umask(0o077)
    sys.stdin.flush()
    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, "rb", buffering=0) as stdin, open(log_path, "ab", buffering=0) as log:
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(log.fileno(), sys.stdout.fileno())
        os.dup2(log.fileno(), sys.stderr.fileno())
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
