import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from minio import Minio


CONFIG_PATH = Path(os.getenv("LUCEON_RUNTIME_CONFIG", "/data/runtime_config.json"))
BACKUP_ROOT = Path(os.getenv("LUCEON_BACKUP_ROOT", "/backups"))
CONTRACT_BUCKETS = [
    "eduassets-input",
    "eduassets-mineru",
    "eduassets-minerupopo",
    "eduassets-raw",
    "eduassets-clean",
    "eduassets-parsed",
]
SECRET_FIELDS = {"access_key", "secret_key", "api_key", "ssh_password"}
_BACKUP_SCHEDULER_STARTED = False


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def default_runtime_config() -> dict[str, Any]:
    return {
        "minio": {
            "endpoint": os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000"),
            "public_endpoint": os.getenv("MINIO_PUBLIC_ENDPOINT", ""),
            "secure": _env_bool("MINIO_SECURE", False),
            "access_key": os.getenv("MINIO_ACCESS_KEY", ""),
            "secret_key": os.getenv("MINIO_SECRET_KEY", ""),
            "region": os.getenv("MINIO_REGION", "us-east-1"),
            "contract_buckets": list(CONTRACT_BUCKETS),
        },
        "gpu": {
            "wrapper_url": os.getenv("GPU_WRAPPER_URL", os.getenv("MINERU_API_URL", "")),
            "api_key": os.getenv("GPU_WRAPPER_API_KEY", ""),
            "ssh_host": os.getenv("GPU_SSH_HOST", ""),
            "ssh_port": int(os.getenv("GPU_SSH_PORT", "23") or "23"),
            "ssh_user": os.getenv("GPU_SSH_USER", "root"),
            "ssh_key_path": os.getenv("GPU_SSH_KEY_PATH", ""),
            "ssh_password": "",
            "service_root": os.getenv("GPU_SERVICE_ROOT", "/root/mineru-popo-service"),
        },
        "backup": {
            "enabled": False,
            "mode": "manifest",
            "schedule_enabled": False,
            "interval_hours": 24,
            "include_auxiliary": False,
            "max_objects": 50000,
            "targets": [
                {"id": "local", "label": "Local", "provider": "local", "path": str(BACKUP_ROOT / "local"), "enabled": True},
                {"id": "onedrive", "label": "OneDrive", "provider": "onedrive", "path": "", "enabled": False},
                {"id": "googledrive", "label": "Google Drive", "provider": "googledrive", "path": "", "enabled": False},
                {"id": "icloud", "label": "iCloud", "provider": "icloud", "path": "", "enabled": False},
            ],
            "last_backup": None,
        },
    }


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_runtime_config(include_secrets: bool = True) -> dict[str, Any]:
    config = default_runtime_config()
    if CONFIG_PATH.exists():
        try:
            stored = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                config = _deep_merge(config, stored)
        except json.JSONDecodeError:
            pass
    return config if include_secrets else sanitize_config(config)


def _strip_blank_secrets(incoming: Any, existing: Any) -> Any:
    if isinstance(incoming, dict):
        cleaned = {}
        for key, value in incoming.items():
            if key in SECRET_FIELDS and not str(value or "").strip():
                continue
            cleaned[key] = _strip_blank_secrets(value, existing.get(key) if isinstance(existing, dict) else None)
        return cleaned
    if isinstance(incoming, list):
        return [_strip_blank_secrets(item, {}) for item in incoming]
    return incoming


def save_runtime_config(payload: dict[str, Any]) -> dict[str, Any]:
    current = load_runtime_config(include_secrets=True)
    cleaned = _strip_blank_secrets(payload, current)
    merged = _deep_merge(current, cleaned)
    merged.get("minio", {}).pop("access_key_configured", None)
    merged.get("minio", {}).pop("secret_key_configured", None)
    merged.get("gpu", {}).pop("api_key_configured", None)
    merged.get("gpu", {}).pop("ssh_password_configured", None)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = CONFIG_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(tmp_path, 0o600)
    tmp_path.replace(CONFIG_PATH)
    return sanitize_config(merged)


def sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    safe = json.loads(json.dumps(config, ensure_ascii=False))
    minio = safe.get("minio", {})
    minio["access_key_configured"] = bool(config.get("minio", {}).get("access_key"))
    minio["secret_key_configured"] = bool(config.get("minio", {}).get("secret_key"))
    minio["access_key"] = ""
    minio["secret_key"] = ""
    gpu = safe.get("gpu", {})
    gpu["api_key_configured"] = bool(config.get("gpu", {}).get("api_key"))
    gpu["ssh_password_configured"] = bool(config.get("gpu", {}).get("ssh_password"))
    gpu["api_key"] = ""
    gpu["ssh_password"] = ""
    return safe


def _parse_minio_endpoint(endpoint: str, secure: bool) -> tuple[str, bool]:
    parsed = urlparse(endpoint)
    if parsed.scheme:
        return parsed.netloc, parsed.scheme == "https"
    return endpoint, secure


def minio_client_from_config(config: dict[str, Any] | None = None) -> Minio:
    config = config or load_runtime_config(include_secrets=True)
    minio = config.get("minio", {})
    endpoint, secure = _parse_minio_endpoint(str(minio.get("endpoint") or ""), bool(minio.get("secure")))
    return Minio(
        endpoint,
        access_key=str(minio.get("access_key") or ""),
        secret_key=str(minio.get("secret_key") or ""),
        secure=secure,
        region=str(minio.get("region") or "us-east-1"),
    )


def pipeline_env() -> dict[str, str]:
    config = load_runtime_config(include_secrets=True)
    env = os.environ.copy()
    minio = config.get("minio", {})
    gpu = config.get("gpu", {})
    if minio.get("endpoint"):
        env["MINIO_ENDPOINT"] = str(minio["endpoint"])
    if minio.get("public_endpoint"):
        env["MINIO_PUBLIC_ENDPOINT"] = str(minio["public_endpoint"])
    env["MINIO_SECURE"] = "true" if minio.get("secure") else "false"
    if minio.get("access_key"):
        env["MINIO_ACCESS_KEY"] = str(minio["access_key"])
    if minio.get("secret_key"):
        env["MINIO_SECRET_KEY"] = str(minio["secret_key"])
    if gpu.get("wrapper_url"):
        env["GPU_WRAPPER_URL"] = str(gpu["wrapper_url"])
    if gpu.get("api_key"):
        env["GPU_WRAPPER_API_KEY"] = str(gpu["api_key"])
    return env


def check_minio_contract(create_missing: bool = False) -> dict[str, Any]:
    config = load_runtime_config(include_secrets=True)
    client = minio_client_from_config(config)
    buckets = config.get("minio", {}).get("contract_buckets") or CONTRACT_BUCKETS
    rows = []
    connected = True
    error = ""
    for bucket in buckets:
        bucket_name = str(bucket)
        try:
            exists = client.bucket_exists(bucket_name)
            created = False
            if create_missing and not exists:
                client.make_bucket(bucket_name)
                exists = True
                created = True
            rows.append({"bucket": bucket_name, "exists": exists, "created": created, "role": bucket_role(bucket_name)})
        except Exception as exc:
            connected = False
            error = str(exc)
            rows.append({"bucket": bucket_name, "exists": False, "created": False, "role": bucket_role(bucket_name), "error": str(exc)})
    missing = [row["bucket"] for row in rows if not row.get("exists")]
    return {
        "connected": connected,
        "endpoint": sanitize_config(config).get("minio", {}).get("endpoint"),
        "buckets": rows,
        "missing": missing,
        "contract_ok": connected and not missing,
        "error": error,
    }


def bucket_role(bucket: str) -> str:
    return {
        "eduassets-input": "source_pdf",
        "eduassets-mineru": "mineru_official",
        "eduassets-minerupopo": "popo_official",
        "eduassets-raw": "raw_master",
        "eduassets-clean": "clean_candidate",
        "eduassets-parsed": "archive_optional",
    }.get(bucket, "unknown")


