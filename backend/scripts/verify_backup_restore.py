#!/usr/bin/env python3
"""Restore deterministic samples from a filesystem backup into an isolated directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_response(response: Any) -> str:
    digest = hashlib.sha256()
    try:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            digest.update(chunk)
    finally:
        close = getattr(response, "close", None)
        if close:
            close()
        release = getattr(response, "release_conn", None)
        if release:
            release()
    return digest.hexdigest()


def selected_objects(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in manifest.get("objects", []):
        grouped[str(row["bucket"])].append(row)
    selected = []
    for _, rows in sorted(grouped.items()):
        nonempty = [row for row in rows if int(row.get("size") or 0) > 0]
        candidates = nonempty or rows
        if candidates:
            selected.append(
                min(candidates, key=lambda row: (int(row.get("size") or 0), str(row.get("object") or "")))
            )
    return selected


def verify_restore(backup_root: Path, restore_dir: Path, client: Any) -> dict[str, Any]:
    manifest = json.loads((backup_root / "backup-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("mode") != "copy" or manifest.get("truncated"):
        raise RuntimeError("restore drill requires a complete copy-mode backup")
    if restore_dir.exists():
        raise FileExistsError(f"restore directory already exists: {restore_dir}")
    restore_dir.mkdir(parents=True)

    object_results = []
    for row in selected_objects(manifest):
        source = backup_root / "objects" / row["bucket"] / row["object"]
        destination = restore_dir / "objects" / row["bucket"] / row["object"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        expected_size = int(row.get("size") or 0)
        if destination.stat().st_size != expected_size:
            raise RuntimeError(f"restored object size mismatch: {row['bucket']}/{row['object']}")
        backup_sha = sha256_file(destination)
        live_sha = sha256_response(client.get_object(row["bucket"], row["object"]))
        if backup_sha != live_sha:
            raise RuntimeError(f"restored object hash mismatch: {row['bucket']}/{row['object']}")
        object_results.append(
            {
                "bucket": row["bucket"],
                "object": row["object"],
                "size_bytes": expected_size,
                "sha256": backup_sha,
            }
        )

    database_results = []
    for row in manifest.get("databases", []):
        source = backup_root / "databases" / row["file"]
        destination = restore_dir / "databases" / row["file"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        destination.chmod(0o600)
        digest = sha256_file(destination)
        if digest != row["sha256"] or destination.stat().st_size != int(row["size_bytes"]):
            raise RuntimeError(f"restored database identity mismatch: {row['name']}")
        db = sqlite3.connect(destination)
        try:
            integrity = [str(item[0]) for item in db.execute("PRAGMA integrity_check")]
            table_count = int(
                db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            )
        finally:
            db.close()
        if integrity != ["ok"]:
            raise RuntimeError(f"restored database integrity failed: {row['name']}")
        database_results.append(
            {
                "name": row["name"],
                "size_bytes": destination.stat().st_size,
                "sha256": digest,
                "integrity_check": "ok",
                "table_count": table_count,
            }
        )

    report = {
        "schema": "luceon-backup-restore-drill/v1",
        "backup_job_id": str(manifest.get("job_id") or ""),
        "restored_object_samples": object_results,
        "restored_databases": database_results,
        "status": "passed",
    }
    (restore_dir / "restore-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--restore-dir", type=Path, required=True)
    args = parser.parse_args()
    from app.services.runtime_settings import minio_client_from_config

    report = verify_restore(args.backup_root.resolve(), args.restore_dir.resolve(), minio_client_from_config())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
