import json
import shutil
from pathlib import Path

from app.workflow_v2.elegantbook_validation import _enrich_latex_diagnostics, validate_elegantbook_project


def test_compile_diagnostics_gain_source_line_and_page_evidence():
    main = """\\documentclass{elegantbook}
% source_page_idx: 17
Text with 囲.
Long answer branch.
"""
    diagnostics = _enrich_latex_diagnostics(
        {
            "missing_characters": [{"character": "囲", "pdf_page_hint": 18}],
            "overfull_hboxes": [{"width_pt": 25.0, "line_start": 4, "line_end": 4, "pdf_page_hint": 19}],
        },
        main,
    )

    assert diagnostics["missing_characters"][0]["occurrences"][0]["source_page_idx"] == "17"
    assert diagnostics["missing_characters"][0]["occurrences"][0]["line"] == 3
    assert diagnostics["overfull_hboxes"][0]["source_page_idx"] == "17"
    assert diagnostics["overfull_hboxes"][0]["excerpt"] == "Long answer branch."
from app.workflow_v2.runtime.elegantbook.scripts.clean_to_elegantbook import render_locked_template_main


ASSETS = Path(__file__).parents[1] / "app" / "workflow_v2" / "runtime" / "elegantbook" / "assets"


def _fixture(tmp_path):
    project = tmp_path / "project"
    (project / "chapters").mkdir(parents=True)
    (project / "images").mkdir()
    (project / "figure").mkdir()
    semantic = tmp_path / "semantic.md"
    cleanlatex = tmp_path / "input.tex"
    bundled = ASSETS / "elegantbook.cls"
    semantic.write_text("<!-- page_idx: 0 -->\n# Unit 1\n## Word power\n## Practice\n![A](images/a.png)\n", encoding="utf-8")
    cleanlatex.write_text("source", encoding="utf-8")
    shutil.copy2(bundled, project / "elegantbook.cls")
    shutil.copy2(ASSETS / "figure/logo.jpg", project / "figure/logo.jpg")
    shutil.copy2(ASSETS / "figure/cover.jpg", project / "figure/cover.jpg")
    content = "% source_page_idx: 0\n\\chapter{Unit 1}\n\\begin{tcolorbox}[vocabbox,title={Word power}]\n\\end{tcolorbox}\n\\section{Practice}\n\\includegraphics{images/a.png}\n"
    (project / "chapters/content.tex").write_text(content, encoding="utf-8")
    (project / "main.tex").write_text(render_locked_template_main(
        content=content,
        title="Unit 1",
        subtitle="高阶班",
        author=r"Emily\&Sunny\&Kuma",
        institute="橡心国际",
        date_text="June, 2025",
    ), encoding="utf-8")
    (project / "images/a.png").write_bytes(b"image")
    (project / "main.pdf").write_bytes(b"pdf")
    (project / "compile-report.json").write_text(json.dumps({
        "engine_version": "XeTeX (TeX Live 2025)",
        "source_date_epoch": 0,
        "passes": 3,
        "pdf_sha256_by_pass": ["a", "b", "b"],
        "page_count_by_pass": [1, 1, 1],
        "byte_identical_final_passes": True,
        "diagnostics": {
            "schema": "luceon.latex-diagnostics/v1",
            "obvious_overflow_threshold_pt": 10.0,
            "missing_character_count": 0,
            "missing_characters": [],
            "overfull_hbox_count": 0,
            "overfull_hboxes": [],
            "obvious_overflow_count": 0,
            "max_overfull_pt": 0.0,
            "unresolved_reference_or_resource_count": 0,
        },
        "log_tail": "",
    }), encoding="utf-8")
    return project, semantic, cleanlatex, bundled


