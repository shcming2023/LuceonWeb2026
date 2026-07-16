import sqlite3
from pathlib import Path

import pytest

from scripts.repair_review_asset_integrity import execute


def make_database(path: Path) -> None:
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE review_assets (
          id INTEGER PRIMARY KEY,
          user_id TEXT NOT NULL,
          title TEXT NOT NULL,
          material_id TEXT,
          run_id TEXT,
          manifest_bucket TEXT NOT NULL,
          manifest_object TEXT NOT NULL,
          review_status TEXT NOT NULL DEFAULT 'pending',
          review_note TEXT,
          created_at TEXT,
          updated_at TEXT
        );
        CREATE UNIQUE INDEX idx_review_user_manifest
          ON review_assets(user_id, manifest_bucket, manifest_object);
        CREATE TABLE materials (
          id INTEGER PRIMARY KEY, user_id TEXT, material_id TEXT,
          popo_run_id TEXT, popo_manifest_object TEXT, review_asset_id INTEGER
        );
        CREATE TABLE material_outputs (
          id INTEGER PRIMARY KEY, user_id TEXT, material_id TEXT,
          popo_run_id TEXT, review_asset_id INTEGER
        );
        CREATE TABLE codex_skill_jobs (
          id INTEGER PRIMARY KEY, user_id TEXT, material_id TEXT,
          source_popo_manifest_object TEXT, review_asset_id INTEGER
        );
        CREATE TABLE final_review_sessions (
          id INTEGER PRIMARY KEY, user_id TEXT, review_asset_id INTEGER NOT NULL
        );
        """
    )
    db.commit()
    db.close()


def test_repairs_orphans_by_exact_lineage(tmp_path):
    database = tmp_path / "app.db"
    make_database(database)
    db = sqlite3.connect(database)
    db.execute("DROP INDEX idx_review_user_manifest")
    db.execute(
        "INSERT INTO review_assets VALUES (1,'u','Book','pdf-1','popo-1','popo','path/manifest.json','pending',NULL,'2026-01-01',NULL)"
    )
    db.execute(
        "INSERT INTO review_assets VALUES (2,'u','Book','pdf-1','popo-1','popo','path/manifest.json','pending',NULL,'2026-01-02',NULL)"
    )
    db.execute("INSERT INTO materials VALUES (1,'u','pdf-1','popo-1','path/manifest.json',2)")
    db.execute("INSERT INTO material_outputs VALUES (1,'u','pdf-1','popo-1',99)")
    db.execute("INSERT INTO codex_skill_jobs VALUES (1,'u','pdf-1','path/manifest.json',2)")
    db.commit()
    db.close()

    result = execute(database, tmp_path / "backups", apply=True)

    assert result["after"]["ok"] is True
    db = sqlite3.connect(database)
    assert db.execute("SELECT GROUP_CONCAT(id) FROM review_assets").fetchone()[0] == "2"
    assert db.execute("SELECT review_asset_id FROM materials").fetchone()[0] == 2
    assert db.execute("SELECT review_asset_id FROM codex_skill_jobs").fetchone()[0] == 2
    assert db.execute("SELECT review_asset_id FROM material_outputs WHERE id=1").fetchone()[0] == 2
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_review_user_manifest'"
    ).fetchone()[0] == 1
    db.close()
    assert Path(result["backup"]).stat().st_mode & 0o777 == 0o600


def test_aborts_when_nonnullable_orphan_cannot_be_resolved(tmp_path):
    database = tmp_path / "app.db"
    make_database(database)
    db = sqlite3.connect(database)
    db.execute("INSERT INTO final_review_sessions VALUES (1,'u',999)")
    db.commit()
    db.close()

    with pytest.raises(RuntimeError, match="cannot safely repair"):
        execute(database, tmp_path / "backups", apply=True)

    db = sqlite3.connect(database)
    assert db.execute("SELECT review_asset_id FROM final_review_sessions").fetchone()[0] == 999
    db.close()


def test_aborts_when_nullable_orphan_cannot_be_resolved(tmp_path):
    database = tmp_path / "app.db"
    make_database(database)
    db = sqlite3.connect(database)
    db.execute("INSERT INTO material_outputs VALUES (1,'u','pdf-missing','popo-missing',999)")
    db.commit()
    db.close()

    with pytest.raises(RuntimeError, match="cannot safely repair"):
        execute(database, tmp_path / "backups", apply=True)

    db = sqlite3.connect(database)
    assert db.execute("SELECT review_asset_id FROM material_outputs").fetchone()[0] == 999
    db.close()


def test_aborts_instead_of_merging_conflicting_review_notes(tmp_path):
    database = tmp_path / "app.db"
    make_database(database)
    db = sqlite3.connect(database)
    db.execute("DROP INDEX idx_review_user_manifest")
    db.execute(
        "INSERT INTO review_assets VALUES (1,'u','Book','pdf-1','popo-1','popo','same','pending','note-a',NULL,NULL)"
    )
    db.execute(
        "INSERT INTO review_assets VALUES (2,'u','Book','pdf-1','popo-1','popo','same','pending','note-b',NULL,NULL)"
    )
    db.commit()
    db.close()

    with pytest.raises(RuntimeError, match="conflicting review_note"):
        execute(database, tmp_path / "backups", apply=True)

    db = sqlite3.connect(database)
    assert db.execute("SELECT COUNT(*) FROM review_assets").fetchone()[0] == 2
    db.close()
