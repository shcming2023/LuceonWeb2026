from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from app.workflow_v2.runtime.elegantbook.scripts.clean_to_elegantbook import (
    BOX_TITLES,
    format_heading_title,
    is_exercise_title,
    render_locked_template_main,
)
from app.workflow_v2.runtime.elegantbook.scripts.semantic_markdown_to_cleanlatex import clean_heading


LOCKED_TEMPLATE_SHA256 = {
    "template-main.tex": "b684a7ab0af064111ea36864661a736571340f173c756534343437f4efef71f4",
    "elegantbook.cls": "048c3b90da41be64f4744da3bff6ae8c5ea7abd30a5f3e2a6ad1a98f3b0d71fe",
    "figure/logo.jpg": "e11c44cd0d23767e58140ef2abe77025d817220717d734fcd68fc3d402de7bb0",
    "figure/cover.jpg": "a756e026bf8ca0f59e0cc9820f45d765709103137a2c6fcc9f5ee8b15cb25a30",
}


def validate_elegantbook_project(
    project_dir: Path,
    semantic_markdown: Path,
    cleanlatex_path: Path,
    bundled_class: Path,
) -> dict:
    required = [
        "main.tex",
        "elegantbook.cls",
        "chapters/content.tex",
        "figure/logo.jpg",
        "figure/cover.jpg",
        "main.pdf",
        "compile-report.json",
    ]
    missing_files = [name for name in required if not (project_dir / name).is_file()]
    blockers = []
    if missing_files:
        blockers.append({"code": "elegantbook_project_files_missing", "paths": missing_files})
        return _write_reports(project_dir, blockers, {}, {})

    main = (project_dir / "main.tex").read_text(encoding="utf-8")
    content = (project_dir / "chapters/content.tex").read_text(encoding="utf-8")
    semantic = semantic_markdown.read_text(encoding="utf-8")
    compile_report = json.loads((project_dir / "compile-report.json").read_text(encoding="utf-8"))

    private_use = [
        {"character": char, "codepoint": f"U+{ord(char):04X}", "line": line_number}
        for line_number, line in enumerate(content.splitlines(), start=1)
        for char in line
        if _is_private_use(char)
    ]
    if private_use:
        blockers.append({"code": "latex_private_use_characters", "count": len(private_use), "occurrences": private_use[:200]})

    if not re.search(r"\\documentclass(?:\[[^]]*\])?\{elegantbook\}", main):
        blockers.append({"code": "elegantbook_documentclass_missing"})
    class_matches = (
        _sha256(bundled_class) == LOCKED_TEMPLATE_SHA256["elegantbook.cls"]
        and _sha256(project_dir / "elegantbook.cls") == LOCKED_TEMPLATE_SHA256["elegantbook.cls"]
    )
    if not class_matches:
        blockers.append({"code": "elegantbook_template_fingerprint_mismatch"})
    locked_template = bundled_class.parent / "template-main.tex"
    bundled_figure_dir = bundled_class.parent / "figure"
    template_assets_match = (
        locked_template.is_file()
        and _sha256(locked_template) == LOCKED_TEMPLATE_SHA256["template-main.tex"]
        and all(
        (bundled_figure_dir / name).is_file()
        and _sha256(bundled_figure_dir / name) == LOCKED_TEMPLATE_SHA256[f"figure/{name}"]
        and _sha256(project_dir / "figure" / name) == LOCKED_TEMPLATE_SHA256[f"figure/{name}"]
        for name in ("logo.jpg", "cover.jpg")
        )
    )
    if not template_assets_match:
        blockers.append({"code": "elegantbook_locked_figure_fingerprint_mismatch"})

    metadata = _extract_locked_metadata(main)
    if metadata is None:
        blockers.append({"code": "elegantbook_locked_metadata_invalid"})
        main_matches_locked_template = False
    elif not template_assets_match:
        main_matches_locked_template = False
    else:
        expected_main = render_locked_template_main(content=content, date_text=metadata.pop("date"), **metadata)
        main_matches_locked_template = main == expected_main
        if not main_matches_locked_template:
            blockers.append({"code": "elegantbook_locked_main_template_changed"})

    forbidden_definitions = _forbidden_body_definitions(content)
    if forbidden_definitions:
        blockers.append({
            "code": "elegantbook_body_defines_custom_latex",
            "occurrences": forbidden_definitions[:200],
        })

    expected_representations = _expected_heading_representations(semantic)
    actual_representations = Counter(
        _normalize_font_fallbacks(line.strip()) for line in content.splitlines() if line.strip()
    )
    missing_representations = sorted((expected_representations - actual_representations).elements())
    if missing_representations:
        blockers.append({"code": "semantic_outline_not_preserved_in_latex", "representations": missing_representations[:200]})
    expected_structural = Counter({
        representation: count
        for representation, count in expected_representations.items()
        if representation.startswith((r"\chapter{", r"\section{", r"\subsection{"))
    })
    actual_structural = Counter(
        _normalize_font_fallbacks(line.strip()) for line in content.splitlines()
        if line.strip().startswith((r"\chapter{", r"\section{", r"\subsection{"))
    )
    extra_structural = sorted((actual_structural - expected_structural).elements())
    if extra_structural:
        blockers.append({"code": "latex_structural_headings_not_in_accepted_outline", "representations": extra_structural[:200]})

    semantic_pages = re.findall(r"<!--\s*page_idx:\s*([^>]+?)\s*-->", semantic)
    latex_pages = re.findall(r"^%\s*source_page_idx:\s*(.+?)\s*$", content, re.M)
    if semantic_pages != latex_pages:
        blockers.append({"code": "source_page_lineage_changed", "semantic_count": len(semantic_pages), "latex_count": len(latex_pages)})

    semantic_image_refs = re.findall(r"\]\((images/[^)]+)\)", semantic)
    semantic_image_refs.extend(re.findall(r"<img\b[^>]*\bsrc=[\"'](images/[^\"']+)[\"']", semantic, re.I))
    image_refs = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", content)
    missing_image_representations = sorted((Counter(semantic_image_refs) - Counter(image_refs)).elements())
    extra_image_representations = sorted((Counter(image_refs) - Counter(semantic_image_refs)).elements())
    if missing_image_representations:
        blockers.append({"code": "semantic_images_missing_from_latex", "paths": missing_image_representations[:200]})
    if extra_image_representations:
        blockers.append({"code": "latex_images_not_in_semantic_input", "paths": extra_image_representations[:200]})
    unsafe_refs = sorted({ref for ref in image_refs if Path(ref).is_absolute() or ".." in Path(ref).parts})
    missing_images = sorted({ref for ref in image_refs if not (project_dir / ref).is_file()})
    if unsafe_refs:
        blockers.append({"code": "project_uses_nonlocal_image_path", "paths": unsafe_refs})
    if missing_images:
        blockers.append({"code": "project_images_missing", "paths": missing_images[:200]})
    inventory_path = project_dir / "delivery-image-inventory.json"
    image_inventory = json.loads(inventory_path.read_text(encoding="utf-8")) if inventory_path.is_file() else {}
    image_inventory_preserved = image_inventory.get("filenames_and_count_preserved") is True
    if image_inventory and not image_inventory_preserved:
        blockers.append({
            "code": "popo_image_inventory_changed",
            "expected_count": image_inventory.get("expected_count"),
            "actual_count": image_inventory.get("actual_count"),
        })

    compile_ok = (
        compile_report.get("byte_identical_final_passes") is True
        and len(compile_report.get("pdf_sha256_by_pass") or []) >= 2
        and len(set((compile_report.get("pdf_sha256_by_pass") or [])[-2:])) == 1
        and "TeX Live 2025" in str(compile_report.get("engine_version") or "")
    )
    if not compile_ok:
        blockers.append({"code": "texlive_2025_reproducible_compile_gate_failed"})
    diagnostics = compile_report.get("diagnostics")
    if not isinstance(diagnostics, dict):
        blockers.append({"code": "latex_structured_diagnostics_missing"})
        diagnostics = {}
    diagnostics = _enrich_latex_diagnostics(diagnostics, main)
    if int(diagnostics.get("unresolved_reference_or_resource_count") or 0) > 0:
        blockers.append({"code": "latex_unresolved_reference_or_resource"})
    if int(diagnostics.get("missing_character_count") or 0) > 0:
        blockers.append({
            "code": "latex_missing_glyphs",
            "count": diagnostics.get("missing_character_count"),
            "characters": (diagnostics.get("missing_characters") or [])[:200],
        })
    if int(diagnostics.get("obvious_overflow_count") or 0) > 0:
        blockers.append({
            "code": "latex_obvious_overflow",
            "count": diagnostics.get("obvious_overflow_count"),
            "max_overfull_pt": diagnostics.get("max_overfull_pt"),
            "boxes": [
                row for row in (diagnostics.get("overfull_hboxes") or [])
                if float(row.get("width_pt") or 0) >= float(diagnostics.get("obvious_overflow_threshold_pt") or 10.0)
            ][:200],
        })

    lineage = {
        "schema": "luceon.elegantbook-lineage/v1",
        "semantic_markdown_sha256": _sha256(semantic_markdown),
        "cleanlatex_sha256": _sha256(cleanlatex_path),
        "template_main_sha256": _sha256(locked_template),
        "elegantbook_class_sha256": _sha256(project_dir / "elegantbook.cls"),
        "logo_sha256": _sha256(project_dir / "figure" / "logo.jpg"),
        "cover_sha256": _sha256(project_dir / "figure" / "cover.jpg"),
        "main_tex_sha256": _sha256(project_dir / "main.tex"),
        "content_tex_sha256": _sha256(project_dir / "chapters/content.tex"),
        "compiled_pdf_sha256": _sha256(project_dir / "main.pdf"),
        "engine_version": compile_report.get("engine_version"),
        "source_date_epoch": compile_report.get("source_date_epoch"),
    }
    evidence = {
        "required_files": required,
        "class_matches_bundled": class_matches,
        "main_matches_locked_template": main_matches_locked_template,
        "locked_figure_assets_match": template_assets_match,
        "forbidden_body_definition_count": len(forbidden_definitions),
        "semantic_heading_count": sum(expected_representations.values()),
        "latex_heading_representation_count": sum((expected_representations & actual_representations).values()),
        "expected_structural_heading_count": sum(expected_structural.values()),
        "actual_structural_heading_count": sum(actual_structural.values()),
        "extra_structural_heading_count": len(extra_structural),
        "source_page_marker_count": len(semantic_pages),
        "image_reference_count": len(image_refs),
        "semantic_image_reference_count": len(semantic_image_refs),
        "missing_image_representation_count": len(missing_image_representations),
        "extra_image_representation_count": len(extra_image_representations),
        "missing_image_count": len(missing_images),
        "unsafe_image_reference_count": len(unsafe_refs),
        "popo_image_inventory_preserved": image_inventory_preserved if image_inventory else None,
        "popo_image_inventory_expected_count": image_inventory.get("expected_count"),
        "popo_image_inventory_actual_count": image_inventory.get("actual_count"),
        "private_use_character_count": len(private_use),
        "compile_passes": compile_report.get("passes"),
        "compiled_page_count": (compile_report.get("page_count_by_pass") or [None])[-1],
        "latex_diagnostics": diagnostics,
    }
    return _write_reports(project_dir, blockers, evidence, lineage)