def check_gpu_runtime() -> dict[str, Any]:
    config = load_runtime_config(include_secrets=True)
    gpu = config.get("gpu", {})
    wrapper_url = str(gpu.get("wrapper_url") or "").rstrip("/")
    result: dict[str, Any] = {
        "wrapper_url": wrapper_url,
        "wrapper_ok": False,
        "staged_api_ok": False,
        "ssh_ok": False,
        "ssh_status": "skipped",
        "health": {},
        "staged_api": {},
        "errors": [],
    }
    headers = {"Authorization": "Bearer " + str(gpu.get("api_key"))} if gpu.get("api_key") else {}
    if wrapper_url:
        try:
            health = httpx.get(f"{wrapper_url}/api/v1/health", timeout=5)
            result["health"] = {"status_code": health.status_code, "body": _safe_json(health)}
            result["wrapper_ok"] = health.status_code == 200
        except Exception as exc:
            result["errors"].append(f"wrapper health: {exc}")
        paths = {
            "mineru_batches": "/api/v1/mineru/batches",
            "mineru_results_probe": "/api/v1/mineru/results/__probe__",
            "popo_batches": "/api/v1/popo/batches",
            "popo_results_probe": "/api/v1/popo/results/__probe__",
        }
        codes = {}
        for name, path in paths.items():
            try:
                resp = httpx.get(f"{wrapper_url}{path}", headers=headers, timeout=5)
                codes[name] = resp.status_code
            except Exception as exc:
                codes[name] = None
                result["errors"].append(f"{name}: {exc}")
        result["staged_api"] = codes
        result["staged_api_ok"] = (
            codes.get("mineru_batches") in (200, 405)
            and codes.get("popo_batches") in (200, 405)
            and codes.get("mineru_results_probe") in (200, 404)
            and codes.get("popo_results_probe") in (200, 404)
        )
    else:
        result["errors"].append("wrapper_url is empty")
    ssh_host = str(gpu.get("ssh_host") or "")
    ssh_user = str(gpu.get("ssh_user") or "root")
    ssh_port = str(gpu.get("ssh_port") or "22")
    ssh_key_path = str(gpu.get("ssh_key_path") or "")
    if ssh_host and ssh_key_path:
        command = [
            "ssh",
            "-p",
            ssh_port,
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=5",
            "-i",
            os.path.expanduser(ssh_key_path),
            f"{ssh_user}@{ssh_host}",
            "echo ok",
        ]
        try:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=10)
            result["ssh_ok"] = completed.returncode == 0 and "ok" in completed.stdout
            result["ssh_status"] = "ok" if result["ssh_ok"] else "failed"
            if not result["ssh_ok"]:
                result["errors"].append("ssh key check failed")
        except Exception as exc:
            result["ssh_status"] = "failed"
            result["errors"].append(f"ssh: {exc}")
    elif ssh_host and gpu.get("ssh_password"):
        result["ssh_status"] = "password_configured_not_tested"
    return result


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text[:500]


def check_backup_targets() -> dict[str, Any]:
    config = load_runtime_config(include_secrets=True)
    targets = []
    for target in config.get("backup", {}).get("targets", []):
        row = dict(target)
        path = Path(str(row.get("path") or ""))
        enabled = bool(row.get("enabled"))
        row["exists"] = path.exists() if row.get("path") else False
        row["writable"] = _is_writable(path) if enabled and row.get("path") else False
        row["status"] = "ready" if enabled and row["writable"] else "disabled" if not enabled else "unavailable"
        targets.append(row)
    return {"targets": targets, "ready_count": sum(1 for item in targets if item["status"] == "ready")}


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".luceon-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def classify_object(bucket: str, object_name: str) -> str:
    if bucket == "eduassets-input" and object_name.lower().endswith(".pdf"):
        return "official"
    if bucket == "eduassets-input" and object_name.startswith("_status/"):
        return "status_marker"
    if bucket == "eduassets-mineru" and object_name.startswith("mineru/"):
        return "official"
    if bucket == "eduassets-minerupopo" and object_name.startswith("minerupopo/"):
        return "official"
    if bucket == "eduassets-raw" and object_name.startswith("raw/"):
        return "official"
    if bucket == "eduassets-clean" and object_name.startswith("clean/"):
        return "official"
    if object_name.endswith("manifest.json"):
        return "manifest"
    return "auxiliary"


