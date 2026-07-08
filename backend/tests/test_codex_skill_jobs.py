from fastapi.testclient import TestClient
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models.base import Base
from app.models.material import Material, MaterialOutput
from app.services.codex_skill_jobs import create_codex_skill_job, publish_staging_job, run_dry_run_job
from app.utils.user_dep import get_user_id
from main import app


class FakeMinio:
    def __init__(self):
        self.objects = {}
        self.buckets = set()

    def bucket_exists(self, bucket: str):
        return bucket in self.buckets

    def make_bucket(self, bucket: str):
        self.buckets.add(bucket)

    def put_object(self, bucket: str, object_name: str, data, length: int, content_type: str = ""):
        self.buckets.add(bucket)
        self.objects[(bucket, object_name)] = {"content": data.read(length), "content_type": content_type}


def make_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

    db = testing_session()
    material = Material(
        user_id="u1",
        material_id="pdf-demo",
        title="Demo",
        filename="Demo.pdf",
        input_bucket="eduassets-input",
        input_object="Demo.pdf",
        source_type="imported",
        stage_status="popo_done",
        pipeline_status="idle",
        popo_manifest_bucket="eduassets-minerupopo",
        popo_manifest_object="minerupopo/pdf-demo/popo-run/manifest.json",
        popo_run_id="popo-run",
        latex_manifest_bucket="eduassets-latex",
        latex_manifest_object="latex/pdf-demo/popo-run/manifest.json",
    )
    db.add(material)
    db.commit()
    material_id = material.id
    db.close()
    return TestClient(app), material_id


def make_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session()
    material = Material(
        user_id="u1",
        material_id="pdf-demo",
        title="Demo",
        filename="Demo.pdf",
        input_bucket="eduassets-input",
        input_object="Demo.pdf",
        source_type="imported",
        stage_status="popo_done",
        pipeline_status="idle",
        popo_manifest_bucket="eduassets-minerupopo",
        popo_manifest_object="minerupopo/pdf-demo/popo-run/manifest.json",
        popo_run_id="popo-run",
        latex_manifest_bucket="eduassets-latex",
        latex_manifest_object="latex/pdf-demo/popo-run/manifest.json",
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return db, material


def teardown_function():
    app.dependency_overrides.clear()


def test_codex_skill_job_create_is_idempotent_and_lists():
    client, material_id = make_client()

    first = client.post(f"/api/materials/{material_id}/codex-jobs", json={"mode": "refresh_legacy"})
    assert first.status_code == 200
    body = first.json()
    assert body["status"] == "queued"
    assert body["mode"] == "refresh_legacy"
    assert body["source_popo_manifest"]["bucket"] == "eduassets-minerupopo"

    second = client.post(f"/api/materials/{material_id}/codex-jobs", json={"mode": "refresh_legacy"})
    assert second.status_code == 200
    assert second.json()["id"] == body["id"]

    listed = client.get(f"/api/materials/{material_id}/codex-jobs")
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()["jobs"]] == [body["id"]]


def test_codex_skill_job_force_new_version_records_run_reason():
    client, material_id = make_client()

    first = client.post(
        f"/api/materials/{material_id}/codex-jobs",
        json={"mode": "refresh_legacy", "skill_version": "refine-v2", "run_reason": "manual_refresh"},
    )
    assert first.status_code == 200
    body = first.json()
    assert body["payload"]["run_reason"] == "manual_refresh"
    cancelled = client.post(f"/api/materials/codex-jobs/{body['id']}/cancel")
    assert cancelled.status_code == 200

    forced = client.post(
        f"/api/materials/{material_id}/codex-jobs",
        json={"mode": "refresh_legacy", "skill_version": "refine-v2", "force": True, "run_reason": "continue_refine"},
    )
    assert forced.status_code == 200
    forced_body = forced.json()
    assert forced_body["id"] != body["id"]
    assert forced_body["skill_version"] == "refine-v2"
    assert forced_body["payload"]["run_reason"] == "continue_refine"
    assert forced_body["attempt_count"] == 1


