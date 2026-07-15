#!/usr/bin/env python3
import argparse
import json
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.workflow_v2.runner import run_one_stage
from app.workflow_v2.queue import consume_once, enqueue, execution_lease_active, reclaim_consumer_leases, record_worker_heartbeat
from app.workflow_v2.database import initialize_workflow_database, workflow_engine, workflow_session_factory
from app.workflow_v2.state_machine import recover_stale_stages
from app.services.runtime_health import record_runtime_worker_heartbeat


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one authorized Worker V2 stage.")
    parser.add_argument("job_id", nargs="?")
    parser.add_argument("--worker-id", default=f"manual-{socket.gethostname()}")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.loop or args.once:
        reclaimed = reclaim_consumer_leases(args.worker_id)
        if reclaimed:
            print(json.dumps({"reclaimed_consumer_leases": reclaimed}, ensure_ascii=False), flush=True)
        next_recovery_at = 0.0
        retry_delay = 1.0
        database_ready = False
        while True:
            record_worker_heartbeat(args.worker_id)
            record_runtime_worker_heartbeat("workflow_v2", args.worker_id)
            try:
                if not database_ready:
                    database = initialize_workflow_database()
                    if not database.get("ready"):
                        raise RuntimeError(f"Worker V2 database is not ready: {database.get('detail')}")
                    database_ready = True
                if time.time() >= next_recovery_at:
                    db = workflow_session_factory()()
                    try:
                        recovered = recover_stale_stages(db, active_lease_checker=execution_lease_active)
                        db.commit()
                        if recovered:
                            messages = {job_id: enqueue(job_id) for job_id in recovered}
                            print(json.dumps({"recovered_jobs": recovered, "message_ids": messages}, ensure_ascii=False), flush=True)
                    except Exception:
                        db.rollback()
                        raise
                    finally:
                        db.close()
                    next_recovery_at = time.time() + 30
                result = consume_once(consumer=args.worker_id, block_ms=1000)
                retry_delay = 1.0
            except Exception as exc:
                database_ready = False
                workflow_engine().dispose()
                print(json.dumps({"worker_loop_error": type(exc).__name__, "message": str(exc)[:1000], "retry_in_seconds": retry_delay}, ensure_ascii=False), flush=True)
                if args.once:
                    return 2
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30.0)
                continue
            if result:
                print(json.dumps(result, ensure_ascii=False), flush=True)
            if args.once:
                return 0 if not result or result.get("ok") else 2
            time.sleep(0.2)
    if not args.job_id:
        parser.error("job_id is required unless --loop or --once is used")
    result = run_one_stage(args.job_id, worker_id=args.worker_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