def test_elegantbook_validation_accepts_structural_environment_mapping(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    assert result["status"] == "passed"
    assert all(result["gates"].values())
    assert (project / "lineage.json").is_file()


def test_elegantbook_validation_blocks_missing_heading_and_unsafe_asset(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    (project / "chapters/content.tex").write_text("% source_page_idx: 0\n\\chapter{Unit 1}\n\\includegraphics{../outside.png}\n", encoding="utf-8")

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    codes = {row["code"] for row in result["blockers"]}
    assert "semantic_outline_not_preserved_in_latex" in codes
    assert "project_uses_nonlocal_image_path" in codes


def test_elegantbook_validation_blocks_structural_heading_not_in_accepted_outline(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    content = project / "chapters/content.tex"
    content.write_text(content.read_text(encoding="utf-8") + "\\chapter{Invented chapter}\n", encoding="utf-8")

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    blocker = next(row for row in result["blockers"] if row["code"] == "latex_structural_headings_not_in_accepted_outline")
    assert blocker["representations"] == [r"\chapter{Invented chapter}"]
    assert result["gates"]["outline_content_and_lineage_invariants_preserved"] is False


def test_elegantbook_validation_requires_exact_semantic_image_multiplicity(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    content = project / "chapters/content.tex"

    passed = validate_elegantbook_project(project, semantic, cleanlatex, bundled)
    assert passed["status"] == "passed"

    content.write_text(content.read_text(encoding="utf-8") + "\\includegraphics{images/a.png}\n", encoding="utf-8")
    blocked = validate_elegantbook_project(project, semantic, cleanlatex, bundled)
    assert "latex_images_not_in_semantic_input" in {row["code"] for row in blocked["blockers"]}


def test_elegantbook_validation_blocks_missing_glyphs_and_obvious_overflow(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    report_path = project / "compile-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["diagnostics"].update({
        "missing_character_count": 1,
        "missing_characters": [{"character": "囲", "codepoint": "U+56F2", "font": "FandolSong"}],
        "overfull_hbox_count": 2,
        "overfull_hboxes": [
            {"width_pt": 2.5, "line_start": 10, "line_end": 11},
            {"width_pt": 21.9, "line_start": 20, "line_end": 22},
        ],
        "obvious_overflow_count": 1,
        "max_overfull_pt": 21.9,
    })
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    assert {row["code"] for row in result["blockers"]} >= {"latex_missing_glyphs", "latex_obvious_overflow"}
    assert result["gates"]["candidate_compiles_reproducibly_in_texlive_2025"] is False


def test_elegantbook_validation_rejects_legacy_report_without_structured_diagnostics(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    report_path = project / "compile-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    del report["diagnostics"]
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    assert "latex_structured_diagnostics_missing" in {row["code"] for row in result["blockers"]}


def test_elegantbook_validation_blocks_private_use_ocr_residue_even_when_font_renders_it(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    content_path = project / "chapters/content.tex"
    content_path.write_text(content_path.read_text(encoding="utf-8") + "OCR residue: \ue000\n", encoding="utf-8")

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    blocker = next(row for row in result["blockers"] if row["code"] == "latex_private_use_characters")
    assert blocker["count"] == 1
    assert blocker["occurrences"][0]["codepoint"] == "U+E000"


def test_elegantbook_validation_blocks_any_locked_template_change(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    main_path = project / "main.tex"
    main_path.write_text(main_path.read_text(encoding="utf-8").replace(
        r"\usepackage{pifont}",
        "\\usepackage{pifont}\n\\usepackage{xurl}",
        1,
    ), encoding="utf-8")

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    assert "elegantbook_locked_main_template_changed" in {row["code"] for row in result["blockers"]}


def test_elegantbook_validation_blocks_changed_popo_image_inventory(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    (project / "delivery-image-inventory.json").write_text(
        '{"expected_count":2,"actual_count":1,"filenames_and_count_preserved":false}',
        encoding="utf-8",
    )

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    assert "popo_image_inventory_changed" in {row["code"] for row in result["blockers"]}


def test_elegantbook_validation_blocks_custom_command_definitions_in_body(tmp_path):
    project, semantic, cleanlatex, bundled = _fixture(tmp_path)
    content_path = project / "chapters/content.tex"
    content = content_path.read_text(encoding="utf-8") + r"\newcommand{\extraformat}[1]{#1}" + "\n"
    content_path.write_text(content, encoding="utf-8")
    (project / "main.tex").write_text(render_locked_template_main(
        content=content,
        title="Unit 1",
        subtitle="高阶班",
        author=r"Emily\&Sunny\&Kuma",
        institute="橡心国际",
        date_text="June, 2025",
    ), encoding="utf-8")

    result = validate_elegantbook_project(project, semantic, cleanlatex, bundled)

    assert "elegantbook_body_defines_custom_latex" in {row["code"] for row in result["blockers"]}
