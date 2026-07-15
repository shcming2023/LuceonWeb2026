#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.services.backup_jobs import (
    claim_next_backup_job,
    default_backup_worker_id,
    enqueue_scheduled_backup_if_due,
    execute_backup_job,
    recover_stale_backup_jobs,
)
from app.services.runtime_health import record_runtime_worker_heartbeat


def consume_once(worker_id: str) -> dict | None:
    db = SessionLocal()
    try:
        enqueue_scheduled_backup_if_due(db)
        job = claim_next_backup_job(db, worker_id)
    finally:
        db.close()
    if not job:
        return None
    return execute_backup_job(job.id, worker_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute durable Luceon backup tasks.")
    parser.add_argument("--worker-id", default=default_backup_worker_id())
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if not args.loop and not args.once:
        parser.error("--loop or --once is required")

    db = SessionLocal()
    try:
        recovered = recover_stale_backup_jobs(db)
    finally:
        db.close()
    if recovered:
        print(json.dumps({"recovered": recovered}, ensure_ascii=False), flush=True)

    retry_delay = 1.0
    while True:
        try:
            record_runtime_worker_heartbeat("backup", args.worker_id)
            result = consume_once(args.worker_id)
            retry_delay = 1.0
            if result:
                print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"backup_worker_error": type(exc).__name__, "message": str(exc)[:1000]}, ensure_ascii=False), flush=True)
            if args.once:
                return 2
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30.0)
            continue
        if args.once:
            return 0
        time.sleep(5 if not result else 0.2)


if __name__ == "__main__":
    raise SystemExit(main())