def _expected_heading_representations(markdown: str) -> Counter:
    rows = Counter()
    for match in re.finditer(r"^(#{1,3})\s+(.+?)\s*$", markdown, re.M):
        level = len(match.group(1))
        title = format_heading_title(clean_heading(match.group(2)))
        if level == 1:
            representation = rf"\chapter{{{title}}}"
        elif level == 2 and title in BOX_TITLES:
            style = "vocabbox" if title == "Word power" else "notebox"
            representation = rf"\begin{{tcolorbox}}[{style},title={{{title}}}]"
        elif level == 2 and is_exercise_title(title):
            representation = rf"\subsection*{{{title}}}"
        elif level == 2:
            representation = rf"\section{{{title}}}"
        elif is_exercise_title(title):
            representation = rf"\subsection*{{{title}}}"
        else:
            representation = rf"\subsection{{{title}}}"
        rows[representation] += 1
    return rows


def _normalize_font_fallbacks(value: str) -> str:
    value = re.sub(r"\{\\CJKfontspec\{IPAexMincho\}([^{}])\}", r"\1", value)
    return re.sub(r"\{\\fontspec\{Charis SIL\}([^{}]+)\}", r"\1", value)


def _enrich_latex_diagnostics(diagnostics: dict, main: str) -> dict:
    """Attach best-effort PDF/source-page/line evidence to compile diagnostics."""
    enriched = dict(diagnostics)
    lines = main.splitlines()
    source_pages: list[str | None] = []
    current_source_page: str | None = None
    for line in lines:
        marker = re.match(r"^%\s*source_page_idx:\s*(.+?)\s*$", line)
        if marker:
            current_source_page = marker.group(1)
        source_pages.append(current_source_page)

    missing_rows = []
    for row in diagnostics.get("missing_characters") or []:
        item = dict(row)
        char = str(item.get("character") or "")
        occurrences = []
        if char:
            for line_number, line in enumerate(lines, start=1):
                if char not in line:
                    continue
                occurrences.append({
                    "line": line_number,
                    "source_page_idx": source_pages[line_number - 1],
                    "excerpt": line.strip()[:240],
                })
                if len(occurrences) >= 20:
                    break
        item["occurrences"] = occurrences
        missing_rows.append(item)

    overfull_rows = []
    for row in diagnostics.get("overfull_hboxes") or []:
        item = dict(row)
        line_number = int(item.get("line_start") or 0)
        if 1 <= line_number <= len(lines):
            item["source_page_idx"] = source_pages[line_number - 1]
            item["excerpt"] = lines[line_number - 1].strip()[:400]
        else:
            item["source_page_idx"] = None
            item["excerpt"] = ""
        overfull_rows.append(item)
    enriched["missing_characters"] = missing_rows
    enriched["overfull_hboxes"] = overfull_rows
    return enriched


