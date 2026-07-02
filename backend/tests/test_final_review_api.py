import json

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

    def close(self):
        return None

    def release_conn(self):
        return None


class FakeMinio:
    def __init__(self):
        self.buckets = {"std", "clean", "raw"}
        self.objects = {
            ("std", "standard/m1/std1/manifest.json"): b'{"objects":{"standard_document_json":"standard_document.json","standard_md":"standard.md","standard_html":"standard.html"}}',
            ("std", "standard/m1/std1/standard_document.json"): b'{"blocks":[{"id":"b1","markdown":"# Unit 1","heading_path":["Unit 1"]}]}',
            ("std", "standard/m1/std1/standard.md"): b"# Unit 1\n\n$ x^2 $",
            ("std", "standard/m1/std1/standard.html"): b"<html><body><h1 id='b1'>Unit 1</h1></body></html>",
            ("clean", "clean/m1/clean1/manifest.json"): b"{}",
            ("clean", "clean/m1/clean1/clean.md"): b"# Unit 1\n\n$ x^2 $",
            ("raw", "raw/m1/raw1/manifest.json"): b"{}",
            ("raw", "raw/m1/raw1/clean.md"): b"# Unit 1\n\n$ x^2 $",
        }
        self.puts = {}

    def stat_object(self, bucket, object_name):
        if (bucket, object_name) not in self.objects and (bucket, object_name) not in self.puts:
            raise FileNotFoundError(object_name)

    def get_object(self, bucket, object_name, *args, **kwargs):
        if (bucket, object_name) in self.objects:
            return FakeObject(self.objects[(bucket, object_name)])
        if (bucket, object_name) in self.puts:
            return FakeObject(self.puts[(bucket, object_name)]["content"])
        raise FileNotFoundError(object_name)

    def bucket_exists(self, bucket):
        return bucket in self.buckets

    def make_bucket(self, bucket):
        self.buckets.add(bucket)

    def put_object(self, bucket, object_name, data, length, content_type=None):
        self.buckets.add(bucket)
        self.puts[(bucket, object_name)] = {
            "content": data.read(),
            "content_type": content_type,
        }


def make_client(monkeypatch):
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
    app.dependency_overrides[get_user_id] = lambda: "u1"
    fake_minio = FakeMinio()
    monkeypatch.setattr("app.services.final_review.minio_client", fake_minio)
    monkeypatch.setattr("app.services.luceon_review.minio_client", fake_minio)

    db = testing_session()
    asset = ReviewAsset(
        user_id="u1",
        title="Test Book",
        input_filename="test.pdf",
        review_stage="parse",
        material_id="m1",
        run_id="popo1",
        manifest_bucket="popo",
        manifest_object="minerupopo/m1/popo1/manifest.json",
        manifest_json=json.dumps({"material_id": "m1"}),
        review_status="pending",
    )
    missing_standard_asset = ReviewAsset(
        user_id="u1",
        title="No Standard",
        input_filename="no-standard.pdf",
        review_stage="parse",
        material_id="m2",
        run_id="popo2",
        manifest_bucket="popo",
        manifest_object="minerupopo/m2/popo2/manifest.json",
        manifest_json=json.dumps({"material_id": "m2"}),
        review_status="pending",
    )
    db.add_all([asset, missing_standard_asset])
    db.flush()
    db.add_all(
        [
            Material(
                user_id="u1",
                material_id="m1",
                title="Test Book",
                filename="test.pdf",
                source_type="imported",
                stage_status="standard_done",
                pipeline_status="idle",
                raw_manifest_bucket="raw",
                raw_manifest_object="raw/m1/raw1/manifest.json",
                raw_run_id="raw1",
                clean_manifest_bucket="clean",
                clean_manifest_object="clean/m1/clean1/manifest.json",
                clean_run_id="clean1",
                standard_manifest_bucket="std",
                standard_manifest_object="standard/m1/std1/manifest.json",
                standard_run_id="std1",
                standard_quality_score=86,
                review_asset_id=asset.id,
            ),
            Material(
                user_id="u1",
                material_id="m2",
                title="No Standard",
                filename="no-standard.pdf",
                source_type="imported",
                stage_status="clean_done",
                pipeline_status="idle",
                review_asset_id=missing_standard_asset.id,
            ),
        ]
    )
    db.commit()
    asset_id = str(asset.id)
    missing_standard_asset_id = str(missing_standard_asset.id)
    db.close()
    return TestClient(app), fake_minio, asset_id, missing_standard_asset_id


def teardown_module():
    app.dependency_overrides.clear()


def test_final_review_requires_standard_asset(monkeypatch):
    client, _fake_minio, _asset_id, missing_standard_asset_id = make_client(monkeypatch)

    response = client.post("/api/review/final/sessions", json={"asset_id": int(missing_standard_asset_id)})

    assert response.status_code == 400
    assert "Standard" in response.json()["detail"]
    app.dependency_overrides.clear()


