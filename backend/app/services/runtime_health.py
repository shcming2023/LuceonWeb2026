from __future__ import annotations

import json
import time

from app.utils.redis_client import redis_client


WORKER_HEARTBEAT_TTL_SECONDS = 20
WORKER_HEARTBEAT_PREFIX = "luceon:runtime:worker"


def record_runtime_worker_heartbeat(worker_kind: str, worker_id: str) -> None:
    if not redis_client.client:
        raise RuntimeError("Redis is unavailable")
    redis_client.client.setex(
        f"{WORKER_HEARTBEAT_PREFIX}:{worker_kind}",
        WORKER_HEARTBEAT_TTL_SECONDS,
        json.dumps({"worker_id": worker_id, "timestamp": time.time()}),
    )


def runtime_worker_health(worker_kind: str) -> dict:
    if not redis_client.client:
        return {"ready": False, "reason": "redis_unavailable"}
    raw = redis_client.client.get(f"{WORKER_HEARTBEAT_PREFIX}:{worker_kind}")
    if not raw:
        return {"ready": False, "reason": "heartbeat_missing"}
    try:
        decoded = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        heartbeat = json.loads(decoded)
        age_seconds = max(0.0, round(time.time() - float(heartbeat.get("timestamp") or 0), 1))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {"ready": False, "reason": "heartbeat_invalid"}
    return {
        "ready": age_seconds <= WORKER_HEARTBEAT_TTL_SECONDS,
        "worker_id": str(heartbeat.get("worker_id") or ""),
        "age_seconds": age_seconds,
    }
