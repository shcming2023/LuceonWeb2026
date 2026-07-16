#!/usr/bin/env python3
"""Safely consolidate duplicate review assets and repair their references."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REFERENCE_TABLES = (
    "materials",
    "material_outputs",
    "codex_skill_jobs",
    "final_review_sessions",
)
IDENTITY_COLUMNS = {"id", "user_id", "manifest_bucket", "manifest_object"}
TIMESTAMP_COLUMNS = {"created_at", "updated_at"}


def table_columns(db: sqlite3.Connection, table: str) -> dict[str, sqlite3.Row]:
    return {row["name"]: row for row in db.execute(f'PRAGMA table_info("{table}")')}


def table_exists(db: sqlite3.Connection, table: str) -> bool:
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def reference_tables(db: sqlite3.Connection) -> list[str]:
    return [
        table
        for table in REFERENCE_TABLES
        if table_exists(db, table) and "review_asset_id" in table_columns(db, table)
    ]


def review_asset_indexes(db: sqlite3.Connection) -> list[tuple[str, str]]:
    rows = db.execute(
        """
        SELECT name, sql FROM sqlite_master
        WHERE type='index' AND tbl_name='review_assets' AND sql IS NOT NULL
        ORDER BY name
        """
    ).fetchall()
    definitions = [(str(row[0]), str(row[1])) for row in rows]
    if not any(name == "idx_review_user_manifest" for name, _ in definitions):
        definitions.append(
            (
                "idx_review_user_manifest",
                "CREATE UNIQUE INDEX idx_review_user_manifest "
                "ON review_assets (user_id, manifest_bucket, manifest_object)",
            )
        )
    return definitions


def drop_review_asset_indexes(db: sqlite3.Connection, definitions: list[tuple[str, str]]) -> None:
    for name, _ in definitions:
        db.execute(f'DROP INDEX IF EXISTS "{name}"')


def recreate_review_asset_indexes(db: sqlite3.Connection, definitions: list[tuple[str, str]]) -> None:
    for _, statement in definitions:
        db.execute(statement)


def reference_count(db: sqlite3.Connection, asset_id: int, tables: list[str]) -> int:
    return sum(
        int(
            db.execute(
                f'SELECT COUNT(*) FROM "{table}" NOT INDEXED WHERE review_asset_id=?',
                (asset_id,),
            ).fetchone()[0]
        )
        for table in tables
    )


def duplicate_groups(db: sqlite3.Connection) -> list[list[sqlite3.Row]]:
    groups = db.execute(
        """
        SELECT user_id, manifest_bucket, manifest_object
        FROM review_assets NOT INDEXED
        GROUP BY user_id, manifest_bucket, manifest_object
        HAVING COUNT(*) > 1
        ORDER BY user_id, manifest_bucket, manifest_object
        """
    ).fetchall()
    return [
        db.execute(
            """
            SELECT * FROM review_assets NOT INDEXED
            WHERE user_id=? AND manifest_bucket=? AND manifest_object=?
            ORDER BY id
            """,
            tuple(group),
        ).fetchall()
        for group in groups
    ]


def empty(value: Any) -> bool:
    return value is None or value == ""


def merged_values(rows: list[sqlite3.Row], canonical_id: int) -> dict[str, Any]:
    canonical = next(row for row in rows if int(row["id"]) == canonical_id)
    merged = dict(canonical)
    for column in canonical.keys():
        if column in IDENTITY_COLUMNS:
            continue
        values = [row[column] for row in rows if not empty(row[column])]
        if not values:
            continue
        if column == "created_at":
            merged[column] = min(values)
            continue
        if column == "updated_at":
            merged[column] = max(values)
            continue
        distinct = {str(value) for value in values}
        if len(distinct) > 1:
            raise RuntimeError(
                f"duplicate review assets have conflicting {column}: "
                f"ids={','.join(str(row['id']) for row in rows)}"
            )
        merged[column] = values[0]
    return merged


def consolidate_duplicates(db: sqlite3.Connection, tables: list[str]) -> list[dict[str, Any]]:
    actions = []
    for rows in duplicate_groups(db):
        ranked = sorted(
            rows,
            key=lambda row: (-reference_count(db, int(row["id"]), tables), int(row["id"])),
        )
        canonical_id = int(ranked[0]["id"])
        duplicate_ids = [int(row["id"]) for row in rows if int(row["id"]) != canonical_id]
        merged = merged_values(rows, canonical_id)
        assignments = []
        values = []
        for column, value in merged.items():
            if column in IDENTITY_COLUMNS:
                continue
            assignments.append(f'"{column}"=?')
            values.append(value)
        if assignments:
            db.execute(
                f'UPDATE review_assets SET {", ".join(assignments)} WHERE id=?',
                (*values, canonical_id),
            )
        redirected = defaultdict(int)
        for duplicate_id in duplicate_ids:
            for table in tables:
                cursor = db.execute(
                    f'UPDATE "{table}" NOT INDEXED SET review_asset_id=? WHERE review_asset_id=?',
                    (canonical_id, duplicate_id),
                )
                redirected[table] += int(cursor.rowcount or 0)
            db.execute("DELETE FROM review_assets WHERE id=?", (duplicate_id,))
        actions.append(
            {
                "canonical_id": canonical_id,
                "removed_ids": duplicate_ids,
                "redirected": dict(redirected),
                "manifest": f"{ranked[0]['manifest_bucket']}/{ranked[0]['manifest_object']}",
            }
        )
    return actions


def orphan_rows(db: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    return db.execute(
        f"""
        SELECT source.*
        FROM "{table}" AS source
        LEFT JOIN review_assets AS asset NOT INDEXED ON asset.id=source.review_asset_id
        WHERE source.review_asset_id IS NOT NULL AND asset.id IS NULL
        ORDER BY source.id
        """
    ).fetchall()


def orphan_candidates(db: sqlite3.Connection, table: str, row: sqlite3.Row) -> list[int]:
    columns = set(row.keys())
    user_id = row["user_id"] if "user_id" in columns else None
    material_id = row["material_id"] if "material_id" in columns else None
    manifest_object = None
    for name in ("source_popo_manifest_object", "popo_manifest_object"):
        if name in columns and row[name]:
            manifest_object = row[name]
            break
    if user_id is not None and manifest_object:
        return [
            int(candidate[0])
            for candidate in db.execute(
                """
                SELECT id FROM review_assets NOT INDEXED
                WHERE user_id=? AND manifest_object=?
                ORDER BY id
                """,
                (str(user_id), str(manifest_object)),
            )
        ]
    popo_run_id = row["popo_run_id"] if "popo_run_id" in columns else None
    if user_id is not None and material_id and popo_run_id:
        return [
            int(candidate[0])
            for candidate in db.execute(
                """
                SELECT id FROM review_assets NOT INDEXED
                WHERE user_id=? AND material_id=? AND run_id=?
                ORDER BY id
                """,
                (str(user_id), str(material_id), str(popo_run_id)),
            )
        ]
    return []


def repair_orphans(db: sqlite3.Connection, tables: list[str]) -> list[dict[str, Any]]:
    actions = []
    for table in tables:
        for row in orphan_rows(db, table):
            candidates = orphan_candidates(db, table, row)
            if len(candidates) == 1:
                replacement = candidates[0]
                action = "redirected"
            else:
                raise RuntimeError(
                    f"cannot safely repair {table}.id={row['id']} "
                    f"review_asset_id={row['review_asset_id']} candidates={candidates}"
                )
            db.execute(
                f'UPDATE "{table}" SET review_asset_id=? WHERE id=?',
                (replacement, row["id"]),
            )
            actions.append(
                {
                    "table": table,
                    "row_id": int(row["id"]),
                    "old_review_asset_id": int(row["review_asset_id"]),
                    "new_review_asset_id": replacement,
                    "action": action,
                }
            )
    return actions


def checks(db: sqlite3.Connection, tables: list[str]) -> dict[str, Any]:
    integrity = [row[0] for row in db.execute("PRAGMA integrity_check")]
    foreign_keys = [tuple(row) for row in db.execute("PRAGMA foreign_key_check")]
    duplicates = sum(len(group) - 1 for group in duplicate_groups(db))
    orphans = {table: len(orphan_rows(db, table)) for table in tables}
    return {
        "integrity": integrity,
        "foreign_key_errors": foreign_keys,
        "duplicate_rows": duplicates,
        "orphan_references": orphans,
        "ok": integrity == ["ok"] and not foreign_keys and duplicates == 0 and not any(orphans.values()),
    }


def backup_database(database: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"{database.stem}-pre-review-integrity-{stamp}{database.suffix}"
    source = sqlite3.connect(database)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    destination.chmod(0o600)
    return destination


def execute(database: Path, backup_dir: Path, apply: bool) -> dict[str, Any]:
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    tables = reference_tables(db)
    before = checks(db, tables)
    result: dict[str, Any] = {"database": str(database), "apply": apply, "before": before}
    if not apply:
        result["duplicate_groups"] = [
            [int(row["id"]) for row in group] for group in duplicate_groups(db)
        ]
        result["orphans"] = {
            table: [int(row["id"]) for row in orphan_rows(db, table)] for table in tables
        }
        db.close()
        return result

    db.close()
    backup = backup_database(database, backup_dir)
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("BEGIN IMMEDIATE")
        index_definitions = review_asset_indexes(db)
        drop_review_asset_indexes(db, index_definitions)
        duplicate_actions = consolidate_duplicates(db, tables)
        orphan_actions = repair_orphans(db, tables)
        recreate_review_asset_indexes(db, index_definitions)
        db.execute("REINDEX")
        after = checks(db, tables)
        if not after["ok"]:
            raise RuntimeError(f"post-repair checks failed: {after}")
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        Path(f"{database}-wal").unlink(missing_ok=True)
        Path(f"{database}-shm").unlink(missing_ok=True)
        shutil.copy2(backup, database)
        raise
    db.close()
    result.update(
        {
            "backup": str(backup),
            "duplicates": duplicate_actions,
            "orphans": orphan_actions,
            "after": after,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = execute(args.database.resolve(), args.backup_dir.resolve(), args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("after", result["before"]).get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
