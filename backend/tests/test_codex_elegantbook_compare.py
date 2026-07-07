import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models.base import Base
from app.models.material import Material
from app.models.review_asset import ReviewAsset
from app.utils.user_dep import get_user_id
from main import app


class FakeObject:
    def __init__(self, content: bytes):
        self.content = content

    def read(self):
        return self.content

    def stream(self, size: int):
        for offset in range(0, len(self.content), size):
            yield self.content[offset : offset + size]

    def close(self):
        return None

    def release_conn(self):
        return None


class FakeMinio:
    def __init__(self, objects: dict[tuple[str, str], bytes]):
        self.objects = objects

    def stat_object(self, bucket: str, object_name: str):
        try:
            content = self.objects[(bucket, object_name)]
        except KeyError as exc:
            raise FileNotFoundError(object_name) from exc
        return SimpleNamespace(size=len(content), content_type="")

    def get_object(self, bucket: str, object_name: str, offset: int = 0, length: int | None = None):
        try:
            content = self.objects[(bucket, object_name)]
        except KeyError as exc:
            raise FileNotFoundError(object_name) from exc
        if length is not None:
            content = content[offset : offset + length]
        elif offset:
            content = content[offset:]
        return FakeObject(content)

    def list_objects(self, bucket: str, prefix: str = "", recursive: bool = True):
        _ = recursive
        for object_bucket, object_name in sorted(self.objects):
            if object_bucket == bucket and object_name.startswith(prefix):
                yield SimpleNamespace(object_name=object_name)


def make_client(monkeypatch, objects: dict[tuple[str, str], bytes]):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    def fake_read_object(bucket: str, object_name: str) -> bytes:
        try:
            return objects[(bucket, object_name)]
        except KeyError as exc:
            raise FileNotFoundError(object_name) from exc

    def fake_object_exists(bucket: str, object_name: str) -> bool:
        return (bucket, object_name) in objects

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_user_id] = lambda: "u1"
    fake_minio = FakeMinio(objects)
    monkeypatch.setattr("app.api.review.read_object", fake_read_object)
    monkeypatch.setattr("app.api.review.object_exists", fake_object_exists)
    monkeypatch.setattr("app.api.review.minio_client", fake_minio)
    monkeypatch.setattr("app.services.codex_elegantbook.read_object", fake_read_object)
    monkeypatch.setattr("app.services.codex_elegantbook.object_exists", fake_object_exists)
    monkeypatch.setattr("app.services.codex_elegantbook.minio_client", fake_minio)

    db = testing_session()
    asset = ReviewAsset(
        user_id="u1",
        title="Demo",
        input_filename="Demo.pdf",
        review_stage="compare",
        material_id="pdf-demo",
        run_id="popo-run",
        manifest_bucket="eduassets-minerupopo",
        manifest_object="minerupopo/pdf-demo/popo-run/manifest.json",
        manifest_json=json.dumps({"material_id": "pdf-demo"}),
        review_status="pending",
    )
    db.add(asset)
    db.flush()
    material = Material(
        user_id="u1",
        material_id="pdf-demo",
        title="Demo",
        filename="Demo.pdf",
        input_bucket="eduassets-input",
        input_object="Demo.pdf",
        source_type="imported",
        stage_status="latex_done",
        pipeline_status="idle",
        popo_manifest_bucket="eduassets-minerupopo",
        popo_manifest_object="minerupopo/pdf-demo/popo-run/manifest.json",
        popo_run_id="popo-run",
        latex_manifest_bucket="eduassets-latex",
        latex_manifest_object="latex/pdf-demo/popo-run/manifest.json",
        latex_run_id="popo-run",
        review_asset_id=asset.id,
    )
    db.add(material)
    db.commit()
    asset_id = asset.id
    db.close()
    return TestClient(app), asset_id


def teardown_function():
    app.dependency_overrides.clear()


