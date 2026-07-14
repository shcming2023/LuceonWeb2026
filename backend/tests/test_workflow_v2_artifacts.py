from pathlib import Path
from io import BytesIO
from types import SimpleNamespace

from app.workflow_v2.artifacts import (
    ArtifactIntegrityError,
    optimize_delivery_images,
    publish_stage_directory,
    write_latex_delivery_zip,
    write_reproducible_zip,
)
from app.workflow_v2.contracts import STAGE_CONTRACTS
from app.workflow_v2.models import ArtifactVersion
from app.workflow_v2.service import create_workflow_job
from app.workflow_v2.state_machine import claim_current_stage
from test_workflow_v2 import make_sessions


class FakeMinio:
    def __init__(self):
        self.objects = {}

    def stat_object(self, bucket, object_name):
        try:
            content, metadata = self.objects[(bucket, object_name)]
        except KeyError:
            raise FileNotFoundError(object_name)
        return SimpleNamespace(size=len(content), metadata=metadata)

    def put_object(self, bucket, object_name, stream, length, content_type, metadata):
        content = stream.read()
        assert len(content) == length
        self.objects[(bucket, object_name)] = (content, {"x-amz-meta-sha256": metadata["sha256"]})

    def get_object(self, bucket, object_name):
        content, _metadata = self.objects[(bucket, object_name)]
        response = BytesIO(content)
        response.release_conn = lambda: None
        return response


def _write_locked_delivery_scaffold(project: Path) -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / "images").mkdir(exist_ok=True)
    (project / "figure").mkdir(exist_ok=True)
    (project / "main.tex").write_text("\\documentclass{elegantbook}\n", encoding="utf-8")
    (project / "elegantbook.cls").write_text("class\n", encoding="utf-8")
    (project / "figure/logo.jpg").write_bytes(b"logo")
    (project / "figure/cover.jpg").write_bytes(b"cover")


def test_stage_artifact_is_content_addressed_and_idempotent(tmp_path: Path):
    _old_db, db, material = make_sessions()
    job, _ = create_workflow_job(db, user_id="u1", material=material)
    _job, stage = claim_current_stage(db, job.public_id, "worker-a")
    output = tmp_path / "output"
    output.mkdir()
    (output / "clean.md").write_text("# Stable\n", encoding="utf-8")
    client = FakeMinio()

    first = publish_stage_directory(db, client, job=job, stage=stage, source_dir=output, artifact_kind="canonical_clean", contract=STAGE_CONTRACTS[0].to_dict())
    second = publish_stage_directory(db, client, job=job, stage=stage, source_dir=output, artifact_kind="canonical_clean", contract=STAGE_CONTRACTS[0].to_dict())
    db.commit()

    assert first.id == second.id
    assert first.object_name.endswith(f"/{first.sha256}/manifest.json")
    assert db.query(ArtifactVersion).count() == 1
    assert len(client.objects) == 2


def test_delivery_zip_is_byte_reproducible_and_does_not_include_itself(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.tex").write_text("\\documentclass{elegantbook}\n", encoding="utf-8")
    (project / "images").mkdir()
    (project / "images" / "figure.png").write_bytes(b"png")

    first = write_reproducible_zip(project, project / "latex-project.zip")
    first_bytes = (project / "latex-project.zip").read_bytes()
    second = write_reproducible_zip(project, project / "latex-project.zip")

    assert first["sha256"] == second["sha256"]
    assert first_bytes == (project / "latex-project.zip").read_bytes()
    assert first["file_count"] == 2


def test_delivery_zip_can_exclude_compiled_pdf_and_reports(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.tex").write_text("\\documentclass{elegantbook}\n", encoding="utf-8")
    (project / "main.pdf").write_bytes(b"compiled pdf")
    (project / "compile-report.json").write_text("{}\n", encoding="utf-8")

    result = write_reproducible_zip(
        project,
        project / "latex-project.zip",
        exclude_paths={"main.pdf", "compile-report.json"},
    )

    import zipfile

    with zipfile.ZipFile(project / "latex-project.zip") as archive:
        assert archive.namelist() == ["main.tex"]
    assert result["file_count"] == 1


def test_delivery_image_optimization_preserves_names_and_count(tmp_path: Path):
    from PIL import Image

    project = tmp_path / "project"
    _write_locked_delivery_scaffold(project)
    image_dir = project / "images"
    Image.effect_noise((2400, 2400), 100).convert("RGB").save(image_dir / "large-a.jpg", quality=100)
    Image.effect_noise((2400, 2400), 100).save(image_dir / "large-b.png")

    before_names = sorted(path.name for path in image_dir.iterdir())
    report = optimize_delivery_images(project, max_image_bytes=20_000, max_zip_bytes=40_000)

    assert sorted(path.name for path in image_dir.iterdir()) == before_names
    assert report["image_count"] == 2
    assert report["filenames_preserved"] is True
    assert report["max_image_bytes"] <= 20_000
    assert (project / ".latex-size-check.zip").exists() is False


def test_locked_latex_delivery_zip_contains_only_the_four_allowed_root_entries(tmp_path: Path):
    import zipfile

    project = tmp_path / "project"
    _write_locked_delivery_scaffold(project)
    (project / "images/page-1.png").write_bytes(b"image")
    (project / "main.pdf").write_bytes(b"must not ship")
    (project / "chapters").mkdir()
    (project / "chapters/content.tex").write_text("internal\n", encoding="utf-8")

    result = write_latex_delivery_zip(project, project / "latex-project.zip")

    with zipfile.ZipFile(project / "latex-project.zip") as archive:
        names = archive.namelist()
    assert set(names) == {
        "images/",
        "images/page-1.png",
        "figure/",
        "figure/logo.jpg",
        "figure/cover.jpg",
        "main.tex",
        "elegantbook.cls",
    }
    assert result["root_entries"] == ["images/", "figure/", "main.tex", "elegantbook.cls"]


def test_locked_latex_delivery_rejects_extra_figure_files(tmp_path: Path):
    project = tmp_path / "project"
    _write_locked_delivery_scaffold(project)
    (project / "figure/extra.jpg").write_bytes(b"extra")

    try:
        write_latex_delivery_zip(project, project / "latex-project.zip")
    except ArtifactIntegrityError as exc:
        assert "other than logo.jpg and cover.jpg" in str(exc)
    else:
        raise AssertionError("expected strict figure whitelist gate to fail")


def test_delivery_zip_size_limit_is_hard_gate(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.tex").write_bytes(b"x" * 4096)

    try:
        write_reproducible_zip(project, project / "latex-project.zip", max_size_bytes=100)
    except ArtifactIntegrityError as exc:
        assert "exceeds size limit" in str(exc)
    else:
        raise AssertionError("expected the delivery ZIP size gate to fail")