def _extract_locked_metadata(main: str) -> dict[str, str] | None:
    values: dict[str, str] = {}
    for command in ("title", "subtitle", "author", "institute", "date"):
        matches = re.findall(rf"(?m)^\\{command}\{{(.*)\}}$", main)
        if len(matches) != 1:
            return None
        values[command] = matches[0]
    return values


def _forbidden_body_definitions(content: str) -> list[dict]:
    forbidden = re.compile(
        r"\\(?:documentclass|usepackage|RequirePackage|newcommand|providecommand|DeclareRobustCommand|"
        r"NewDocumentCommand|RenewDocumentCommand|newenvironment|NewDocumentEnvironment|NewEnviron|"
        r"newtcolorbox|newcolumntype|DeclareMathOperator|definecolor|colorlet|def)\b"
    )
    return [
        {"line": line_number, "command": match.group(0)}
        for line_number, line in enumerate(content.splitlines(), start=1)
        for match in forbidden.finditer(line)
    ]


def _write_reports(project_dir: Path, blockers: list[dict], evidence: dict, lineage: dict) -> dict:
    validation = {
        "schema": "luceon.elegantbook-validation/v1",
        "status": "passed" if not blockers else "review",
        "gates": {
            "latex_project_schema_valid": not any(row["code"] in {
                "elegantbook_project_files_missing",
                "elegantbook_documentclass_missing",
                "elegantbook_template_fingerprint_mismatch",
                "elegantbook_locked_figure_fingerprint_mismatch",
                "elegantbook_locked_metadata_invalid",
                "elegantbook_locked_main_template_changed",
                "elegantbook_body_defines_custom_latex",
            } for row in blockers),
            "outline_content_and_lineage_invariants_preserved": not any(row["code"] in {"semantic_outline_not_preserved_in_latex", "latex_structural_headings_not_in_accepted_outline", "source_page_lineage_changed"} for row in blockers),
            "content_contains_no_private_use_ocr_residue": not any(row["code"] == "latex_private_use_characters" for row in blockers),
            "assets_are_local_and_traceable": not any(row["code"] in {"semantic_images_missing_from_latex", "latex_images_not_in_semantic_input", "project_uses_nonlocal_image_path", "project_images_missing"} for row in blockers),
            "candidate_compiles_reproducibly_in_texlive_2025": not any(row["code"] in {
                "texlive_2025_reproducible_compile_gate_failed",
                "latex_structured_diagnostics_missing",
                "latex_unresolved_reference_or_resource",
                "latex_missing_glyphs",
                "latex_obvious_overflow",
            } for row in blockers),
        },
        "evidence": evidence,
        "blockers": blockers,
    }
    (project_dir / "elegantbook-validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if lineage:
        (project_dir / "lineage.json").write_text(json.dumps(lineage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return validation


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_private_use(char: str) -> bool:
    codepoint = ord(char)
    return (
        0xE000 <= codepoint <= 0xF8FF
        or 0xF0000 <= codepoint <= 0xFFFFD
        or 0x100000 <= codepoint <= 0x10FFFD
    )
