from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "import_legacy_selfloop_latex.py"
SPEC = importlib.util.spec_from_file_location("legacy_selfloop_latex_import", SCRIPT_PATH)
legacy_import = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = legacy_import
SPEC.loader.exec_module(legacy_import)


def make_material_row(popo_run_id: str):
    return legacy_import.MaterialRow(
        id=7,
        user_id="1",
        material_id="pdf-demo",
        title="Demo",
        filename="Demo.pdf",
        input_bucket="eduassets-input",
        input_object="Demo.pdf",
        mineru_manifest_bucket="eduassets-mineru",
        mineru_manifest_object="mineru/pdf-demo/mineru-run/manifest.json",
        mineru_run_id="mineru-run",
        popo_manifest_bucket="eduassets-minerupopo",
        popo_manifest_object=f"minerupopo/pdf-demo/{popo_run_id}/manifest.json",
        popo_run_id=popo_run_id,
        review_asset_id=11,
        stage_status="popo_done",
    )


def make_legacy_run(tmp_path: Path) -> Path:
    run_root = tmp_path / "work" / "selfloop" / "runs" / "run-demo"
    sample_id = "pdf-demo-sample"
    sample_root = run_root / "samples" / sample_id
    body_final = sample_root / "01-intake-outline-clean" / "body-final"
    annotation = sample_root / "02-semantic-annotation" / "annotation"
    project = sample_root / "03-elegantbook-render" / "elegantbook"
    compile_dir = sample_root / "03-elegantbook-render" / "compile"
    review = sample_root / "04-final-review"
    review_pack = review / "review_pack"
    for path in (body_final, annotation, project / "chapters", project / "images", compile_dir, review_pack):
        path.mkdir(parents=True, exist_ok=True)
    (body_final / "clean.md").write_text("# Demo\n", encoding="utf-8")
    (body_final / "qa_report.md").write_text("# QA\n", encoding="utf-8")
    (body_final / "outline_decision.json").write_text("{}", encoding="utf-8")
    (project / "main.tex").write_text("\\documentclass{article}", encoding="utf-8")
    (project / "main-fallback.tex").write_text("\\documentclass{article}", encoding="utf-8")
    (project / "main.pdf").write_bytes(b"%PDF-1.4\n")
    (project / "chapters" / "content.tex").write_text("Demo", encoding="utf-8")
    (project / "images" / "one.png").write_bytes(b"png")
    (sample_root / "03-elegantbook-render" / "elegantbook-overleaf.zip").write_bytes(b"zip")
    (compile_dir / "overleaf_compile_report.json").write_text('{"success": true, "container": "sharelatex"}', encoding="utf-8")
    (review / "final_review_gate.json").write_text("{}", encoding="utf-8")
    (review / "final_review_gate.md").write_text("# Final\n", encoding="utf-8")
    (review_pack / "contact_sheet.png").write_bytes(b"png")
    (review_pack / "page-0001.png").write_bytes(b"png")
    (review_pack / "automated_review_report.json").write_text('{"pdfinfo": {"pages": 1}}', encoding="utf-8")

    sample = {
        "sample_id": sample_id,
        "pdf_id": "pdf-demo",
        "job_id": "popo-run",
        "source_name": "Demo.pdf",
        "source_hash": "hash",
        "source_pdf_sha256": "demo-sha",
        "popo_prefix": "eduassets-minerupopo/minerupopo/pdf-demo/popo-run",
        "mineru_runs": ["mineru-run"],
    }
    (run_root / "sample_basket.json").write_text(json.dumps({"selected": [sample]}), encoding="utf-8")
    (run_root / "run_state.json").write_text(
        json.dumps(
            {
                "samples": [
                    {
                        **sample,
                        "status": "passed",
                        "accepted": True,
                        "stages": [
                            {"id": "01-intake-outline-clean", "skill": "pdf-clean-markdown-rebuild", "status": "passed"},
                            {"id": "02-semantic-annotation", "skill": "material-semantic-annotator", "status": "passed"},
                            {"id": "03-elegantbook-render", "skill": "cleanlatex-to-elegantbook", "status": "passed"},
                            {"id": "04-final-review", "skill": "finished-textbook-final-review", "status": "passed"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (run_root / "visual_review_queue.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "sample_id": sample_id,
                        "final_stage_status": "passed",
                        "visual_status": "agent_approved",
                        "rendered_pages": [f"work/selfloop/runs/run-demo/samples/{sample_id}/04-final-review/review_pack/page-0001.png"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (run_root / "final_all_after_visual_approval_preserve_fix.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    return run_root


def test_upload_items_emit_product_latex_manifest(tmp_path):
    run_root = make_legacy_run(tmp_path)
    sample = legacy_import.load_legacy_samples(run_root)[0]
    items, summary = legacy_import.build_upload_items(run_root, sample, [make_material_row("popo-run")], include_sources=True)
    by_name = {item.relative_object: item for item in items}

    assert summary["matched_material_rows"] == [7]
    assert by_name["compiled.pdf"].path and by_name["compiled.pdf"].path.name == "main.pdf"
    assert "chapters/content.tex" in by_name
    assert "images/one.png" in by_name

    manifest = json.loads(by_name["manifest.json"].data.decode("utf-8"))
    assert manifest["schema"] == "luceon-latex-material/v1"
    assert manifest["stage"] == "latex"
    assert manifest["material_id"] == "pdf-demo"
    assert manifest["run_id"] == "popo-run"
    assert manifest["objects"]["compiled_pdf"] == "compiled.pdf"
    assert manifest["source"]["popo_run_id"] == "popo-run"


def test_import_report_requires_exact_popo_run_match(tmp_path):
    run_root = make_legacy_run(tmp_path)
    db_path = tmp_path / "mineru.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        create table materials (
            id integer primary key,
            user_id text,
            material_id text,
            title text,
            filename text,
            input_bucket text,
            input_object text,
            mineru_manifest_bucket text,
            mineru_manifest_object text,
            mineru_run_id text,
            popo_manifest_bucket text,
            popo_manifest_object text,
            popo_run_id text,
            review_asset_id integer,
            stage_status text,
            ignored boolean default 0
        )
        """
    )
    conn.execute(
        """
        insert into materials (
            id, user_id, material_id, title, filename,
            input_bucket, input_object,
            mineru_manifest_bucket, mineru_manifest_object, mineru_run_id,
            popo_manifest_bucket, popo_manifest_object, popo_run_id,
            review_asset_id, stage_status, ignored
        ) values (
            1, '1', 'pdf-demo', 'Demo', 'Demo.pdf',
            'eduassets-input', 'Demo.pdf',
            'eduassets-mineru', 'mineru/pdf-demo/mineru-run/manifest.json', 'mineru-run',
            'eduassets-minerupopo', 'minerupopo/pdf-demo/other-run/manifest.json', 'other-run',
            9, 'popo_done', 0
        )
        """
    )
    conn.commit()
    conn.close()

    report, _rows = legacy_import.import_report(db_path, run_root, user_ids=None, include_sources=False)

    assert report[0]["matched_material_rows"] == []
    assert report[0]["will_update_db"] is False
    assert report[0]["missing_required"] == []