def test_final_review_annotation_verify_decision_and_export(monkeypatch):
    client, fake_minio, asset_id, _missing_standard_asset_id = make_client(monkeypatch)

    session_response = client.post("/api/review/final/sessions", json={"asset_id": int(asset_id)})
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]

    draft_response = client.post(
        f"/api/review/final/sessions/{session_id}/annotations",
        json={
            "issue_type": "formula_broken",
            "severity": "major",
            "status": "draft",
            "human_note": "公式没有渲染",
            "anchors": {"standard_block_id": "b1", "pdf_page": 3, "heading_path": ["Unit 1"]},
        },
    )
    assert draft_response.status_code == 200
    draft_id = draft_response.json()["id"]
    assert client.delete(f"/api/review/final/annotations/{draft_id}").status_code == 200

    annotation_response = client.post(
        f"/api/review/final/sessions/{session_id}/annotations",
        json={
            "issue_type": "formula_broken",
            "severity": "major",
            "status": "submitted",
            "human_note": "公式没有渲染",
            "anchors": {"standard_block_id": "b1", "pdf_page": 3, "heading_path": ["Unit 1"]},
        },
    )
    annotation_id = annotation_response.json()["id"]
    assert client.delete(f"/api/review/final/annotations/{annotation_id}").status_code == 400

    verify_response = client.post(f"/api/review/final/annotations/{annotation_id}/verify")
    assert verify_response.status_code == 200
    assert verify_response.json()["verification"]["root_cause_stage"] == "standard_rendering"
    assert verify_response.json()["verification"]["root_cause_label"] == "math_rendering"

    decision_response = client.patch(
        f"/api/review/final/annotations/{annotation_id}/decision",
        json={"decision": "rerun_standard", "reviewer_note": "重跑 Standard"},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["annotation"]["status"] == "fix_proposed"

    export_response = client.get(f"/api/review/final/sessions/{session_id}/export")
    assert export_response.status_code == 200
    objects = export_response.json()["archive"]["objects"]
    assert set(objects) == {
        "final_review_ledger.jsonl",
        "root_cause_report.json",
        "project_decisions.jsonl",
        "review_summary.json",
    }
    ledger_ref = objects["final_review_ledger.jsonl"]
    assert (ledger_ref["bucket"], ledger_ref["object"]) in fake_minio.puts
    app.dependency_overrides.clear()


def test_final_review_open_feedback_is_classified(monkeypatch):
    client, _fake_minio, asset_id, _missing_standard_asset_id = make_client(monkeypatch)

    session_response = client.post("/api/review/final/sessions", json={"asset_id": int(asset_id)})
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]

    annotation_response = client.post(
        f"/api/review/final/sessions/{session_id}/annotations",
        json={
            "issue_type": "needs_ai_check",
            "severity": "major",
            "status": "submitted",
            "human_note": "Main Idea 和 Detail 是题目的分类，和题目有关联关系，排版处理有问题。",
            "anchors": {"standard_block_id": "b1", "pdf_page": 3, "heading_path": ["Unit 1"]},
        },
    )
    assert annotation_response.status_code == 200
    annotation_id = annotation_response.json()["id"]

    verify_response = client.post(f"/api/review/final/annotations/{annotation_id}/verify")
    assert verify_response.status_code == 200
    verification = verify_response.json()["verification"]
    assert verification["root_cause_stage"] == "standard_grouping"
    assert verification["root_cause_label"] == "block_assignment"
    assert verification["proposed_action"]["target_stage"] == "standard"

    layout_response = client.post(
        f"/api/review/final/sessions/{session_id}/annotations",
        json={
            "issue_type": "needs_ai_check",
            "severity": "major",
            "status": "submitted",
            "human_note": "正文不需要分栏，当前布局处理有问题。",
            "anchors": {"standard_block_id": "b2", "pdf_page": 4, "heading_path": ["Unit 1"]},
        },
    )
    assert layout_response.status_code == 200
    layout_id = layout_response.json()["id"]
    layout_verify_response = client.post(f"/api/review/final/annotations/{layout_id}/verify")
    assert layout_verify_response.status_code == 200
    layout_verification = layout_verify_response.json()["verification"]
    assert layout_verification["root_cause_stage"] == "standard_layout"
    assert layout_verification["proposed_action"]["target_stage"] == "standard"

    noise_response = client.post(
        f"/api/review/final/sessions/{session_id}/annotations",
        json={
            "issue_type": "needs_ai_check",
            "severity": "major",
            "status": "submitted",
            "human_note": "这不是正文内容，不需要。Vocabulary Building 1 等目录文字不应进入正文。",
            "anchors": {"standard_block_id": "b3", "pdf_page": 2, "heading_path": ["Unit 1"]},
        },
    )
    assert noise_response.status_code == 200
    noise_id = noise_response.json()["id"]
    noise_verify_response = client.post(f"/api/review/final/annotations/{noise_id}/verify")
    assert noise_verify_response.status_code == 200
    noise_verification = noise_verify_response.json()["verification"]
    assert noise_verification["root_cause_stage"] == "clean_overclean"
    assert noise_verification["proposed_action"]["target_stage"] == "clean"

    app.dependency_overrides.clear()
