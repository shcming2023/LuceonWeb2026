from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import fitz

from app.services.codex_workbook_repair import (
    choice_option_counts,
    duplicate_image_ocr_labels,
    missing_cloze_blank_numbers,
    missing_written_response_prompts,
    sentence_split_figures,
    translation_expression_items_without_space,
    unsafe_metadata_infoboxes,
)


LOW_TEXT_CHARS = 80
MAX_PAGE_EXPANSION_RATIO = 3.0
LANDSCAPE_PAGE_EXPANSION_RATIO = 3.5
LATE_CHAPTER_START_RATIO = 0.58
MIN_RENDER_IMAGE_BYTES = 1024
CHAPTER_HEADING_RE = re.compile(r"(?:第\s*\d+\s*章|Chapter\s+\d+\b)", re.IGNORECASE)
STRUCTURAL_DIVIDER_RE = re.compile(
    r"^(?:(?:第\s*\d+\s*章|\d+)\s*)?(?:SECTION|PART|UNIT|MODULE)\s+(?:\d+|[IVX]+)\s*[:：]",
    re.IGNORECASE,
)
MATH_OCR_RESIDUE_PATTERNS = {
    "exponent_wedge": re.compile(r"∧\s*\(?\s*\d"),
    "fraction_tuple": re.compile(r"\(\s*\d+\s*\)[ \t]*\([ \t]*[A-Za-z]+[ \t]*\)"),
    "radical_tuple": re.compile(r"\[\s*\d+\s*\]\("),
    "source_table_evidence": re.compile(r"source\s+table\s+evidence", re.IGNORECASE),
    "ocr_case_marker": re.compile(r"\(\s*l\s*\)"),
}


