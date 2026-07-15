import io
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models.base import Base
from app.models.material import Material
from app.models.user import User
from app.services import material_artifacts as subject
from main import app


class FakeMinio:
    def __init__(self, objects: dict[tuple[str, str], bytes]):
        self.objects = objects

    def stat_object(self, bucket, object_name):
        if (bucket, object_name) not in self.objects:
            raise FileNotFoundError(object_name)
        data = self.objects[(bucket, object_name)]
        return SimpleNamespace(
            size=len(data),
            content_type="application/octet-stream",
            etag=f"etag-{len(data)}",
            last_modified=None,
        )

    def list_objects(self, bucket, prefix, recursive=True):
        return [
            SimpleNamespace(object_name=object_name)
            for (row_bucket, object_name) in sorted(self.objects)
            if row_bucket == bucket and object_name.startswith(prefix)
        ]

    def get_object(self, bucket, object_name, offset=0, length=None):
        data = self.objects[(bucket, object_name)][offset:]
        if length is not None:
            data = data[:length]
        stream = io.BytesIO(data)
        stream.release_conn = lambda: None
        return stream


def material() -> Material:
    return Material(
        id=1,
        user_id="u1",
        material_id="pdf-1234567890abcdef",
        title="Book",
        filename="book.pdf",
        source_type="uploaded",
        input_bucket="eduassets-input",
        input_object="book.pdf",
        input_sha256="1" * 64,
        size_bytes=12,
        stage_status="popo_done",
        pipeline_status="idle",
        mineru_manifest_bucket="eduassets-mineru",
        mineru_manifest_object="mineru/pdf-1234567890abcdef/mineru-1/manifest.json",
        mineru_run_id="mineru-1",
        popo_manifest_bucket="eduassets-minerupopo",
        popo_manifest_object="minerupopo/pdf-1234567890abcdef/popo-2/manifest.json",
        popo_run_id="popo-2",
    )


def fake_objects() -> dict[tuple[str, str], bytes]:
    mineru_manifest = {
        "status": "mineru_done_frozen",
        "material_id": "pdf-1234567890abcdef",
        "run_id": "mineru-1",
        "archive_sha256": "a" * 64,
        "archive_size_bytes": 12,
        "stage_prefixes": {"archive": {"bucket": "eduassets-parsed", "object": "mineru.tar.gz"}},
    }
    popo_manifest = {
        "material_id": "pdf-1234567890abcdef",
        "run_id": "popo-2",
        "archive_sha256": "b" * 64,
        "archive_size_bytes": 12,
        "stage_prefixes": {"archive": {"bucket": "eduassets-parsed", "object": "popo.tar.gz"}},
    }
    return {
        ("eduassets-input", "book.pdf"): b"source-bytes",
        ("eduassets-input", "_status/pdf-1234567890abcdef/mineru-1.mineru_done_frozen.json"): b"{}",
        ("eduassets-input", "_status/pdf-1234567890abcdef/popo-2.popo_done_frozen.json"): b"{}",
        ("eduassets-mineru", "mineru/pdf-1234567890abcdef/mineru-1/manifest.json"): json.dumps(mineru_manifest).encode(),
        ("eduassets-minerupopo", "minerupopo/pdf-1234567890abcdef/popo-2/manifest.json"): json.dumps(popo_manifest).encode(),
        ("eduassets-parsed", "mineru.tar.gz"): b"mineru-bytes",
        ("eduassets-parsed", "popo.tar.gz"): b"popo--bytes!",
    }


def test_catalog_exposes_source_and_verified_stage_archives_without_paths(monkeypatch):
    objects = fake_objects()
    fake = FakeMinio(objects)
    monkeypatch.setattr(subject, "minio_client", fake)
    monkeypatch.setattr(subject, "read_object", lambda bucket, object_name: objects[(bucket, object_name)])
    monkeypatch.setattr(subject, "_candidate_records", lambda _user_id, _material: [])
    monkeypatch.setattr(subject, "_output_records", lambda _db, _user_id, _material: [])

    catalog = subject.material_artifact_catalog(SimpleNamespace(), "u1", material())
    by_id = {row["artifact_id"]: row for row in catalog["artifacts"]}

    assert set(by_id) == {
        "source",
        "mineru~mineru-1~archive",
        "mineru~mineru-1~manifest",
        "popo~popo-2~archive",
        "popo~popo-2~manifest",
    }
    assert by_id["mineru~mineru-1~archive"]["frozen"] is True
    assert by_id["popo~popo-2~archive"]["sha256"] == "b" * 64
    assert all("_ref" not in row for row in catalog["artifacts"])


def test_resolver_rejects_arbitrary_object_paths(monkeypatch):
    objects = fake_objects()
    monkeypatch.setattr(subject, "minio_client", FakeMinio(objects))
    monkeypatch.setattr(subject, "read_object", lambda bucket, object_name: objects[(bucket, object_name)])

    with pytest.raises(subject.ArtifactNotFoundError):
        subject.resolve_material_artifact(SimpleNamespace(), "u1", material(), "../../secret")


def test_single_range_supports_resume_and_rejects_multiple_ranges():
    assert subject.parse_single_range("bytes=2-5", 10) == (2, 5)
    assert subject.parse_single_range("bytes=-3", 10) == (7, 9)
    with pytest.raises(ValueError, match="单段"):
        subject.parse_single_range("bytes=0-1,4-5", 10)


def test_large_download_is_yielded_in_bounded_chunks():
    class LargeResponse:
        def __init__(self):
            self.remaining = 6 * 1024 * 1024 + 17
            self.max_requested = 0
            self.closed = False

        def read(self, size):
            self.max_requested = max(self.max_requested, size)
            if not self.remaining:
                return b""
            length = min(size, self.remaining)
            self.remaining -= length
            return b"x" * length

        def close(self):
            self.closed = True

    response = LargeResponse()
    chunks = list(subject.stream_response_body(response, chunk_size=1024 * 1024))

    assert sum(map(len, chunks)) == 6 * 1024 * 1024 + 17
    assert response.max_requested == 1024 * 1024
    assert response.closed is True


def make_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session


def test_raw_asset_catalog_fails_closed_when_auth_is_disabled(monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "true")
    monkeypatch.delenv("LUCEON_ALLOW_PUBLIC_RAW_ASSET_DOWNLOADS", raising=False)
    client, testing_session = make_client()
    try:
        db = testing_session()
        db.add(User(id=2, email="workspace@luceon.local", password_hash="disabled"))
        row = material()
        row.user_id = "2"
        db.add(row)
        db.commit()

        response = client.get("/api/materials/1/artifacts")
        assert response.status_code == 403
        assert "认证关闭" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_material_owner_filter_prevents_cross_user_catalog_access(monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "true")
    monkeypatch.setenv("LUCEON_ALLOW_PUBLIC_RAW_ASSET_DOWNLOADS", "true")
    client, testing_session = make_client()
    try:
        db = testing_session()
        db.add_all(
            [
                User(id=1, email="one@example.com", password_hash="disabled"),
                User(id=2, email="two@example.com", password_hash="disabled"),
            ]
        )
        row = material()
        row.user_id = "1"
        db.add(row)
        db.commit()

        response = client.get("/api/materials/1/artifacts", headers={"X-User-Id": "2"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
