from __future__ import annotations

import os


def _enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def v1_batch_enabled() -> bool:
    return _enabled("LUCEON_WORKER_V1_BATCH_ENABLED", False)


def v1_auto_retry_enabled() -> bool:
    return _enabled("LUCEON_WORKER_V1_AUTO_RETRY_ENABLED", False)


def v1_policy() -> dict[str, bool | str]:
    return {
        "mode": "audit_only",
        "batch_enabled": v1_batch_enabled(),
        "auto_retry_enabled": v1_auto_retry_enabled(),
        "single_job_audit_enabled": True,
    }