def build_print_quality_report(
    staging_dir: Path,
    compiled_pdf: Path,
    requirements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    requirements = requirements or {}
    issues: list[dict[str, Any]] = []
    try:
        document = fitz.open(compiled_pdf)
    except Exception as exc:
        return _report([], [{"code": "pdf_unreadable", "detail": str(exc)}], {})

    pages: list[dict[str, Any]] = []
    page_texts: list[str] = []
    for index, page in enumerate(document, start=1):
        text = page.get_text("text")
        page_texts.append(text)
        compact_chars = len(re.sub(r"\s+", "", text))
        repeated_one_items = sum(1 for line in text.splitlines() if re.match(r"^\s*1\.\s+", line))
        ungrouped_choices = _has_ungrouped_choice_matrix(text)
        layout = _page_layout_metrics(page)
        image_quality = _page_image_quality(page)
        structured_response_page = bool(
            (image_quality["max_image_area_ratio"] >= 0.08 and layout["writing_rule_count"] >= 3)
            or layout["writing_rule_count"] >= 3
            or (layout["writing_rule_count"] >= 2 and compact_chars >= 20)
        )
        math_ocr_residue = {
            name: len(pattern.findall(text))
            for name, pattern in MATH_OCR_RESIDUE_PATTERNS.items()
        }
        pages.append(
            {
                "page": index,
                "text_chars": compact_chars,
                "repeated_one_items": repeated_one_items,
                "ungrouped_choice_matrix": ungrouped_choices,
                "structured_response_page": structured_response_page,
                "ocr_placeholder_runs": len(re.findall(r"[({]{4,}|[)}]{4,}", text)),
                "math_ocr_residue": math_ocr_residue,
                **layout,
                **image_quality,
            }
        )
    document.close()

    for index, row in enumerate(pages):
        row["image_only_exercise_page"] = _is_image_only_exercise_page(pages, page_texts, index)

    page_count = len(pages)
    all_text = "\n".join(page_texts)
    low_text_pages = [
        row["page"]
        for row in pages[2:]
        if row["text_chars"] < LOW_TEXT_CHARS
        and not row["structured_response_page"]
        and not row["structural_divider_page"]
        and not row["image_only_exercise_page"]
        and not (
            row["page"] == page_count
            and row["text_chars"] >= 80
            and row["max_image_area_ratio"] >= 0.03
        )
        and not (
            row["text_chars"] >= 80
            and row["max_image_area_ratio"] >= 0.08
        )
        and not (
            row["text_chars"] >= 120
            and row["max_image_area_ratio"] >= 0.05
        )
        and not (
            row["text_chars"] >= 15
            and row["max_image_area_ratio"] >= 0.01
        )
    ]
    repeated_numbering_pages = [row["page"] for row in pages if row["repeated_one_items"] >= 8]
    ungrouped_choice_pages = [row["page"] for row in pages if row["ungrouped_choice_matrix"]]
    chapter_collision_pages = [row["page"] for row in pages if row["chapter_heading_collision"]]
    late_chapter_start_pages = [row["page"] for row in pages if row["late_chapter_start"]]
    low_resolution_image_pages = [row["page"] for row in pages if row["low_resolution_image_enlarged"]]
    if low_text_pages:
        _issue(issues, "low_text_or_orphan_pages", pages=low_text_pages)
    if repeated_numbering_pages:
        _issue(issues, "broken_list_numbering", pages=repeated_numbering_pages)
    if ungrouped_choice_pages:
        _issue(issues, "ungrouped_choice_matrix", pages=ungrouped_choice_pages)
    if chapter_collision_pages:
        _issue(issues, "chapter_heading_collision", pages=chapter_collision_pages)
    if late_chapter_start_pages:
        _issue(issues, "late_chapter_start", pages=late_chapter_start_pages)
    if low_resolution_image_pages:
        _issue(issues, "low_resolution_image_enlarged", pages=low_resolution_image_pages)

    residue_counts = {
        "qr_or_scan_prompt": len(
            re.findall(r"二维码|扫码|扫描上方|QR\s*code|scan (?:the |this )?code", all_text, re.IGNORECASE)
        ),
        "ai_image_caption": len(
            re.findall(r"no (?:visible )?text or symbols|no text or symbols", all_text, re.IGNORECASE)
        ),
        "source_brand_footer": len(re.findall(r"SHANGHAI STUDENTS['’] POST", all_text, re.IGNORECASE)),
        "ocr_placeholder_run": sum(row["ocr_placeholder_runs"] for row in pages),
        "test_string": len(re.findall(r"quick brown fox", all_text, re.IGNORECASE)),
        "markdown_image_syntax": len(re.findall(r"!\s*\[", all_text)),
        "editorial_image_description": len(re.findall(r"\bIllustration of\b", all_text, re.IGNORECASE)),
    }
    for key, count in residue_counts.items():
        allowed = 1 if key == "source_brand_footer" else 0
        if count > allowed:
            details: dict[str, Any] = {"count": count}
            if key == "ocr_placeholder_run":
                details["pages"] = [row["page"] for row in pages if row["ocr_placeholder_runs"]]
            _issue(issues, key, **details)
    math_ocr_pages = [
        row["page"]
        for row in pages
        if sum(row["math_ocr_residue"].values())
    ]
    if math_ocr_pages:
        totals = {
            name: sum(row["math_ocr_residue"][name] for row in pages)
            for name in MATH_OCR_RESIDUE_PATTERNS
        }
        _issue(issues, "math_ocr_residue", pages=math_ocr_pages, counts=totals)

    clean_markdown = _first_match(staging_dir, "clean.md", prefer="/body-final/")
    clean_text = _read_text(clean_markdown)
    metadata_units = len(re.findall(r"语篇类型", clean_text))
    outline_ledger = _read_json(staging_dir / "source_outline_ledger.json")
    ledger_items = outline_ledger.get("items") if isinstance(outline_ledger.get("items"), list) else []
    ledger_units = len(ledger_items)
    mapped_ledger_units = sum(
        1
        for row in ledger_items
        if isinstance(row, dict)
        and str(row.get("output_chapter") or "").strip()
        and str(row.get("status") or "").strip().lower() == "mapped"
    )
    try:
        minimum_expected_units = int(requirements.get("minimum_expected_units") or 0)
    except (TypeError, ValueError):
        minimum_expected_units = 0
    expected_units = max(metadata_units, ledger_units, minimum_expected_units)
    if minimum_expected_units and ledger_units < minimum_expected_units:
        _issue(
            issues,
            "source_outline_ledger_incomplete",
            required_units=minimum_expected_units,
            ledger_units=ledger_units,
        )
    if ledger_units and mapped_ledger_units < ledger_units:
        _issue(
            issues,
            "source_outline_mapping_incomplete",
            ledger_units=ledger_units,
            mapped_units=mapped_ledger_units,
        )
    content_tex = _content_tex(staging_dir)
    content_text = _read_text(content_tex)
    cleanlatex_input = _first_match(staging_dir, "input.tex", prefer="/02-cleanlatex/")
    cleanlatex_text = _read_text(cleanlatex_input)
    source_choice_counts = choice_option_counts(cleanlatex_text)
    refined_choice_counts = choice_option_counts(content_text)
    lost_choice_counts = {
        label: source_choice_counts[label] - refined_choice_counts[label]
        for label in "ABC"
        if refined_choice_counts[label] < source_choice_counts[label]
    }
    if lost_choice_counts:
        _issue(
            issues,
            "choice_options_lost",
            source=source_choice_counts,
            refined=refined_choice_counts,
            lost=lost_choice_counts,
        )
    unsafe_infoboxes = unsafe_metadata_infoboxes(content_text)
    if unsafe_infoboxes:
        _issue(issues, "metadata_infobox_unsafe_list", count=len(unsafe_infoboxes))
    cloze_numbering_issues = missing_cloze_blank_numbers(content_text)
    if cloze_numbering_issues:
        _issue(
            issues,
            "cloze_blank_numbers_missing",
            count=len(cloze_numbering_issues),
            sections=cloze_numbering_issues,
        )
    translation_items_missing_space = translation_expression_items_without_space(content_text)
    if translation_items_missing_space:
        _issue(
            issues,
            "translation_answer_space_missing",
            count=translation_items_missing_space,
        )
    split_figure_lines = sentence_split_figures(content_text)
    if expected_units >= 1 and split_figure_lines:
        _issue(issues, "figure_splits_sentence", lines=split_figure_lines)
    image_ocr_labels = duplicate_image_ocr_labels(content_text)
    if image_ocr_labels:
        _issue(issues, "duplicate_image_ocr_labels", count=len(image_ocr_labels))
    missing_written_surfaces = missing_written_response_prompts(content_text)
    if missing_written_surfaces:
        _issue(
            issues,
            "written_response_space_missing",
            count=len(missing_written_surfaces),
            prompts=missing_written_surfaces,
        )
    main_text = _read_text(staging_dir / "main.tex")
    unsafe_clearpage_count = len(
        re.findall(
            r"\\(?:let\s*\\(?:clearpage|cleardoublepage)\s*\\relax|"
            r"renewcommand\*?\s*\{?\\(?:clearpage|cleardoublepage)\}?\s*\{\s*\}|"
            r"def\s*\\(?:clearpage|cleardoublepage)\s*\{\s*\})",
            main_text,
        )
    )
    if unsafe_clearpage_count:
        _issue(issues, "unsafe_page_flush_suppression", count=unsafe_clearpage_count)
    chapter_count = len(re.findall(r"\\chapter\*?\s*\{", content_text))
    if expected_units >= 2 and chapter_count < expected_units:
        _issue(
            issues,
            "outline_coverage_incomplete",
            expected_units=expected_units,
            rendered_chapters=chapter_count,
        )

    source_anchor_rows = _source_tail_anchors(clean_text)
    normalized_pdf_text = _normalize_anchor(all_text)
    missing_source_anchors = [
        row["title"]
        for row in source_anchor_rows
        if not any(window in normalized_pdf_text for window in row["windows"])
    ]
    if missing_source_anchors:
        _issue(
            issues,
            "source_tail_anchor_missing",
            checked_units=len(source_anchor_rows),
            units=missing_source_anchors,
        )

    source_pdf = _first_source_pdf(staging_dir, compiled_pdf)
    source_pages = _pdf_page_count(source_pdf)
    expansion_ratio = round(page_count / source_pages, 3) if source_pages else None
    expansion_limit = _page_expansion_limit(source_pdf)
    if expansion_ratio and expansion_ratio > expansion_limit:
        _issue(
            issues,
            "page_expansion_suspicious",
            source_pages=source_pages,
            output_pages=page_count,
            ratio=expansion_ratio,
            limit=expansion_limit,
        )

    polish_report = _read_json(staging_dir / "latex_polish_report.json")
    after = polish_report.get("after") if isinstance(polish_report.get("after"), dict) else {}
    reported_answer_spaces = int(after.get("print_answer_space_blocks") or 0)
    rendered_answer_spaces = len(
        re.findall(
            r"\\(?:workbookanswerspace|printshortanswer|printmediumanswer|printlonganswer|"
            r"printlistanswer|printwritingbox|printchapterendwritingbox)\b",
            content_text,
        )
    )
    answer_space_blocks = max(reported_answer_spaces, rendered_answer_spaces)
    writing_prompt_count = len(
        re.findall(
            r"translate the following|translate the sentences|according to the chinese instructions|explain why|write (?:a|an|your)|complete the table",
            all_text,
            re.IGNORECASE,
        )
    )
    if expected_units >= 1 and writing_prompt_count >= 3 and answer_space_blocks == 0:
        _issue(
            issues,
            "print_answer_space_missing",
            writing_prompts=writing_prompt_count,
            added_answer_spaces=answer_space_blocks,
        )

    page_review = _read_json_value(staging_dir / "page_review.json")
    if isinstance(page_review, list):
        reviewed_rows = page_review
    elif isinstance(page_review, dict) and isinstance(page_review.get("pages"), list):
        reviewed_rows = page_review["pages"]
    elif isinstance(page_review, dict) and isinstance(page_review.get("records"), list):
        reviewed_rows = page_review["records"]
    else:
        reviewed_rows = []
    compiled_sha256 = _sha256(compiled_pdf)
    review_pdf_sha256 = str(page_review.get("pdf_sha256") or "").strip() if isinstance(page_review, dict) else ""
    try:
        review_page_count = int(page_review.get("page_count") or 0) if isinstance(page_review, dict) else 0
    except (TypeError, ValueError):
        review_page_count = 0
    if review_pdf_sha256 != compiled_sha256 or review_page_count != page_count:
        _issue(
            issues,
            "page_review_provenance_mismatch",
            expected_pdf_sha256=compiled_sha256,
            reported_pdf_sha256=review_pdf_sha256,
            expected_page_count=page_count,
            reported_page_count=review_page_count,
        )
    reviewed_pages: set[int] = set()
    missing_render_pages: list[int] = []
    invalid_render_pages: list[int] = []
    failed_review_pages: list[int] = []
    for row in reviewed_rows:
        if not isinstance(row, dict):
            continue
        try:
            page_number = int(row.get("page"))
        except (TypeError, ValueError):
            continue
        reviewed_pages.add(page_number)
        image_value = str(row.get("image") or "").strip()
        image_path = Path(image_value)
        if not image_path.is_absolute():
            image_path = staging_dir / image_path
        if not image_value or not image_path.is_file():
            missing_render_pages.append(page_number)
        elif not _valid_render_image(image_path):
            invalid_render_pages.append(page_number)
        if str(row.get("status") or "").lower() != "passed":
            failed_review_pages.append(page_number)
    expected_page_numbers = set(range(1, page_count + 1))
    if reviewed_pages != expected_page_numbers or missing_render_pages:
        _issue(
            issues,
            "full_page_visual_review_missing",
            reviewed=len(reviewed_pages),
            expected=page_count,
            missing_pages=sorted(expected_page_numbers - reviewed_pages),
            missing_render_pages=sorted(set(missing_render_pages)),
        )
    if invalid_render_pages:
        _issue(issues, "rendered_page_image_invalid", pages=sorted(set(invalid_render_pages)))
    if failed_review_pages:
        _issue(issues, "page_visual_review_failed", pages=sorted(set(failed_review_pages)))

    metrics = {
        "output_pages": page_count,
        "source_pages": source_pages,
        "page_expansion_ratio": expansion_ratio,
        "low_text_pages": low_text_pages,
        "repeated_numbering_pages": repeated_numbering_pages,
        "ungrouped_choice_pages": ungrouped_choice_pages,
        "chapter_collision_pages": chapter_collision_pages,
        "late_chapter_start_pages": late_chapter_start_pages,
        "low_resolution_image_pages": low_resolution_image_pages,
        "residue_counts": residue_counts,
        "math_ocr_residue_pages": math_ocr_pages,
        "unsafe_page_flush_suppression_count": unsafe_clearpage_count,
        "expected_units": expected_units,
        "metadata_units": metadata_units,
        "outline_ledger_units": ledger_units,
        "mapped_outline_units": mapped_ledger_units,
        "rendered_chapters": chapter_count,
        "source_choice_option_counts": source_choice_counts,
        "refined_choice_option_counts": refined_choice_counts,
        "lost_choice_option_counts": lost_choice_counts,
        "unsafe_metadata_infoboxes": len(unsafe_infoboxes),
        "cloze_numbering_issues": cloze_numbering_issues,
        "translation_items_without_answer_space": translation_items_missing_space,
        "sentence_split_figure_lines": split_figure_lines,
        "source_anchor_units_checked": len(source_anchor_rows),
        "source_anchor_units_missing": missing_source_anchors,
        "writing_prompt_count": writing_prompt_count,
        "added_answer_space_blocks": answer_space_blocks,
        "duplicate_image_ocr_label_runs": len(image_ocr_labels),
        "written_response_prompts_without_space": missing_written_surfaces,
        "reviewed_pages": len(reviewed_pages),
        "compiled_pdf_sha256": compiled_sha256,
    }
    return _report(pages, issues, metrics)


def _report(pages: list[dict[str, Any]], issues: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "luceon-worker-print-quality/v1",
        "status": "passed" if not issues else "blocked",
        "hard_blockers": issues,
        "metrics": metrics,
        "pages": pages,
    }


def _issue(issues: list[dict[str, Any]], code: str, **details: Any) -> None:
    issues.append({"code": code, **details})


def _has_ungrouped_choice_matrix(text: str) -> bool:
    labels: list[tuple[int, str]] = []
    for index, line in enumerate(text.splitlines()):
        match = re.match(r"^\s*(?:\d+\.\s*)?([ABC])\.\s+", line)
        if match:
            labels.append((index, match.group(1)))
    positions = {label: [index for index, value in labels if value == label] for label in "ABC"}
    if min((len(positions[label]) for label in "ABC"), default=0) < 4:
        return False
    return max(positions["A"]) < min(positions["B"]) and max(positions["B"]) < min(positions["C"])


def _page_layout_metrics(page: fitz.Page) -> dict[str, Any]:
    lines: list[dict[str, Any]] = []
    for block in page.get_text("dict", sort=True).get("blocks", []):
        for line in block.get("lines", []):
            text = "".join(str(span.get("text") or "") for span in line.get("spans", [])).strip()
            if text:
                maximum_font_size = max((float(span.get("size") or 0) for span in line.get("spans", [])), default=0)
                lines.append({"text": text, "bbox": fitz.Rect(line["bbox"]), "maximum_font_size": maximum_font_size})
    heading_rows = [
        row
        for row in lines
        if row["maximum_font_size"] >= 14 and CHAPTER_HEADING_RE.search(row["text"])
    ]
    collision = False
    for heading in heading_rows:
        for other in lines:
            if other is heading or CHAPTER_HEADING_RE.search(other["text"]):
                continue
            vertical_overlap = min(heading["bbox"].y1, other["bbox"].y1) - max(heading["bbox"].y0, other["bbox"].y0)
            horizontal_overlap = min(heading["bbox"].x1, other["bbox"].x1) - max(heading["bbox"].x0, other["bbox"].x0)
            if vertical_overlap > 2 and horizontal_overlap > 2 and len(re.sub(r"\s+", "", other["text"])) >= 3:
                collision = True
                break
        if collision:
            break
    heading_y = min((row["bbox"].y0 for row in heading_rows), default=None)
    structural_divider_page = len(lines) <= 4 and any(
        row["maximum_font_size"] >= 16 and STRUCTURAL_DIVIDER_RE.search(row["text"])
        for row in lines
    )
    writing_rule_count = _writing_rule_count(page)
    return {
        "chapter_heading_collision": collision,
        "chapter_heading_y": round(heading_y, 2) if heading_y is not None else None,
        "late_chapter_start": bool(heading_y is not None and heading_y / page.rect.height > LATE_CHAPTER_START_RATIO),
        "structural_divider_page": structural_divider_page,
        "writing_rule_count": writing_rule_count,
    }


def _is_image_only_exercise_page(pages: list[dict[str, Any]], page_texts: list[str], index: int) -> bool:
    row = pages[index]
    if row.get("text_chars", 0) > 15 or row.get("max_image_area_ratio", 0) < 0.08:
        return False
    visible_lines = [line.strip() for line in page_texts[index].splitlines() if line.strip()]
    if visible_lines and re.match(r"^\d+(?:\.\d+)*\s+\d+\s+.{1,24}$", visible_lines[0]):
        visible_lines.pop(0)
    if visible_lines and re.fullmatch(r"\d{1,4}", visible_lines[-1]):
        visible_lines.pop()
    visible = re.sub(r"\s+", "", " ".join(visible_lines))
    if visible and not re.fullmatch(r"[0-9A-Za-z.,()]+", visible):
        return False
    context = "\n".join(page_texts[max(0, index - 2) : index + 1])
    return bool(
        re.search(
            r"(?:look\s+at\s+the\s+pictures?|write\s+[^.\n]{0,80}\s+for\s+each\s+picture|complete\s+the\s+picture\s+exercise|(?:solve|illustrate)\s+[^.\n]{0,100}\s+graphically|(?:draw|sketch|plot)\s+[^.\n]{0,100}\s+(?:graph|coordinate\s+grid)|选择|下列[^。\n]{0,30}(?:图形|图)|下面[^。\n]{0,30}(?:图形|图)|观察[^。\n]{0,30}(?:图形|图))",
            context,
            re.IGNORECASE,
        )
    )


def _writing_rule_count(page: fitz.Page) -> int:
    count = 0
    minimum_width = page.rect.width * 0.5
    for drawing in page.get_drawings():
        for item in drawing.get("items", []):
            if not item or item[0] != "l":
                continue
            start, end = item[1], item[2]
            if abs(start.y - end.y) <= 1 and abs(start.x - end.x) >= minimum_width:
                count += 1
    return count


def _page_image_quality(page: fitz.Page) -> dict[str, Any]:
    page_area = page.rect.width * page.rect.height
    maximum_area_ratio = 0.0
    minimum_effective_dpi: float | None = None
    low_resolution_enlarged = False
    for info in page.get_image_info(xrefs=True):
        bbox = fitz.Rect(info.get("bbox") or (0, 0, 0, 0))
        if bbox.width <= 0 or bbox.height <= 0:
            continue
        area_ratio = bbox.get_area() / page_area
        if area_ratio < 0.01:
            continue
        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        if width <= 0 or height <= 0:
            continue
        effective_dpi = min(width / (bbox.width / 72), height / (bbox.height / 72))
        maximum_area_ratio = max(maximum_area_ratio, area_ratio)
        minimum_effective_dpi = effective_dpi if minimum_effective_dpi is None else min(minimum_effective_dpi, effective_dpi)
        if area_ratio >= 0.25 and effective_dpi < 100:
            low_resolution_enlarged = True
    return {
        "max_image_area_ratio": round(maximum_area_ratio, 3),
        "min_effective_image_dpi": round(minimum_effective_dpi, 1) if minimum_effective_dpi is not None else None,
        "low_resolution_image_enlarged": low_resolution_enlarged,
    }


def _source_tail_anchors(clean_text: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"(?m)^#\s+(.+?)\s*$", clean_text))
    rows: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(clean_text)
        candidates: list[str] = []
        for raw_line in clean_text[match.end() : body_end].splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("<!--", "![", "*", "<", "语篇类型", "范畴:", "教材链接:")):
                continue
            if re.match(r"^(?:[A-G]\.|\d+\.\s*_*$|#{1,6}\s)", line):
                continue
            for fragment in re.split(r"_{2,}\d*_{2,}", line):
                english_words = re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)?", fragment)
                normalized = _normalize_anchor(fragment)
                if len(english_words) >= 8 and len(normalized) >= 45:
                    candidates.append(normalized)
        if not candidates:
            continue
        anchor = candidates[-1]
        windows = [anchor[offset : offset + 48] for offset in range(0, len(anchor), 40) if len(anchor[offset : offset + 48]) >= 36]
        if windows:
            rows.append({"title": match.group(1).strip(), "windows": windows})
    return rows


