from __future__ import annotations

import os


def _enabled(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Worker V2 is currently converging its core production gates. Targeted repair
# remains available as audited history, but it must not participate in runs.
CORE_CONVERGENCE_MODE = _enabled("WORKFLOW_V2_CORE_CONVERGENCE_MODE", True)
SIDECAR_ENABLED = _enabled("WORKFLOW_V2_SIDECAR_ENABLED", False) and not CORE_CONVERGENCE_MODE
POST_QA_AUTO_REPAIR_ENABLED = _enabled("WORKFLOW_V2_POST_QA_AUTO_REPAIR_ENABLED", False) and not CORE_CONVERGENCE_MODE


def execution_policy() -> dict[str, bool]:
    return {
        "core_convergence_mode": CORE_CONVERGENCE_MODE,
        "sidecar_enabled": SIDECAR_ENABLED,
        "post_qa_auto_repair_enabled": POST_QA_AUTO_REPAIR_ENABLED,
    }
