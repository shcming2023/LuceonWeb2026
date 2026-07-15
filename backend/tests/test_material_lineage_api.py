import hashlib
import io
import asyncio
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile

from app.api import materials as materials_api
from app.models.base import Base
from app.models.material import Material, MaterialOutput, MetadataJob, PipelineRun, PipelineRunItem, PipelineStageAttempt
from app.services.material_inventory import material_id_from_sha256, upload_input_pdfs


def make_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def add_material(db, *, user_id="u1"):
    row = Material(
        user_id=user_id,
        material_id="pdf-lineage",
        source_hash="source",
        title="Lineage Book",
        filename="lineage.pdf",
        source_type="uploaded",
        input_bucket="eduassets-input",
        input_object="lineage.pdf",
        input_sha256="a" * 64,
        stage_status="popo_done",
        pipeline_status="idle",
    )
    db.add(row)
    db.flush()
    return row


def test_lineage_joins_pipeline_metadata_worker_output_and_review(monkeypatch):
    db = make_session()
    material = add_material(db)
    material.review_asset_id = 42
    run = PipelineRun(user_id="u1", status="partial", mode="apply", total=1, failed=1)
    db.add(run)
    db.flush()
    item = PipelineRunItem(
        run_id=run.id,
        user_id="u1",
        material_pk=material.id,
        material_id=material.material_id,
        filename=material.filename,
        input_bucket=material.input_bucket,
        input_object=material.input_object,
        status="failed",
        current_stage="popo",
    )
    db.add(item)
    db.flush()
    db.add(PipelineStageAttempt(run_item_id=item.id, user_id="u1", stage="popo", attempt=1, status="failed"))
    db.add(MetadataJob(user_id="u1", material_pk=material.id, material_id=material.material_id, status="queued", idempotency_key="metadata-1"))
    db.add(MaterialOutput(user_id="u1", material_pk=material.id, material_id=material.material_id, review_asset_id=42, manifest_bucket="outputs", manifest_object="manifest.json"))
    db.commit()

    class WorkflowSession:
        def close(self):
            pass

    monkeypatch.setattr(materials_api, "workflow_session_factory", lambda: lambda: WorkflowSession())
    monkeypatch.setattr(materials_api, "list_workflow_jobs", lambda *_args, **_kwargs: [{"id": "worker-1", "status": "needs_review"}])

    result = materials_api.get_material_lineage(material.id, user_id="u1", db=db)

    assert result["pipeline_items"][0]["attempts"][0]["stage"] == "popo"
    assert result["metadata_jobs"][0]["status"] == "queued"
    assert result["workflow_jobs"][0]["id"] == "worker-1"
    assert result["outputs"][0]["review_asset_id"] == "42"
    assert result["review"] == {"asset_id": "42", "available": True}


def test_upload_deduplicates_by_sha_before_minio_write_and_records_pages(monkeypatch):
    data = (Path(__file__).parent / "test.pdf").read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    db = make_session()
    material = add_material(db)
    material.material_id = material_id_from_sha256(sha256)
    material.input_sha256 = sha256
    material.page_count = None
    db.commit()

    class ForbiddenMinio:
        def put_object(self, *_args, **_kwargs):
            raise AssertionError("duplicate upload must not write MinIO")

    monkeypatch.setattr("app.services.material_inventory.minio_client", ForbiddenMinio())
    upload = UploadFile(filename="same-content-renamed.pdf", file=io.BytesIO(data))
    result = asyncio.run(upload_input_pdfs([upload], "u1", db))

    assert result["duplicates"] == 1
    assert result["success"] == 1
    assert result["files"][0]["status"] == "duplicate"
    assert material.page_count and material.page_count > 0
    assert db.query(Material).count() == 1
