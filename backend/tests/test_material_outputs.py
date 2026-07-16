from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.material import Material
from app.models.review_asset import ReviewAsset
from app.services.codex_elegantbook import infer_ids
from app.services.material_outputs import register_elegantbook_output


def make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def test_output_keeps_review_asset_for_its_own_popo_run():
    db = make_session()
    material = Material(
        user_id="u1",
        material_id="pdf-1",
        title="Book",
        filename="book.pdf",
        stage_status="popo_done",
        pipeline_status="idle",
    )
    db.add(material)
    db.flush()
    old_asset = ReviewAsset(
        user_id="u1",
        title="Book",
        material_id="pdf-1",
        run_id="popo-old",
        manifest_bucket="eduassets-minerupopo",
        manifest_object="minerupopo/pdf-1/popo-old/manifest.json",
    )
    new_asset = ReviewAsset(
        user_id="u1",
        title="Book",
        material_id="pdf-1",
        run_id="popo-new",
        manifest_bucket="eduassets-minerupopo",
        manifest_object="minerupopo/pdf-1/popo-new/manifest.json",
    )
    db.add_all([old_asset, new_asset])
    db.flush()
    material.review_asset_id = new_asset.id

    output = SimpleNamespace(
        manifest_ref=SimpleNamespace(bucket="outputs", object="old-output/manifest.json"),
        material_id="pdf-1",
        origin="workflow_v2",
        popo_run_id="popo-old",
        output_run_id="worker-old",
        manifest={},
        created_at="2026-07-16T00:00:00",
    )
    row = register_elegantbook_output(db, "u1", material, output)

    assert row.review_asset_id == old_asset.id


def test_workflow_output_infers_popo_run_from_immutable_source_manifest():
    material = SimpleNamespace(material_id="pdf-1", popo_run_id="popo-current")
    manifest = {
        "schema": "luceon.workflow.artifact-manifest/v1",
        "workflow_job_id": "worker-old",
        "source_popo_manifest": {
            "bucket": "eduassets-minerupopo",
            "object": "minerupopo/pdf-1/popo-old/manifest.json",
        },
    }

    material_id, popo_run_id, output_run_id = infer_ids(
        "worker-v2/pdf-1/worker-old/stage/attempt/hash/manifest.json",
        manifest,
        material,
    )

    assert material_id == "pdf-1"
    assert popo_run_id == "popo-old"
    assert output_run_id == "worker-old"