def run_manual_backup() -> dict[str, Any]:
    config = load_runtime_config(include_secrets=True)
    backup_cfg = config.get("backup", {})
    client = minio_client_from_config(config)
    mode = str(backup_cfg.get("mode") or "manifest")
    include_auxiliary = bool(backup_cfg.get("include_auxiliary"))
    max_objects = int(backup_cfg.get("max_objects") or 50000)
    buckets = config.get("minio", {}).get("contract_buckets") or CONTRACT_BUCKETS
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    objects: list[dict[str, Any]] = []
    truncated = False
    for bucket in buckets:
        try:
            if not client.bucket_exists(bucket):
                continue
            for item in client.list_objects(bucket, recursive=True):
                object_name = str(getattr(item, "object_name", "") or "")
                classification = classify_object(bucket, object_name)
                if classification == "auxiliary" and not include_auxiliary:
                    continue
                objects.append(
                    {
                        "bucket": bucket,
                        "object": object_name,
                        "size": int(getattr(item, "size", 0) or 0),
                        "etag": str(getattr(item, "etag", "") or ""),
                        "classification": classification,
                    }
                )
                if len(objects) >= max_objects:
                    truncated = True
                    break
        except Exception as exc:
            objects.append({"bucket": bucket, "object": "", "classification": "error", "error": str(exc)})
        if truncated:
            break
    targets = [row for row in backup_cfg.get("targets", []) if row.get("enabled") and row.get("path")]
    written_targets = []
    for target in targets:
        root = Path(str(target["path"])) / f"luceon-backup-{stamp}"
        root.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": "luceon-backup-manifest/v1",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "mode": mode,
            "truncated": truncated,
            "object_count": len(objects),
            "objects": objects,
        }
        (root / "backup-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        copied = 0
        if mode == "copy":
            for obj in objects:
                if obj.get("classification") == "error" or not obj.get("object"):
                    continue
                dest = root / "objects" / obj["bucket"] / str(obj["object"])
                dest.parent.mkdir(parents=True, exist_ok=True)
                response = client.get_object(obj["bucket"], obj["object"])
                try:
                    with dest.open("wb") as fh:
                        shutil.copyfileobj(response, fh)
                    copied += 1
                finally:
                    close = getattr(response, "close", None)
                    if close:
                        close()
                    release_conn = getattr(response, "release_conn", None)
                    if release_conn:
                        release_conn()
        written_targets.append({"id": target.get("id"), "path": str(root), "manifest": str(root / "backup-manifest.json"), "copied": copied})
    config["backup"]["last_backup"] = {"created_at": datetime.utcnow().isoformat() + "Z", "object_count": len(objects), "targets": written_targets}
    save_runtime_config(config)
    return {"mode": mode, "object_count": len(objects), "truncated": truncated, "targets": written_targets}


def start_backup_scheduler() -> None:
    global _BACKUP_SCHEDULER_STARTED
    if _BACKUP_SCHEDULER_STARTED:
        return
    _BACKUP_SCHEDULER_STARTED = True
    thread = threading.Thread(target=_backup_scheduler_loop, daemon=True)
    thread.start()


def _backup_scheduler_loop() -> None:
    while True:
        try:
            config = load_runtime_config(include_secrets=True)
            backup_cfg = config.get("backup", {})
            if backup_cfg.get("enabled") and backup_cfg.get("schedule_enabled") and _backup_due(backup_cfg):
                run_manual_backup()
        except Exception:
            pass
        time.sleep(300)


def _backup_due(backup_cfg: dict[str, Any]) -> bool:
    interval_seconds = max(1, int(backup_cfg.get("interval_hours") or 24)) * 3600
    last_backup = backup_cfg.get("last_backup") if isinstance(backup_cfg.get("last_backup"), dict) else {}
    created_at = str(last_backup.get("created_at") or "")
    if not created_at:
        return True
    try:
        last = datetime.fromisoformat(created_at.rstrip("Z"))
    except ValueError:
        return True
    return (datetime.utcnow() - last).total_seconds() >= interval_seconds


def runtime_status() -> dict[str, Any]:
    minio = check_minio_contract(create_missing=False)
    gpu = check_gpu_runtime()
    backup = check_backup_targets()
    blockers = []
    warnings = []
    if not minio.get("contract_ok"):
        blockers.append("minio_contract")
    if not gpu.get("wrapper_ok"):
        warnings.append("gpu_wrapper")
    if backup.get("ready_count", 0) <= 0:
        warnings.append("backup_target")
    status = "blocked" if blockers else "warning" if warnings else "ready"
    return {"status": status, "blockers": blockers, "warnings": warnings, "minio": minio, "gpu": gpu, "backup": backup}
