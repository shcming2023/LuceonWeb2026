import io
import json
import sqlite3

from scripts.verify_backup_restore import selected_objects, sha256_file, verify_restore


class FakeMinio:
    def __init__(self, objects):
        self.objects = objects

    def get_object(self, bucket, object_name):
        return io.BytesIO(self.objects[bucket][object_name])


def test_restore_sample_prefers_nonempty_object_per_bucket():
    manifest = {
        "objects": [
            {"bucket": "input", "object": "_status/done", "size": 0},
            {"bucket": "input", "object": "large.pdf", "size": 12},
            {"bucket": "input", "object": "small.pdf", "size": 3},
            {"bucket": "markers", "object": "_status/done", "size": 0},
        ]
    }

    assert selected_objects(manifest) == [
        {"bucket": "input", "object": "small.pdf", "size": 3},
        {"bucket": "markers", "object": "_status/done", "size": 0},
    ]


def test_restore_drill_copies_and_hashes_objects_and_databases(tmp_path):
    backup = tmp_path / "backup"
    (backup / "objects/input").mkdir(parents=True)
    (backup / "objects/input/book.pdf").write_bytes(b"pdf")
    (backup / "databases").mkdir()
    database = backup / "databases/application.db"
    db = sqlite3.connect(database)
    db.execute("CREATE TABLE evidence (value TEXT)")
    db.execute("INSERT INTO evidence VALUES ('ok')")
    db.commit()
    db.close()
    manifest = {
        "job_id": "1",
        "mode": "copy",
        "truncated": False,
        "objects": [{"bucket": "input", "object": "book.pdf", "size": 3}],
        "databases": [
            {
                "name": "application",
                "file": "application.db",
                "size_bytes": database.stat().st_size,
                "sha256": sha256_file(database),
            }
        ],
    }
    (backup / "backup-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = verify_restore(backup, tmp_path / "restore", FakeMinio({"input": {"book.pdf": b"pdf"}}))

    assert report["status"] == "passed"
    assert report["restored_object_samples"][0]["sha256"]
    assert report["restored_databases"][0]["integrity_check"] == "ok"
    assert (tmp_path / "restore/restore-report.json").is_file()
