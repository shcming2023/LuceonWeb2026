from __future__ import annotations

import json
import os
import socket
import time
import threading

from app.utils.redis_client import redis_client
from app.workflow_v2.runner import run_one_stage
from app.workflow_v2.database import workflow_engine, workflow_session_factory
from app.workflow_v2.state_machine import touch_stage_heartbeat
from app.workflow_v2.policy import POST_QA_AUTO_REPAIR_ENABLED, SIDECAR_ENABLED


STREAM = os.getenv("WORKFLOW_V2_STREAM", "luceon:workflow-v2")
GROUP = os.getenv("WORKFLOW_V2_CONSUMER_GROUP", "workflow-v2-workers")
HEARTBEAT_KEY = os.getenv("WORKFLOW_V2_HEARTBEAT_KEY", "luceon:workflow-v2:worker-heartbeat")
PENDING_CLAIM_MS = max(1_000, int(os.getenv("WORKFLOW_V2_PENDING_CLAIM_MS", "5000")))
EXECUTION_LEASE_SECONDS = max(120, int(os.getenv("WORKFLOW_V2_EXECUTION_LEASE_SECONDS", "1800")))
AUTO_RULE_REPAIR_CODES = {
    "broken_list_numbering",
    "cloze_blank_numbers_missing",
    "duplicate_image_ocr_labels",
    "figure_splits_sentence",
    "low_resolution_image_enlarged",
    "metadata_infobox_unsafe_list",
    "print_answer_space_missing",
    "qr_or_scan_prompt",
    "translation_answer_space_missing",
    "ungrouped_choice_matrix",
    "written_response_space_missing",
}
EXPECTED_PREVISUAL_CODES = {"page_review_provenance_mismatch", "full_page_visual_review_missing"}


def enqueue(public_id: str) -> str:
    if not redis_client.client:
        raise RuntimeError("Redis is unavailable")
    redis_client.create_consumer_group(STREAM, GROUP)
    message_id = redis_client.client.xadd(STREAM, {"job_id": public_id})
    return _text(message_id)


def enqueue_codex_repair(public_id: str, repair_id: int) -> str:
    if not SIDECAR_ENABLED:
        raise RuntimeError("Codex sidecar is paused while Worker V2.3 core gates converge")
    if not redis_client.client:
        raise RuntimeError("Redis is unavailable")
    redis_client.create_consumer_group(STREAM, GROUP)
    message_id = redis_client.client.xadd(
        STREAM,
        {"job_id": public_id, "kind": "codex_repair", "repair_id": str(repair_id)},
    )
    return _text(message_id)


def record_worker_heartbeat(worker_id: str) -> None:
    if not redis_client.client:
        raise RuntimeError("Redis is unavailable")
    redis_client.client.setex(HEARTBEAT_KEY, 15, json.dumps({"worker_id": worker_id, "timestamp": time.time()}))


def execution_lease_active(public_id: str) -> bool:
    return bool(redis_client.client and redis_client.client.exists(f"workflow-v2:lock:{public_id}"))


def reclaim_consumer_leases(consumer: str) -> list[str]:
    """Release leases left by a previous process using this consumer identity."""
    if not redis_client.client:
        raise RuntimeError("Redis is unavailable")
    reclaimed = []
    for raw_key in redis_client.client.scan_iter(match="workflow-v2:lock:*"):
        if _text(redis_client.client.get(raw_key)) != consumer:
            continue
        redis_client.client.delete(raw_key)
        reclaimed.append(_text(raw_key).removeprefix("workflow-v2:lock:"))
    return reclaimed


def worker_health() -> dict:
    if not redis_client.client:
        return {"available": False, "reason": "redis_unavailable"}
    raw = redis_client.client.get(HEARTBEAT_KEY)
    if not raw:
        return {"available": False, "reason": "heartbeat_missing"}
    try:
        heartbeat = json.loads(_text(raw))
    except json.JSONDecodeError:
        return {"available": False, "reason": "heartbeat_invalid"}
    age_seconds = max(0, round(time.time() - float(heartbeat.get("timestamp") or 0), 1))
    return {"available": age_seconds <= 15, "worker_id": heartbeat.get("worker_id"), "age_seconds": age_seconds}