def test_compare_uses_legacy_selfloop_when_codex_output_missing(monkeypatch):
    legacy_manifest = {
        "schema": "luceon-latex-material/v1",
        "stage": "latex",
        "material_id": "pdf-demo",
        "run_id": "popo-run",
        "origin": "legacy_selfloop",
        "objects": {
            "compiled_pdf": "compiled.pdf",
            "package_zip": "latex-project.zip",
            "compile_report": "compile_report.json",
        },
    }
    objects = {
        ("eduassets-input", "Demo.pdf"): b"%PDF-source\n",
        ("eduassets-latex", "latex/pdf-demo/popo-run/manifest.json"): json.dumps(legacy_manifest).encode(),
        ("eduassets-latex", "latex/pdf-demo/popo-run/compiled.pdf"): b"%PDF-legacy\n",
        ("eduassets-latex", "latex/pdf-demo/popo-run/latex-project.zip"): b"PK-legacy",
        ("eduassets-latex", "latex/pdf-demo/popo-run/compile_report.json"): b'{"success": true}',
    }
    client, asset_id = make_client(monkeypatch, objects)

    response = client.get(f"/api/review/assets/{asset_id}/latex_compare")

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "elegantbook"
    assert body["output_origin"] == "legacy_selfloop"
    assert body["manifest"]["bucket"] == "eduassets-latex"
    assert "stage=elegantbook" in body["latex_pdf_url"]

    artifact = client.get(f"/api/review/assets/{asset_id}/artifact", params={"stage": "elegantbook", "path": "compiled.pdf"})
    assert artifact.status_code == 200
    assert artifact.content == b"%PDF-legacy\n"


def test_compare_prefers_codex_refined_elegantbook_output(monkeypatch):
    legacy_manifest = {
        "schema": "luceon-latex-material/v1",
        "stage": "latex",
        "material_id": "pdf-demo",
        "run_id": "popo-run",
        "origin": "legacy_selfloop",
        "objects": {"compiled_pdf": "compiled.pdf", "package_zip": "latex-project.zip"},
    }
    codex_manifest = {
        "schema": "luceon-codex-elegantbook/v1",
        "material_id": "pdf-demo",
        "popo_run_id": "popo-run",
        "codex_run_id": "codex-001",
        "created_at": "2026-07-07T08:00:00Z",
        "stages": [{"skill": "refine-elegantbook-latex", "status": "passed"}],
        "objects": {
            "compiled_pdf": "compiled.pdf",
            "refined_overleaf_zip": "refined-overleaf.zip",
            "compile_report": "compile_report.json",
            "latex_polish_report": "latex_polish_report.md",
        },
    }
    objects = {
        ("eduassets-input", "Demo.pdf"): b"%PDF-source\n",
        ("eduassets-latex", "latex/pdf-demo/popo-run/manifest.json"): json.dumps(legacy_manifest).encode(),
        ("eduassets-latex", "latex/pdf-demo/popo-run/compiled.pdf"): b"%PDF-legacy\n",
        ("eduassets-elegantbook", "elegantbook/pdf-demo/popo-run/codex-001/manifest.json"): json.dumps(codex_manifest).encode(),
        ("eduassets-elegantbook", "elegantbook/pdf-demo/popo-run/codex-001/compiled.pdf"): b"%PDF-codex\n",
        ("eduassets-elegantbook", "elegantbook/pdf-demo/popo-run/codex-001/refined-overleaf.zip"): b"PK-codex",
        ("eduassets-elegantbook", "elegantbook/pdf-demo/popo-run/codex-001/compile_report.json"): b'{"success": true}',
        ("eduassets-elegantbook", "elegantbook/pdf-demo/popo-run/codex-001/latex_polish_report.md"): b"# Polish\n",
    }
    client, asset_id = make_client(monkeypatch, objects)

    response = client.get(f"/api/review/assets/{asset_id}/latex_compare")

    assert response.status_code == 200
    body = response.json()
    assert body["output_origin"] == "codex_refined"
    assert body["output_run_id"] == "codex-001"
    assert body["manifest"]["bucket"] == "eduassets-elegantbook"
    assert body["download_urls"]["package_zip"].endswith("stage=elegantbook&path=refined-overleaf.zip")

    artifact = client.get(f"/api/review/assets/{asset_id}/artifact", params={"stage": "elegantbook", "path": "compiled.pdf"})
    assert artifact.status_code == 200
    assert artifact.content == b"%PDF-codex\n"


def test_internal_latex_execution_and_workspace_routes_are_gone(monkeypatch):
    objects = {
        ("eduassets-input", "Demo.pdf"): b"%PDF-source\n",
        ("eduassets-latex", "latex/pdf-demo/popo-run/manifest.json"): b'{"objects":{"compiled_pdf":"compiled.pdf"}}',
    }
    client, asset_id = make_client(monkeypatch, objects)

    assert client.post("/api/materials/1/popo2latex/preflight").status_code == 410
    assert client.post("/api/materials/1/popo2latex/start", json={"force": True}).status_code == 410
    assert client.get(f"/api/review/assets/{asset_id}/latex_workspace").status_code == 410
    assert client.get(f"/api/review/assets/{asset_id}/overleaf").status_code == 410