def test_codex_skill_job_cancel_and_retry():
    client, material_id = make_client()
    created = client.post(f"/api/materials/{material_id}/codex-jobs", json={"mode": "new_pdf"}).json()

    cancelled = client.post(f"/api/materials/codex-jobs/{created['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    retried = client.post(f"/api/materials/codex-jobs/{created['id']}/retry")
    assert retried.status_code == 200
    assert retried.json()["status"] == "queued"
    assert retried.json()["attempt_count"] == 1


def test_legacy_batch_refresh_enqueues_existing_latex_outputs():
    client, _material_id = make_client()

    first = client.post("/api/materials/codex-jobs/batch-refresh-legacy", json={"limit": 10})
    assert first.status_code == 200
    assert first.json() == {"selected": 1, "created": 1, "existing": 0, "failed": 0}

    second = client.post("/api/materials/codex-jobs/batch-refresh-legacy", json={"limit": 10})
    assert second.status_code == 200
    assert second.json() == {"selected": 1, "created": 0, "existing": 1, "failed": 0}


def test_materials_list_prioritizes_active_codex_jobs():
    client, material_id = make_client()
    db = next(app.dependency_overrides[get_db]())
    try:
        db.add(
            Material(
                user_id="u1",
                material_id="pdf-newer",
                title="Newer ordinary material",
                filename="Newer.pdf",
                source_type="imported",
                stage_status="latex_done",
                pipeline_status="idle",
                latex_manifest_bucket="eduassets-latex",
                latex_manifest_object="latex/pdf-newer/popo-run/manifest.json",
            )
        )
        db.commit()
    finally:
        db.close()
    created = client.post(f"/api/materials/{material_id}/codex-jobs", json={"mode": "refresh_legacy"})
    assert created.status_code == 200

    listed = client.get("/api/materials", params={"page": 1, "page_size": 1})
    assert listed.status_code == 200
    rows = listed.json()["materials"]
    assert rows[0]["id"] == str(material_id)
    assert rows[0]["codex_job"]["status"] == "queued"


def test_publish_staging_job_registers_promoted_output(monkeypatch, tmp_path):
    db, material = make_session()
    fake_minio = FakeMinio()
    monkeypatch.setattr("app.services.codex_skill_jobs.minio_client", fake_minio)

    job = create_codex_skill_job(db, "u1", material, mode="refresh_legacy")
    run_dry_run_job(db, job, staging_root=tmp_path)
    staging_dir = tmp_path / f"job-{job.id}"
    (staging_dir / "compiled.pdf").write_bytes(b"%PDF-codex\n")
    (staging_dir / "refined-overleaf.zip").write_bytes(b"PK-codex")
    nested = staging_dir / "work" / "candidate"
    nested.mkdir(parents=True)
    (nested / "compiled.pdf").write_bytes(b"%PDF-nested\n")
    (nested / "refined-overleaf.zip").write_bytes(b"PK-nested")
    (staging_dir / "main.tex").write_text("\\documentclass{article}")
    (staging_dir / "run_state.json").write_text(json.dumps({"status": "passed"}))
    (staging_dir / "source_trace.json").write_text(json.dumps({"status": "passed"}))
    (staging_dir / "final_review_report.json").write_text(json.dumps({"status": "passed", "qa": {"status": "passed", "hard_blockers": [], "review_status": "passed"}}))
    (staging_dir / "final_review_report.md").write_text("# passed")
    (staging_dir / "compile_report.json").write_text(json.dumps({"status": "succeeded", "engine": "test", "pages": 1}))

    publish_staging_job(db, job, target_bucket="eduassets-elegantbook", promote=True)
    db.commit()
    db.refresh(job)
    db.refresh(material)

    assert job.status == "published"
    assert job.result()["status"] == "published"
    assert job.output_manifest_bucket == "eduassets-elegantbook"
    assert job.output_manifest_object.startswith("elegantbook/pdf-demo/popo-run/")
    assert ("eduassets-elegantbook", job.output_manifest_object) in fake_minio.objects
    manifest = json.loads(fake_minio.objects[("eduassets-elegantbook", job.output_manifest_object)]["content"])
    assert manifest["objects"]["compiled_pdf"] == "compiled.pdf"
    assert manifest["objects"]["refined_overleaf_zip"] == "refined-overleaf.zip"
    assert manifest["objects"]["package_zip"] == "refined-overleaf.zip"
    assert manifest["objects"]["main_tex"] == "main.tex"
    assert manifest["objects"]["final_review_report"] == "final_review_report.md"
    assert manifest["objects"]["final_review_report_json"] == "final_review_report.json"
    assert manifest["objects"]["run_state"] == "run_state.json"
    assert manifest["objects"]["source_trace"] == "source_trace.json"
    output = db.query(MaterialOutput).filter(MaterialOutput.codex_job_id == job.id).one()
    assert output.is_current is True
    assert output.quality_status == "passed"
    assert material.latex_manifest_object == job.output_manifest_object