def consume_once(*, consumer: str | None = None, block_ms: int = 1000) -> dict | None:
    if not redis_client.client:
        raise RuntimeError("Redis is unavailable")
    consumer = consumer or f"{socket.gethostname()}-{os.getpid()}"
    rows = redis_client.read_stream(STREAM, GROUP, consumer, count=1, block=block_ms)
    if not rows:
        claimed = redis_client.client.xautoclaim(STREAM, GROUP, consumer, min_idle_time=PENDING_CLAIM_MS, start_id="0-0", count=1)
        rows = claimed[1] if claimed and len(claimed) > 1 else []
    if not rows:
        return None
    message_id, fields = rows[0]
    public_id = _text(fields.get(b"job_id") or fields.get("job_id"))
    message_kind = _text(fields.get(b"kind") or fields.get("kind")) or "workflow_stage"
    repair_id = int(_text(fields.get(b"repair_id") or fields.get("repair_id")) or 0)
    lock_key = f"workflow-v2:lock:{public_id}"
    locked = redis_client.client.set(lock_key, consumer, nx=True, ex=EXECUTION_LEASE_SECONDS)
    if not locked:
        _record_queue_wait(public_id, message_id, consumer)
        return {"ok": False, "job_id": public_id, "deferred": True, "reason": "job lock is held"}
    try:
        stop = threading.Event()
        lease = threading.Thread(target=_refresh_execution_lease, args=(stop, lock_key, public_id, consumer), daemon=True)
        lease.start()
        if message_kind == "codex_repair" and not SIDECAR_ENABLED:
            result = {
                "ok": False,
                "job_id": public_id,
                "repair_id": str(repair_id),
                "kind": "codex_repair",
                "paused": True,
                "reason": "core_convergence_mode",
            }
        elif message_kind == "codex_repair":
            from app.workflow_v2.sidecar_apply import run_registered_codex_repair

            result = run_registered_codex_repair(public_id, repair_id)
        else:
            result = run_one_stage(public_id, worker_id=consumer)
        if result.get("ok") and result.get("job_status") == "queued":
            next_message_id = redis_client.client.xadd(STREAM, {"job_id": public_id})
            result["next_message_id"] = _text(next_message_id)
        elif POST_QA_AUTO_REPAIR_ENABLED and not result.get("ok") and result.get("stage") == "independent_final_review":
            auto_repair = _try_auto_rule_repair(public_id)
            result["auto_rule_repair"] = auto_repair
            if auto_repair.get("queued"):
                next_message_id = redis_client.client.xadd(STREAM, {"job_id": public_id})
                result["next_message_id"] = _text(next_message_id)
        redis_client.ack_message(STREAM, GROUP, message_id)
        return result
    finally:
        stop.set()
        if "lease" in locals():
            lease.join(timeout=2)
        if _text(redis_client.client.get(lock_key)) == consumer:
            redis_client.client.delete(lock_key)


def _refresh_execution_lease(stop: threading.Event, lock_key: str, public_id: str, worker_id: str) -> None:
    while not stop.wait(10):
        try:
            if _text(redis_client.client.get(lock_key)) != worker_id:
                return
            redis_client.client.expire(lock_key, EXECUTION_LEASE_SECONDS)
            record_worker_heartbeat(worker_id)
            db = workflow_session_factory()()
            try:
                touch_stage_heartbeat(db, public_id, worker_id)
                db.commit()
            except Exception:
                db.rollback()
                workflow_engine().dispose()
            finally:
                db.close()
        except Exception:
            workflow_engine().dispose()


def _record_queue_wait(public_id: str, message_id, consumer: str) -> None:
    from app.workflow_v2.models import StageEvent, StageRun, WorkflowJob

    db = workflow_session_factory()()
    try:
        job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).one_or_none()
        if not job:
            return
        message_id_text = _text(message_id)
        latest = (
            db.query(StageEvent)
            .filter(
                StageEvent.workflow_job_id == job.id,
                StageEvent.event_type == "queue_waiting_for_lock",
            )
            .order_by(StageEvent.id.desc())
            .first()
        )
        if latest and latest.load(latest.payload_json, {}).get("message_id") == message_id_text:
            return
        stage = (
            db.query(StageRun)
            .filter(
                StageRun.workflow_job_id == job.id,
                StageRun.stage_key == job.current_stage_key,
            )
            .order_by(StageRun.attempt.desc())
            .first()
        )
        db.add(
            StageEvent(
                workflow_job_id=job.id,
                stage_run_id=stage.id if stage else None,
                event_type="queue_waiting_for_lock",
                level="info",
                message="Queue message is waiting for the active job lease.",
                payload_json=StageEvent.dump({"message_id": message_id_text, "consumer": consumer}),
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _try_auto_rule_repair(public_id: str) -> dict:
    from app.workflow_v2.models import QaFinding, RepairAttempt, StageRun, WorkflowJob
    from app.workflow_v2.rule_repair import apply_current_rule_repairs
    from app.workflow_v2.state_machine import retry_failed_stage

    db = workflow_session_factory()()
    try:
        job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).one_or_none()
        if not job or job.status != "failed" or job.current_stage_key != "independent_final_review":
            return {"queued": False, "reason": "job_is_not_a_failed_independent_review"}
        prior_repairs = db.query(RepairAttempt).filter(
            RepairAttempt.workflow_job_id == job.id,
            RepairAttempt.repair_kind == "deterministic_rule_upgrade",
        ).count()
        if prior_repairs >= 1:
            return {"queued": False, "reason": "automatic_rule_repair_limit_reached"}
        stage = db.query(StageRun).filter(
            StageRun.workflow_job_id == job.id,
            StageRun.stage_key == "independent_final_review",
            StageRun.status == "failed",
        ).order_by(StageRun.attempt.desc()).first()
        if not stage:
            return {"queued": False, "reason": "failed_review_stage_missing"}
        blocker_codes = {
            row.code
            for row in db.query(QaFinding).filter(
                QaFinding.stage_run_id == stage.id,
                QaFinding.status == "open",
            ).all()
        }
        if not blocker_codes or not blocker_codes.issubset(AUTO_RULE_REPAIR_CODES):
            return {"queued": False, "reason": "findings_require_specialist_repair", "blockers": sorted(blocker_codes)}
        repair = apply_current_rule_repairs(db, public_id)
        remaining = set(repair.get("remaining_blockers") or []) - EXPECTED_PREVISUAL_CODES
        if remaining:
            db.commit()
            return {"queued": False, "reason": "deterministic_repair_did_not_clear_gates", "blockers": sorted(remaining), **repair}
        _, retry = retry_failed_stage(db, public_id)
        db.commit()
        return {"queued": True, "stage_attempt": retry.attempt, **repair}
    except Exception as exc:
        db.rollback()
        return {"queued": False, "reason": "automatic_rule_repair_failed", "error": str(exc)[:1000]}
    finally:
        db.close()


def _text(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value or "")