def _normalize_anchor(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    return "".join(character for character in value if character.isalnum() or "\u4e00" <= character <= "\u9fff")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_render_image(path: Path) -> bool:
    try:
        if path.stat().st_size < MIN_RENDER_IMAGE_BYTES:
            return False
        header = path.read_bytes()[:12]
    except OSError:
        return False
    return header.startswith(b"\x89PNG\r\n\x1a\n") or header.startswith(b"\xff\xd8\xff")


def _first_match(root: Path, name: str, *, prefer: str = "") -> Path | None:
    rows = [path for path in root.rglob(name) if path.is_file()]
    if prefer:
        preferred = [path for path in rows if prefer in path.as_posix()]
        if preferred:
            rows = preferred
    return sorted(rows, key=lambda path: (len(path.parts), path.as_posix()))[0] if rows else None


def _content_tex(staging_dir: Path) -> Path | None:
    report = _read_json(staging_dir / "latex_polish_report.json")
    project_dir = str(report.get("project_dir") or "").strip()
    if project_dir:
        candidate = staging_dir / project_dir / "chapters" / "content.tex"
        if candidate.is_file():
            return candidate
    return _first_match(staging_dir, "content.tex", prefer="/project/chapters/")


def _first_source_pdf(staging_dir: Path, compiled_pdf: Path) -> Path | None:
    source_dir = staging_dir / "inputs" / "source"
    rows = [path for path in source_dir.glob("*.pdf") if path.is_file() and path != compiled_pdf]
    return sorted(rows)[0] if rows else None


def _pdf_page_count(path: Path | None) -> int | None:
    if not path:
        return None
    try:
        document = fitz.open(path)
        count = len(document)
        document.close()
        return count
    except Exception:
        return None


def _page_expansion_limit(path: Path | None) -> float:
    if not path or not path.is_file():
        return MAX_PAGE_EXPANSION_RATIO
    try:
        document = fitz.open(path)
    except Exception:
        return MAX_PAGE_EXPANSION_RATIO
    try:
        content_pages = [page for index, page in enumerate(document) if index >= 2]
        if not content_pages:
            content_pages = list(document)
        landscape = sum(1 for page in content_pages if page.rect.width > page.rect.height)
        return LANDSCAPE_PAGE_EXPANSION_RATIO if landscape > len(content_pages) / 2 else MAX_PAGE_EXPANSION_RATIO
    finally:
        document.close()


def _read_text(path: Path | None) -> str:
    if not path:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    value = _read_json_value(path)
    return value if isinstance(value, dict) else {}


def _read_json_value(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
