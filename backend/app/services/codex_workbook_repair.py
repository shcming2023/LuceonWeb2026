from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import fitz


MATRIX_BLOCKER = "ungrouped_choice_matrix"
IMAGE_BLOCKERS = {"low_resolution_image_enlarged", "low_text_or_orphan_pages"}
CONTENT_CLEANUP_BLOCKERS = {
    "cloze_blank_numbers_missing",
    "duplicate_image_ocr_labels",
    "figure_splits_sentence",
    "metadata_infobox_unsafe_list",
    "translation_answer_space_missing",
    "written_response_space_missing",
    "print_answer_space_missing",
    "qr_or_scan_prompt",
}
NUMBERING_BLOCKER = "broken_list_numbering"
ANSWER_SURFACE_RE = re.compile(
    r"\\(?:workbookanswerspace|printanswerline|printshortanswer|printmediumanswer|printlonganswer|"
    r"printlistanswer|printwritingbox|printchapterendwritingbox)\b"
)
A_OPTION_RE = re.compile(
    r"^\s*\\par\s*\\Needspace\{[^}]+\}\s*\\noindent\s*"
    r"\\textbf\{(\d+)\.\}\s*A\.\s*(.*?)\\par\s*$"
)
INLINE_A_OPTION_RE = re.compile(r"^\s*(\d+)\.\s*A\.\s*(.+?)\s*$")
PLAIN_OPTION_RE = re.compile(r"^\s*([B-D])\.\s*(.+?)\s*$")
INCLUDEGRAPHICS_RE = re.compile(
    r"\\includegraphics\[(?P<options>[^]]*)\]\{(?P<path>[^}]+)\}"
)
FIGURE_OCR_LABEL_RE = re.compile(
    r"(?P<figure>\\end\{figure\})(?P<gap>\s*)\\emph\{(?P<labels>[^{}\n]{120,})\}"
)
WRITING_PROMPT_RE = re.compile(
    r"(?is)(Give\b.{0,140}?\bat least\s+(?:[A-Za-z]+|\d+)\s+"
    r"(?:pieces? of advice|reasons?|sentences?|examples?)\.)"
)
METADATA_ITEM_RE = re.compile(r"^\\item\[\\textbf\{([^{}]+)\}\]\s*(.*?)\s*$")
METADATA_TAIL_RE = re.compile(r"^(范畴|范围|教材链接)\s*[:：]\s*(.*?)\s*$")
READING_PROFILE_LIST_BEGIN = r"\begin{description}[leftmargin=0pt,labelindent=0pt]"
CLOZE_SECTION_RE = re.compile(
    r"(?P<header>\\exerciseheading\{[^{}\n]*Choose the best words? or phrases?[^{}\n]*\})"
    r"(?P<body>.*?)(?=\\begin\{vocabbox\}|\\exerciseheading\{|\\chapter\{|\Z)",
    re.I | re.S,
)
CLOZE_BLANK_RE = re.compile(
    r"\\rule\{2\.0em\}\{0\.4pt\}(?:(?P<number>\d+)\\rule\{2\.0em\}\{0\.4pt\})?"
)
TRANSLATION_SECTION_RE = re.compile(
    r"(?P<header>\\exerciseheading\{[^{}\n]*(?:Translate the following expressions from English to Chinese|Translate the sentences according to the Chinese)[^{}\n]*\})"
    r"(?P<body>.*?)(?=\\exerciseheading\{|\\chapter\{|\Z)",
    re.I | re.S,
)
TRANSLATION_ANSWER_POSITION_RE = re.compile(
    r"(?P<end>\\end\{enumerate\})\s*\\printshortanswer(?P<tail>.*?)(?=\\begin\{enumerate\}|\Z)",
    re.S,
)
NUMBERED_PAR_LINE_RE = re.compile(
    r"^\s*\\par\\Needspace\{[^}]+\}\\noindent\\textbf\{\d+\.\}.*\\par\s*$"
)
CHOICE_LABEL_RE = re.compile(r"(?m)(?:^|\b\d+\.\s+|\\\\)\s*([ABC])\.\s+(?=\S)")
WIDTH_RE = re.compile(r"^\s*width\s*=\s*(0?\.\d+)\\textwidth\s*$")
HEIGHT_RE = re.compile(r"^\s*height\s*=")
FIGURE_BLOCK_RE = re.compile(r"\\begin\{figure\}\[H\].*?\\end\{figure\}\s*", re.S)
CAPTION_RE = re.compile(r"\\caption\{([^{}]*)\}")
NESTED_FIGURE_RE = re.compile(
    r"\\begin\{figure\}\[H\](?P<outer>(?:(?!\\begin\{figure\}|\\end\{figure\}|\\chapter\{).)*?\\caption\{(?P<caption>[^{}]*)\}\s*)"
    r"(?P<inner>\\begin\{figure\}\[H\].*?\\end\{figure\})\s*\\end\{figure\}",
    re.S,
)
QR_MARKETING_RE = re.compile(r"二维码|扫码|订购|微信|音源|语音|习题答案|日.{0,4}上方|[二三][维道目重直][码同可直]", re.I)
OPTION_ANSWER_SPACE_RE = re.compile(
    r"(?P<block>\\begin\{enumerate\}\s*(?:\\setcounter\{enumi\}\{\d+\}\s*)?\\item\s+A\.?\s+.*?\\end\{enumerate\})\s*\\printshortanswer\s*",
    re.S,
)
OCR_BLANK_PLACEHOLDER_RE = re.compile(r"\\_(\d+)\s+(?:\\\{){5}\\ensuremath\{\{\}_([A-Za-z][A-Za-z-]*)\}")
OCR_OPTION_PLACEHOLDER_RE = re.compile(r"(?m)^(\d+)\.\s+(?:\\\{){5}\\ensuremath\{\{\}_([A-D])\}\s*\.\s*")
OCR_NUMBERED_NAME_PLACEHOLDER_RE = re.compile(
    r"(?m)^(?P<prefix>(?:\\item\s+)?-?\s*\d+)\s+(?:\\\{){5}\\ensuremath\{\{\}_(?P<name>[A-Za-z][A-Za-z -]*)\}"
)
SINGLE_ANSWER_BLOCK_RE = re.compile(
    r"\\begin\{enumerate\}\s*(?:\\setcounter\{enumi\}\{(?P<counter>\d+)\}\s*)?"
    r"\\item\s+\\rule\{2\.0em\}\{0\.4pt\}\s*\\end\{enumerate\}"
)
ANSWER_INDEX_RUN_RE = re.compile(
    r"(?P<run>(?:(?:\\begin\{enumerate\}\s*(?:\\setcounter\{enumi\}\{\d+\}\s*)?"
    r"\\item\s+\\rule\{2\.0em\}\{0\.4pt\}\s*\\end\{enumerate\}|\d+\.)\s*){3,})"
    r"(?=\\chapter\{|% source_page_idx:|\Z)",
    re.S,
)
DETACHED_TRANSLATION_COMPLETION_RE = re.compile(
    r"(?P<head>\\begin\{enumerate\}\s*(?:\\setcounter\{enumi\}\{\d+\}\s*)?"
    r"\\item\s+[^\n]+\n(?:\([^\n]+\)\s*)?)"
    r"\\end\{enumerate\}\s*(?P<completion>[A-Za-z][^\n]{8,180}[.!?])"
    r"(?P<tail>\s*(?:% source_page_idx:|\\chapter\{|\Z))",
    re.S,
)
EMBEDDED_EXERCISE_HEADING_RE = re.compile(
    r"^(?:I|II|III|IV|V|VI)\.\s+(?:Translate|Answer|Complete|Choose|Write|Match|Fill)\b.+$",
    re.I,
)
SOURCE_TABLE_EVIDENCE_RE = re.compile(
    r"\{\\(?:small|scriptsize)\b.*?\\begingroup\b.*?"
    r"source table evidence.*?\\endgroup\s*\}",
    re.I | re.S,
)
DEBUG_NUMBER_MARKER_RE = re.compile(
    r"\\par\\begingroup\\small\\ttfamily\\raggedright\s*"
    r"\(\s*\(\s*\(\s*\d+\.\s*\)\s*\)\s*\)\\par\s*\\endgroup\s*",
    re.S,
)
TTFAMILY_PROSE_RE = re.compile(
    r"\\par\\begingroup\\small\\ttfamily\\raggedright\s*(?P<body>.*?)\\par\s*\\endgroup",
    re.S,
)
OCR_PAREN_BLANK_RE = re.compile(r"\\_(\d+)\s+(?:\(\)){3,}\\_")
PRIVATE_USE_CLOZE_RE = re.compile(
    r"[\ue000-\uf8ff]\d+\\rule\{2\.0em\}\{0\.4pt\}(\d+)[\ue000-\uf8ff]"
)


class WorkbookRepairError(RuntimeError):
    pass


def repair_staging_candidate(staging_dir: Path) -> dict[str, Any]:
    staging_dir = staging_dir.resolve()
    project_dir = find_staging_project(staging_dir)
    quality_report = _read_json(staging_dir / "worker_quality_report.json")
    blockers = {
        str(row.get("code") or "")
        for row in quality_report.get("hard_blockers", [])
        if isinstance(row, dict)
    }
    report = repair_workbook_project(project_dir, requested_blockers=blockers or None)
    report["staging_dir"] = str(staging_dir)
    report["worker_blockers"] = sorted(blockers)
    report_path = staging_dir / "deterministic_repair_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def repair_workbook_project(
    project_dir: Path,
    *,
    requested_blockers: set[str] | None = None,
) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    content_path = project_dir / "chapters" / "content.tex"
    if not content_path.is_file():
        raise WorkbookRepairError(f"LaTeX content file not found: {content_path}")

    original = content_path.read_text(encoding="utf-8")
    source_before = _invariants(original)
    text = original
    text, misplaced_option_spaces_removed = remove_option_answer_spaces(text)
    text, ocr_placeholders_repaired = repair_ocr_placeholder_runs(text)
    text, embedded_headings_promoted = promote_embedded_exercise_headings(text)
    text, source_evidence_blocks_removed = SOURCE_TABLE_EVIDENCE_RE.subn("", text)
    text, debug_number_markers_removed = DEBUG_NUMBER_MARKER_RE.subn("", text)
    text, accidental_math_prose_unwrapped = unwrap_accidental_math_prose(text)
    text, ocr_parenthesis_blanks_repaired = repair_ocr_parenthesis_blanks(text)
    text, private_use_cloze_blanks_repaired = repair_private_use_cloze_blanks(text)
    text, answer_index_runs_compacted = compact_answer_index_runs(text)
    text, prechapter_answer_lines_compacted = compact_prechapter_answer_lines(text)
    text, prechapter_figures_compacted = compact_prechapter_figures(text)
    text, prechapter_dialogue_tails_compacted = compact_prechapter_dialogue_tails(text)
    text, duplicate_long_captions_removed = remove_duplicate_long_captions(text)
    text, known_ocr_tokens_repaired = normalize_known_ocr_tokens(text)
    text, detached_translation_completions_repaired = repair_detached_translation_completions(text)
    text, plain_section_labels_normalized = normalize_plain_section_labels(text)
    text, orphan_translation_pages_compacted = compact_known_orphan_translation_page(text)
    text, prechapter_translation_tails_compacted = compact_prechapter_translation_tails(text)
    before = _invariants(text)
    protected_answer_surfaces_outside_translation = _answer_surfaces_outside_translation(text)
    matrix_rows: list[dict[str, Any]] = []
    image_rows: list[dict[str, Any]] = []
    content_cleanup_rows: list[dict[str, Any]] = []
    written_response_rows: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    cloze_rows: list[dict[str, Any]] = []
    translation_rows: list[dict[str, Any]] = []
    sentence_figure_rows: list[dict[str, Any]] = []
    word_bank_rows: list[dict[str, Any]] = []
    qr_rows: list[dict[str, Any]] = []
    numbering_rows: list[dict[str, Any]] = []

    if requested_blockers is None or MATRIX_BLOCKER in requested_blockers:
        text, matrix_rows = regroup_choice_matrices(text)
    text, inline_matrix_rows = regroup_inline_column_options(text)
    matrix_rows.extend(inline_matrix_rows)
    if requested_blockers is None or requested_blockers.intersection(IMAGE_BLOCKERS):
        text, image_rows = cap_low_resolution_images(text, project_dir)
    text, qr_rows = remove_qr_marketing_figures(text, project_dir)
    text, qr_ocr_residue_removed = remove_qr_ocr_residue(text)
    text = remove_generic_image_captions(text)
    if requested_blockers is None or NUMBERING_BLOCKER in requested_blockers:
        text, numbering_rows = normalize_exercise_numbering(text)
    if requested_blockers is None or requested_blockers.intersection(CONTENT_CLEANUP_BLOCKERS):
        text, metadata_rows = normalize_metadata_infoboxes(text)
        text, sentence_figure_rows = repair_sentence_split_figures(text)
        text, cloze_rows = restore_cloze_blank_numbers(text)
        text, translation_rows = add_translation_expression_answer_spaces(text)
        text, word_bank_rows = format_simple_word_banks(text)
        text, content_cleanup_rows = clean_image_ocr_labels(text)
        text, written_response_rows = add_written_response_spaces(text)

    after = _invariants(text)
    for key in ("chapters", "exercise_headings"):
        if before[key] != after[key]:
            raise WorkbookRepairError(
                f"Repair changed protected invariant {key}: {before[key]} -> {after[key]}"
            )
    after_outside_translation = _answer_surfaces_outside_translation(text)
    expected_outside_translation = (
        protected_answer_surfaces_outside_translation
        + sum(1 for row in content_cleanup_rows if row.get("answer_surface_added"))
        + len(written_response_rows)
    )
    if after_outside_translation != expected_outside_translation:
        raise WorkbookRepairError(
            "Repair changed answer surfaces outside the allowed operations: "
            f"expected {expected_outside_translation}, got {after_outside_translation}"
        )
    translation_answer_spaces_added = max(
        0,
        (after["answer_surfaces"] - before["answer_surfaces"])
        - (after_outside_translation - protected_answer_surfaces_outside_translation),
    )

    changed = text != original
    if changed:
        content_path.write_text(text, encoding="utf-8")
    answer_macros_added = ensure_answer_surface_macros(project_dir, text)
    project_metadata_repairs = sanitize_project_metadata(project_dir)
    return {
        "schema": "luceon-codex-workbook-repair/v1",
        "status": "changed" if changed else "unchanged",
        "project_dir": str(project_dir),
        "content_path": str(content_path),
        "requested_blockers": sorted(requested_blockers or []),
        "before_sha256": _text_sha256(original),
        "after_sha256": _text_sha256(text),
        "before": before,
        "source_before": source_before,
        "after": after,
        "choice_matrices_regrouped": len(matrix_rows),
        "choice_matrices": matrix_rows,
        "low_resolution_images_capped": len(image_rows),
        "images": image_rows,
        "metadata_infoboxes_normalized": len(metadata_rows),
        "metadata_infoboxes": metadata_rows,
        "sentence_split_figures_repaired": len(sentence_figure_rows),
        "sentence_split_figures": sentence_figure_rows,
        "cloze_blank_numbers_restored": sum(len(row["restored_numbers"]) for row in cloze_rows),
        "cloze_sections": cloze_rows,
        "translation_answer_spaces_added": translation_answer_spaces_added,
        "translation_sections": translation_rows,
        "word_banks_formatted": len(word_bank_rows),
        "word_banks": word_bank_rows,
        "duplicate_image_ocr_labels_removed": len(content_cleanup_rows),
        "content_cleanups": content_cleanup_rows,
        "written_response_spaces_added": len(written_response_rows),
        "written_response_spaces": written_response_rows,
        "qr_marketing_figures_removed": len(qr_rows),
        "qr_marketing_figures": qr_rows,
        "qr_ocr_residue_lines_removed": qr_ocr_residue_removed,
        "exercise_numbering_blocks_fixed": len(numbering_rows),
        "exercise_numbering": numbering_rows,
        "answer_surface_macros_added": answer_macros_added,
        "misplaced_option_answer_spaces_removed": misplaced_option_spaces_removed,
        "ocr_placeholder_runs_repaired": ocr_placeholders_repaired,
        "embedded_exercise_headings_promoted": embedded_headings_promoted,
        "source_table_evidence_blocks_removed": source_evidence_blocks_removed,
        "debug_number_markers_removed": debug_number_markers_removed,
        "accidental_math_prose_unwrapped": accidental_math_prose_unwrapped,
        "ocr_parenthesis_blanks_repaired": ocr_parenthesis_blanks_repaired,
        "private_use_cloze_blanks_repaired": private_use_cloze_blanks_repaired,
        "answer_index_runs_compacted": answer_index_runs_compacted,
        "prechapter_answer_lines_compacted": prechapter_answer_lines_compacted,
        "prechapter_dialogue_tails_compacted": prechapter_dialogue_tails_compacted,
        "prechapter_figures_compacted": prechapter_figures_compacted,
        "duplicate_long_captions_removed": duplicate_long_captions_removed,
        "known_ocr_tokens_repaired": known_ocr_tokens_repaired,
        "detached_translation_completions_repaired": detached_translation_completions_repaired,
        "plain_section_labels_normalized": plain_section_labels_normalized,
        "orphan_translation_pages_compacted": orphan_translation_pages_compacted,
        "prechapter_translation_tails_compacted": prechapter_translation_tails_compacted,
        "project_metadata_repairs": project_metadata_repairs,
    }


def ensure_answer_surface_macros(project_dir: Path, content: str) -> list[str]:
    main_path = project_dir / "main.tex"
    if not main_path.is_file():
        return []
    main = main_path.read_text(encoding="utf-8")
    old_short_definition = r"\providecommand{\printshortanswer}{\par\noindent\rule{\linewidth}{0.4pt}\par\vspace{0.7\baselineskip}}"
    definitions = {
        "printshortanswer": r"\providecommand{\printshortanswer}{\par\noindent\rule{\linewidth}{0.4pt}\par\vspace{0.2\baselineskip}}",
        "printlonganswer": r"\providecommand{\printlonganswer}{\par\noindent\rule{\linewidth}{0.4pt}\par\vspace{3\baselineskip}}",
    }
    additions = []
    added_names = []
    if old_short_definition in main:
        main = main.replace(old_short_definition, definitions["printshortanswer"])
        added_names.append("printshortanswer_compacted")
    if r"\Needspace" in content and not re.search(r"\\usepackage(?:\[[^]]*\])?\{needspace\}", main):
        additions.append(r"\usepackage{needspace}")
        added_names.append("needspace_package")
    for name, definition in definitions.items():
        if rf"\{name}" in content and not re.search(rf"\\(?:providecommand|newcommand)\s*\{{\\{name}\}}", main):
            additions.append(definition)
            added_names.append(name)
    if not additions and not added_names:
        return []
    marker = r"\begin{document}"
    insertion = "\n".join(additions) + ("\n" if additions else "")
    if additions:
        main = main.replace(marker, insertion + marker, 1) if marker in main else main + "\n" + insertion
    main_path.write_text(main, encoding="utf-8")
    return added_names


def sanitize_project_metadata(project_dir: Path) -> list[str]:
    main_path = project_dir / "main.tex"
    if not main_path.is_file():
        return []
    main = main_path.read_text(encoding="utf-8")
    original = main
    main = main.replace(r"\subtitle{Worker V2 candidate}", r"\subtitle{课堂主题精读与练习}")
    main = main.replace(r"\author{Luceon}", r"\author{}")
    main = main.replace(r"\date{\today}", r"\date{}")
    main = main.replace(r"\version{Reviewed}", r"\version{}")
    main = main.replace("Worker V2 candidate", "课堂主题精读与练习")
    main = re.sub(
        r"\{\\normalsize\\color\{gray\}\s*\\begin\{tabular\}\{l\}.*?\\end\{tabular\}\}",
        "",
        main,
        flags=re.S,
    )
    title_match = re.search(r"\\title\{([^{}]+)\}", main)
    if title_match and title_match.group(1).lower().endswith(".pdf"):
        main = main.replace(title_match.group(1), title_match.group(1)[:-4])
    display_title = title_match.group(1)[:-4] if title_match and title_match.group(1).lower().endswith(".pdf") else (title_match.group(1) if title_match else "")
    if display_title and "-" in display_title:
        first_line, second_line = display_title.rsplit("-", 1)
        main = main.replace(
            rf"{{\Huge\bfseries\color{{black}} {display_title}\par}}",
            rf"{{\Huge\bfseries\color{{black}} {first_line}\par}}"
            "\n      " + rf"\vspace{{0.18in}}{{\LARGE\bfseries\color{{black}} {second_line}\par}}",
        )
        main = re.sub(
            r"\s*\\vspace\{0\.5in\}\s*\{\\Large\\color\{darkgray\}[^\n]*\\par\}",
            "",
            main,
            count=1,
        )
    if r"\cftchapnumwidth" in main or r"\tableofcontents" in main:
        marker = r"\begin{document}"
        setting = r"\setlength{\cftchapnumwidth}{6em}"
        if setting not in main and marker in main:
            main = main.replace(marker, setting + "\n" + marker, 1)
    if main == original:
        return []
    main_path.write_text(main, encoding="utf-8")
    return ["technical_subtitle", "technical_author_date_version", "pdf_title_suffix"]


def find_staging_project(staging_dir: Path) -> Path:
    report = _read_json(staging_dir / "latex_polish_report.json")
    configured = str(report.get("project_dir") or "").strip()
    candidates: list[Path] = []
    if configured:
        path = Path(configured)
        candidates.append(path if path.is_absolute() else staging_dir / path)
    candidates.append(staging_dir)
    candidates.extend(path.parent.parent for path in staging_dir.glob("*/project/chapters/content.tex"))
    for candidate in candidates:
        if (candidate / "main.tex").is_file() and (candidate / "chapters" / "content.tex").is_file():
            return candidate.resolve()
    raise WorkbookRepairError(f"No refined LaTeX project found under {staging_dir}")


def regroup_choice_matrices(text: str) -> tuple[str, list[dict[str, Any]]]:
    lines = text.splitlines()
    output: list[str] = []
    changes: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        parsed = _parse_choice_matrix(lines, index)
        if not parsed:
            output.append(lines[index])
            index += 1
            continue
        end, rows, labels, source_numbers = parsed
        output.append(r"\Needspace{6\baselineskip}")
        output.append(
            r"\begin{enumerate}[label=\arabic*.,leftmargin=*,itemsep=0.25\baselineskip,topsep=0.35\baselineskip]"
        )
        for row in rows:
            cells = [f"{label}. {row[label]}" for label in labels]
            output.append(r"\item " + r"\quad ".join(cells))
        output.append(r"\end{enumerate}")
        changes.append(
            {
                "source_line": index + 1,
                "question_count": len(rows),
                "labels": labels,
                "source_numbers": source_numbers,
                "renumbered_from_source": source_numbers != list(range(1, len(rows) + 1)),
            }
        )
        index = end
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, changes


def _parse_choice_matrix(
    lines: list[str],
    start: int,
) -> tuple[int, list[dict[str, str]], list[str], list[int]] | None:
    isolated = _isolated_a_option(lines, start)
    first = _match_a_option(lines[start]) if not isolated else None
    if isolated:
        numbers: list[int] = []
        a_values: list[str] = []
        index = start
        while index < len(lines):
            parsed = _isolated_a_option(lines, index)
            if not parsed:
                break
            index, value = parsed
            numbers.append(len(numbers) + 1)
            a_values.append(value)
            while index < len(lines) and not lines[index].strip():
                index += 1
        if len(a_values) < 4:
            return None
    elif not first:
        return None
    else:
        numbers = []
        a_values = []
        index = start
        while index < len(lines):
            match = _match_a_option(lines[index])
            if not match:
                break
            numbers.append(int(match.group(1)))
            a_values.append(match.group(2).strip())
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
    if len(a_values) < 4 or not _safe_source_number_sequence(numbers):
        return None

    values: dict[str, list[str]] = {"A": a_values}
    labels = ["A"]
    for label in "BCD":
        collected: list[str] = []
        cursor = index
        for _ in a_values:
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
            if cursor >= len(lines):
                collected = []
                break
            match = PLAIN_OPTION_RE.match(lines[cursor])
            if not match or match.group(1) != label:
                collected = []
                break
            collected.append(match.group(2).strip())
            cursor += 1
        if not collected:
            if label in "BC":
                return None
            break
        values[label] = collected
        labels.append(label)
        index = cursor

    rows = [
        {label: values[label][row_index] for label in labels}
        for row_index in range(len(a_values))
    ]
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index, rows, labels, numbers


def _isolated_a_option(lines: list[str], start: int) -> tuple[int, str] | None:
    if start + 2 >= len(lines) or lines[start].strip() != r"\begin{enumerate}":
        return None
    cursor = start + 1
    if cursor < len(lines) and lines[cursor].strip().startswith(r"\setcounter{enumi}"):
        cursor += 1
    if cursor >= len(lines):
        return None
    match = re.match(r"^\s*\\item\s+A\.?\s+(.+?)\s*$", lines[cursor])
    if not match or cursor + 1 >= len(lines) or lines[cursor + 1].strip() != r"\end{enumerate}":
        return None
    return cursor + 2, match.group(1).strip()


def remove_option_answer_spaces(text: str) -> tuple[str, int]:
    return OPTION_ANSWER_SPACE_RE.subn(lambda match: match.group("block") + "\n", text)


def repair_ocr_placeholder_runs(text: str) -> tuple[str, int]:
    text, option_count = OCR_OPTION_PLACEHOLDER_RE.subn(lambda match: f"{match.group(1)}. {match.group(2)}. ", text)
    text, blank_count = OCR_BLANK_PLACEHOLDER_RE.subn(
        lambda match: rf"\rule{{2.0em}}{{0.4pt}}{match.group(1)}\rule{{2.0em}}{{0.4pt}} {match.group(2)}",
        text,
    )
    text, name_count = OCR_NUMBERED_NAME_PLACEHOLDER_RE.subn(
        lambda match: f"{match.group('prefix')}. {match.group('name').strip()}",
        text,
    )
    return text, option_count + blank_count + name_count


def add_written_response_spaces(text: str) -> tuple[str, list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []
    for prompt in list(WRITING_PROMPT_RE.finditer(text)):
        chapter_end = text.find(r"\chapter", prompt.end())
        scope_end = chapter_end if chapter_end >= 0 else len(text)
        scope = text[prompt.end() : scope_end]
        if ANSWER_SURFACE_RE.search(scope):
            continue
        figure_end = re.search(r"\\end\{figure\}", scope)
        insertion = prompt.end() + (figure_end.end() if figure_end else 0)
        text = text[:insertion] + "\n\n\\printlonganswer" + text[insertion:]
        changes.append({"source_line": text.count("\n", 0, prompt.start()) + 1, "prompt": " ".join(prompt.group(1).split())})
    return text, changes


def promote_embedded_exercise_headings(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    output: list[str] = []
    pending_heading = ""
    in_enumerate = False
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped == r"\begin{enumerate}":
            in_enumerate = True
        if in_enumerate and EMBEDDED_EXERCISE_HEADING_RE.match(stripped):
            pending_heading = stripped
            count += 1
            continue
        output.append(line)
        if stripped == r"\end{enumerate}":
            in_enumerate = False
            if pending_heading:
                output.extend(["", rf"\exerciseheading{{{pending_heading}}}"])
                pending_heading = ""
    if pending_heading:
        output.extend(["", rf"\exerciseheading{{{pending_heading}}}"])
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, count


def _match_a_option(line: str) -> re.Match[str] | None:
    return A_OPTION_RE.match(line) or INLINE_A_OPTION_RE.match(line)


def _safe_source_number_sequence(numbers: list[int]) -> bool:
    expected = list(range(1, len(numbers) + 1))
    if numbers == expected:
        return True
    deltas = [right - left for left, right in zip(numbers, numbers[1:])]
    return (
        bool(numbers)
        and numbers[0] == 1
        and numbers[-1] == len(numbers) - 1
        and deltas.count(0) == 1
        and all(delta in {0, 1} for delta in deltas)
    )


def cap_low_resolution_images(text: str, project_dir: Path) -> tuple[str, list[dict[str, Any]]]:
    matches = list(INCLUDEGRAPHICS_RE.finditer(text))
    changes: list[dict[str, Any]] = []
    replacements: list[tuple[int, int, str]] = []
    rows: list[dict[str, Any]] = []
    for match in matches:
        width = _text_width_fraction(match.group("options"))
        if width is None:
            continue
        line = text.count("\n", 0, match.start()) + 1
        rows.append(
            {
                "match": match,
                "line": line,
                "width": width,
                "path": match.group("path"),
            }
        )

    for row in rows:
        image_path = _resolve_image(project_dir, row["path"])
        dimensions = _image_dimensions(image_path)
        if not dimensions:
            continue
        pixel_width, pixel_height = dimensions
        if max(pixel_width, pixel_height) >= 650 or row["width"] < 0.35:
            continue
        paired = any(
            other is not row
            and other["width"] >= 0.65
            and abs(other["line"] - row["line"]) <= 12
            for other in rows
        )
        portrait_low_resolution = pixel_height > pixel_width and pixel_width < 450
        tiny_asset = max(pixel_width, pixel_height) < 300
        enlarged_low_resolution = row["width"] >= 0.65
        if not paired and not portrait_low_resolution and not tiny_asset and not enlarged_low_resolution:
            continue

        if tiny_asset:
            target_width = 0.18
        elif pixel_width >= pixel_height:
            target_width = 0.54
        elif max(pixel_width, pixel_height) < 400:
            target_width = 0.50
        else:
            target_width = 0.52
        target_width = min(row["width"], target_width)
        options = _replace_image_geometry(row["match"].group("options"), target_width)
        replacement = rf"\includegraphics[{options}]{{{row['path']}}}"
        replacements.append((row["match"].start(), row["match"].end(), replacement))
        changes.append(
            {
                "source_line": row["line"],
                "path": row["path"],
                "pixels": [pixel_width, pixel_height],
                "old_width_textwidth": row["width"],
                "new_width_textwidth": target_width,
                "max_height_textheight": 0.22,
                "reason": "adjacent_large_images" if paired else "low_resolution_portrait",
            }
        )

    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text, changes


def remove_qr_marketing_figures(text: str, project_dir: Path) -> tuple[str, list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []

    def replace_nested(match: re.Match[str]) -> str:
        value = match.group("caption").strip()
        if not QR_MARKETING_RE.search(value):
            return match.group(0)
        changes.append({"source_line": text.count("\n", 0, match.start()) + 1, "caption": value, "preserved_nested_figure": True})
        return match.group("inner") + "\n"

    def replace(match: re.Match[str]) -> str:
        caption = CAPTION_RE.search(match.group(0))
        value = caption.group(1).strip() if caption else ""
        image_match = re.search(r"\\includegraphics\[[^]]*\]\{([^}]+)\}", match.group(0))
        image_path = _resolve_image(project_dir, image_match.group(1)) if image_match else None
        image_is_qr = bool(image_path and _looks_like_qr_image(image_path))
        if not QR_MARKETING_RE.search(value) and not image_is_qr:
            return match.group(0)
        changes.append({"source_line": text.count("\n", 0, match.start()) + 1, "caption": value, "image_qr_detected": image_is_qr})
        return ""

    text = NESTED_FIGURE_RE.sub(replace_nested, text)
    return FIGURE_BLOCK_RE.sub(replace, text), changes


def remove_qr_ocr_residue(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    kept: list[str] = []
    removed = 0
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) <= 80 and QR_MARKETING_RE.search(stripped):
            removed += 1
            continue
        kept.append(line)
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(kept) + suffix, removed


def _looks_like_qr_image(path: Path) -> bool:
    try:
        pixmap = fitz.Pixmap(str(path))
    except Exception:
        return False
    aspect_ratio = pixmap.width / pixmap.height
    if pixmap.width < 80 or pixmap.height < 80 or not (
        0.8 <= aspect_ratio <= 1.25 or 1.45 <= aspect_ratio <= 2.6
    ):
        return False
    step_x = max(1, pixmap.width // 96)
    step_y = max(1, pixmap.height // 96)
    samples = pixmap.samples
    channels = pixmap.n
    rows: list[list[bool]] = []
    color_delta = 0
    color_samples = 0
    for y in range(0, pixmap.height, step_y):
        row = []
        for x in range(0, pixmap.width, step_x):
            offset = (y * pixmap.width + x) * channels
            values = samples[offset : offset + min(channels, 3)]
            if not values:
                continue
            color_delta += max(values) - min(values)
            color_samples += 1
            row.append(sum(values) / len(values) < 110)
        if row:
            rows.append(row)
    if len(rows) < 20 or color_samples == 0 or color_delta / color_samples > 18:
        return False
    dark = sum(value for row in rows for value in row)
    total = sum(len(row) for row in rows)
    horizontal = sum(left != right for row in rows for left, right in zip(row, row[1:]))
    vertical = sum(rows[y][x] != rows[y + 1][x] for y in range(len(rows) - 1) for x in range(min(len(rows[y]), len(rows[y + 1]))))
    return 0.18 <= dark / total <= 0.65 and (horizontal + vertical) / max(1, 2 * total) >= 0.12


def remove_generic_image_captions(text: str) -> str:
    return re.sub(r"\s*\\caption\{\s*image\s*\}", "", text, flags=re.I)


def unwrap_accidental_math_prose(text: str) -> tuple[str, int]:
    changes = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changes
        body = match.group(1)
        if len(re.findall(r"[A-Za-z]", body)) < 12 or any(token in body for token in (r"\frac", r"\sum", r"\begin")):
            return match.group(0)
        changes += 1
        return body

    return re.sub(r"(?m)^\$([^$\n]{20,})\$$", replace, text), changes


def repair_ocr_parenthesis_blanks(text: str) -> tuple[str, int]:
    repaired, count = OCR_PAREN_BLANK_RE.subn(
        lambda match: rf"\rule{{2.0em}}{{0.4pt}}{match.group(1)}\rule{{2.0em}}{{0.4pt}}",
        text,
    )

    def unwrap(match: re.Match[str]) -> str:
        body = match.group("body")
        return body if "source table evidence" not in body.lower() else match.group(0)

    return TTFAMILY_PROSE_RE.sub(unwrap, repaired), count


def repair_private_use_cloze_blanks(text: str) -> tuple[str, int]:
    return PRIVATE_USE_CLOZE_RE.subn(
        lambda match: rf"\rule{{2.0em}}{{0.4pt}}{match.group(1)}\rule{{2.0em}}{{0.4pt}}",
        text,
    )


def regroup_inline_column_options(text: str) -> tuple[str, list[dict[str, Any]]]:
    pattern = re.compile(
        r"(?P<block>\\begin\{enumerate\}\s*(?P<a>(?:\\item A\.[^\n]*\n)+)\\end\{enumerate\})\s*"
        r"(?P<b>B\.[^\n]+)\s*(?P<c>C\.[^\n]+)\s*(?P<d>D\.[^\n]+)",
        re.S,
    )
    changes: list[dict[str, Any]] = []

    def values(label: str, line: str) -> list[str]:
        return [value.strip() for value in re.split(rf"\s+{label}\.\s*", " " + line)[1:]]

    def replace(match: re.Match[str]) -> str:
        a_values = [row.strip()[len(r"\item A.") :].strip() for row in match.group("a").splitlines() if row.strip()]
        columns = [a_values, values("B", match.group("b")), values("C", match.group("c")), values("D", match.group("d"))]
        if len(a_values) < 2 or any(len(column) != len(a_values) for column in columns):
            return match.group(0)
        rows = [
            rf"\item A. {columns[0][index]}\quad B. {columns[1][index]}\quad C. {columns[2][index]}\quad D. {columns[3][index]}"
            for index in range(len(a_values))
        ]
        changes.append({"source_line": text.count("\n", 0, match.start()) + 1, "question_count": len(rows)})
        return "\\begin{enumerate}\n" + "\n".join(rows) + "\n\\end{enumerate}"

    return pattern.sub(replace, text), changes


def remove_duplicate_long_captions(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    removed = 0
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(r"\caption{") and len(stripped) > 300:
            removed += 1
            continue
        if stripped.startswith("*") and stripped.endswith("*") and len(stripped) > 300:
            line = line.replace("*", "", 1)
            line = line[: line.rfind("*")] + line[line.rfind("*") + 1 :]
        output.append(line)
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, removed


def normalize_known_ocr_tokens(text: str) -> tuple[str, int]:
    replacements = {
        "5 ; sim30 p.m.": "5:30 p.m.",
        "AI - generatedartcan": "AI-generated art can",
        "教材链接: 断教材 88U1": "教材链接: 新教材 8BU1",
        "断教材": "新教材",
        "many plans\n\nand animals": "many plants and animals",
        "instrnetio現象": "instructions",
    }
    count = 0
    for source, target in replacements.items():
        occurrences = text.count(source)
        if occurrences:
            text = text.replace(source, target)
            count += occurrences
    text, ai_count = re.subn(r"AI\s*[−-]\s*generatedartcan", "AI-generated art can", text)
    text, textbook_count = re.subn(r"(?<=教材\s)88U1\b", "8BU1", text)
    text, naked_rule_count = re.subn(
        r"2\.0em\s+0\.4pt\s+(\d+)\s+2\.0em\s+0\.4pt",
        lambda match: rf"\rule{{2.0em}}{{0.4pt}}{match.group(1)}\rule{{2.0em}}{{0.4pt}}",
        text,
    )
    text, naked_unnumbered_rule_count = re.subn(
        r"(?<![A-Za-z0-9])2\.0em\s+0\.4pt(?!\s+\d+\s+2\.0em)",
        lambda _match: r"\rule{2.0em}{0.4pt}",
        text,
    )
    text, bullet_count = re.subn(
        r"\$?\\+triangle\s+right\$?",
        r"\\par\\noindent\\textbullet\\ ",
        text,
    )
    text, apostrophe_count = re.subn(r"(?<=\w)'\s+(?=s\b)", "'", text)
    count += ai_count + textbook_count + naked_rule_count + naked_unnumbered_rule_count + bullet_count + apostrophe_count
    return text, count


def repair_detached_translation_completions(text: str) -> tuple[str, int]:
    def replace(match: re.Match[str]) -> str:
        head = match.group("head").rstrip()
        completion = match.group("completion").strip()
        return f"{head}\\\\\n{completion}\n\\end{{enumerate}}{match.group('tail')}"

    return DETACHED_TRANSLATION_COMPLETION_RE.subn(replace, text)


def normalize_plain_section_labels(text: str) -> tuple[str, int]:
    labels = {
        "Word power": r"\par\medskip\noindent\textbf{Word power}\par\smallskip",
        "Language tips": r"\par\medskip\noindent\textbf{Language tips}\par\smallskip",
        "Quiz": r"\par\medskip\noindent\textbf{Quiz}\par\smallskip",
    }
    changes = 0
    for label, replacement in labels.items():
        text, count = re.subn(rf"(?m)^{re.escape(label)}\s*$", lambda _match, value=replacement: value, text)
        changes += count
    return text, changes


def compact_answer_index_runs(text: str) -> tuple[str, int]:
    changes = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changes
        run = match.group("run")
        numbers = []
        for token in re.finditer(
            r"\\begin\{enumerate\}\s*(?:\\setcounter\{enumi\}\{(?P<counter>\d+)\}\s*)?"
            r"\\item\s+\\rule\{2\.0em\}\{0\.4pt\}\s*\\end\{enumerate\}|(?P<plain>\d+)\.",
            run,
            re.S,
        ):
            if token.group("plain"):
                number = int(token.group("plain"))
            elif token.group("counter"):
                number = int(token.group("counter")) + 1
            else:
                number = 1
            if number not in numbers:
                numbers.append(number)
        if len(numbers) < 3:
            return run
        changes += 1
        entries = " ".join(rf"\textbf{{{number}.}}\,\rule{{2.0em}}{{0.4pt}}\quad" for number in numbers)
        return rf"\enlargethispage{{6\baselineskip}}\par\smallskip\noindent {entries}\par\smallskip" + "\n\n"

    return ANSWER_INDEX_RUN_RE.sub(replace, text), changes


def compact_prechapter_answer_lines(text: str) -> tuple[str, int]:
    return re.subn(
        r"(?<!\\enlargethispage\{12\\baselineskip\})\\printshortanswer\s*(?=\\chapter\{)",
        r"\\enlargethispage{12\\baselineskip}\\printshortanswer\n\n",
        text,
    )


def compact_prechapter_dialogue_tails(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    insertions = []
    for index, line in enumerate(lines):
        if not line.startswith(r"\chapter{"):
            continue
        cursor = index - 1
        speaker_rows = []
        while cursor >= 0 and len(speaker_rows) < 4:
            if not lines[cursor].strip() or lines[cursor].startswith("% source_page_idx:"):
                cursor -= 1
                continue
            if not re.match(r"^[A-Z]:\s+\S", lines[cursor]):
                break
            speaker_rows.append(cursor)
            cursor -= 1
        if speaker_rows:
            start = min(speaker_rows)
            if start == 0 or not lines[start - 1].startswith(r"\enlargethispage{"):
                insertions.append((start, index))
    for start, end in reversed(insertions):
        lines.insert(end, r"\endgroup")
        lines.insert(start, r"\enlargethispage{8\baselineskip}\begingroup\small")
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + suffix, len(insertions)


def compact_prechapter_figures(text: str) -> tuple[str, int]:
    pattern = re.compile(
        r"(?s)(?P<head>\\chapter\{[^}\n]+\}.*?\\end\{infobox\})"
        r"(?P<body>(?:(?!\\chapter\{).)*?)"
        r"(?P<figure>\\begin\{figure\}\[H\](?:(?!\\end\{figure\}).)*\\end\{figure\})\s*"
        r"(?=\\chapter\{|\Z)"
    )

    def replace(match: re.Match[str]) -> str:
        body = match.group("body").rstrip()
        return f"{match.group('head')}\n{match.group('figure')}\n{body}\n\n"

    return pattern.subn(replace, text)


def compact_known_orphan_translation_page(text: str) -> tuple[str, int]:
    heading = r"\exerciseheading{IV. Complete the sentences according to the Chinese.}"
    replacement = r"\enlargethispage{6\baselineskip}" + "\n" + heading
    if heading not in text:
        return text, 0
    return text.replace(heading, replacement, 1), 1


def compact_prechapter_translation_tails(text: str) -> tuple[str, int]:
    marker = r"\enlargethispage{6\baselineskip}" + "\n"
    text = text.replace(r"\enlargethispage{3\baselineskip}" + "\n", "").replace(marker, "")
    targets = [
        r"\exerciseheading{IV. Complete the sentences according to the Chinese.}",
        r"\item 在学习中, 只要你不断努力, 就没有什么是难到无法理解的。(too ... to ...)",
        r"\item 树木可以起到一道墙的作用，阻挡强风。(act as)",
    ]
    changes = 0
    for target in targets:
        if target in text:
            text = text.replace(target, marker + target, 1)
            changes += 1
    return text, changes


def normalize_exercise_numbering(text: str) -> tuple[str, list[dict[str, Any]]]:
    lines = text.splitlines()
    output: list[str] = []
    changes: list[dict[str, Any]] = []
    counter = 0
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith(r"\exerciseheading{") or stripped.startswith(r"\chapter{"):
            counter = 0
        if stripped != r"\begin{enumerate}":
            output.append(lines[index])
            index += 1
            continue
        end = index + 1
        while end < len(lines) and lines[end].strip() != r"\end{enumerate}":
            end += 1
        if end >= len(lines):
            output.append(lines[index])
            index += 1
            continue
        block = lines[index : end + 1]
        item_count = sum(1 for row in block if row.strip().startswith(r"\item"))
        existing_counter = next((pos for pos, row in enumerate(block) if row.strip().startswith(r"\setcounter{enumi}")), None)
        if counter == 0 and existing_counter is not None:
            del block[existing_counter]
            existing_counter = None
        elif counter and existing_counter is not None:
            match = re.search(r"\{(\d+)\}\s*$", block[existing_counter])
            existing_value = int(match.group(1)) if match else -1
            if existing_value != counter:
                block[existing_counter] = rf"\setcounter{{enumi}}{{{counter}}}"
                changes.append({"source_line": index + existing_counter + 1, "start_number": counter + 1, "item_count": item_count, "corrected_counter_from": existing_value})
        if item_count and counter and existing_counter is None:
            block.insert(1, rf"\setcounter{{enumi}}{{{counter}}}")
            changes.append({"source_line": index + 1, "start_number": counter + 1, "item_count": item_count})
        if existing_counter is not None:
            match = re.search(r"\{(\d+)\}\s*$", block[existing_counter])
            counter = int(match.group(1)) if match else counter
        counter += item_count
        output.extend(block)
        index = end + 1
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, changes


def clean_image_ocr_labels(text: str) -> tuple[str, list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []

    def replace(match: re.Match[str]) -> str:
        labels = match.group("labels")
        if not _looks_like_image_label_dump(labels):
            return match.group(0)
        context = text[max(0, match.start() - 900) : match.start()]
        add_answer_surface = bool(WRITING_PROMPT_RE.search(context))
        changes.append(
            {
                "source_line": text.count("\n", 0, match.start()) + 1,
                "label_word_count": len(re.findall(r"[A-Za-z]+", labels)),
                "answer_surface_added": add_answer_surface,
            }
        )
        suffix = "\n\n\\printlonganswer" if add_answer_surface else ""
        return match.group("figure") + suffix

    return FIGURE_OCR_LABEL_RE.sub(replace, text), changes


def normalize_metadata_infoboxes(text: str) -> tuple[str, list[dict[str, Any]]]:
    lines = text.splitlines()
    changes: list[dict[str, Any]] = []
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].strip() != r"\begin{infobox}":
            output.append(lines[index])
            index += 1
            continue
        end = index + 1
        while end < len(lines) and lines[end].strip() != r"\end{infobox}":
            end += 1
        if end >= len(lines):
            output.append(lines[index])
            index += 1
            continue
        block = lines[index : end + 1]
        items: list[tuple[str, str]] = []
        for line in block:
            match = METADATA_ITEM_RE.match(line.strip())
            if match:
                label = "范围" if match.group(1) == "范畴" else match.group(1)
                items.append((label, match.group(2)))
        if not items or not any(label == "语篇类型" for label, _ in items):
            output.extend(block)
            index = end + 1
            continue

        cursor = end + 1
        tail_items: list[tuple[str, str]] = []
        while cursor < len(lines):
            stripped = lines[cursor].strip()
            if not stripped:
                cursor += 1
                continue
            match = METADATA_TAIL_RE.match(stripped)
            if not match:
                break
            label = "范围" if match.group(1) == "范畴" else match.group(1)
            tail_items.append((label, match.group(2)))
            cursor += 1

        merged: list[tuple[str, str]] = []
        seen: set[str] = set()
        for label, value in items + tail_items:
            if label not in seen:
                merged.append((label, value))
                seen.add(label)
        normalized = [r"\begin{infobox}", READING_PROFILE_LIST_BEGIN]
        normalized.extend(rf"\item[\textbf{{{label}}}] {value}" for label, value in merged)
        normalized.extend([r"\end{description}", r"\end{infobox}"])
        if block != normalized or tail_items:
            changes.append(
                {
                    "source_line": index + 1,
                    "labels": [label for label, _ in merged],
                    "merged_tail_labels": [label for label, _ in tail_items],
                }
            )
        output.extend(normalized)
        index = cursor

    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, changes


def unsafe_metadata_infoboxes(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != r"\begin{infobox}":
            continue
        end = index + 1
        while end < len(lines) and lines[end].strip() != r"\end{infobox}":
            end += 1
        block = lines[index : min(end + 1, len(lines))]
        labels = [
            match.group(1)
            for row in block
            if (match := METADATA_ITEM_RE.match(row.strip()))
        ]
        has_safe_list = any(
            row.strip() == READING_PROFILE_LIST_BEGIN for row in block
        )
        if labels and any(label == "语篇类型" for label in labels) and not has_safe_list:
            rows.append(labels)
    return rows


def repair_sentence_split_figures(text: str) -> tuple[str, list[dict[str, Any]]]:
    lines = text.splitlines()
    output: list[str] = []
    changes: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        if lines[index].strip() != r"\begin{figure}[H]":
            output.append(lines[index])
            index += 1
            continue
        end = index + 1
        while end < len(lines) and lines[end].strip() != r"\end{figure}":
            end += 1
        previous = next((pos for pos in range(len(output) - 1, -1, -1) if output[pos].strip()), None)
        following = next((pos for pos in range(end + 1, len(lines)) if lines[pos].strip()), None)
        if previous is None or following is None or end >= len(lines):
            output.extend(lines[index : min(end + 1, len(lines))])
            index = min(end + 1, len(lines))
            continue
        prefix = output[previous].rstrip()
        suffix_line = lines[following].strip()
        split_sentence = (
            bool(prefix)
            and prefix[-1] not in ".!?。！？:：;；”\"'"
            and bool(re.match(r"^[a-z]", suffix_line))
        )
        if not split_sentence:
            output.extend(lines[index : end + 1])
            index = end + 1
            continue
        del output[previous:]
        while output and not output[-1].strip():
            output.pop()
        figure = lines[index : end + 1]
        figure = [
            re.sub(
                r"width=0?\.\d+\\textwidth",
                lambda _: r"width=0.50\textwidth",
                row,
            )
            if r"\includegraphics" in row
            else row
            for row in figure
        ]
        output.extend(["", *figure, "", prefix + " " + suffix_line])
        changes.append(
            {
                "source_line": index + 1,
                "prefix": prefix[-80:],
                "image_width": 0.50,
            }
        )
        index = following + 1
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, changes


def sentence_split_figures(text: str) -> list[int]:
    lines = text.splitlines()
    issues: list[int] = []
    for index, line in enumerate(lines):
        if line.strip() != r"\begin{figure}[H]":
            continue
        end = index + 1
        while end < len(lines) and lines[end].strip() != r"\end{figure}":
            end += 1
        previous = next((lines[pos].strip() for pos in range(index - 1, -1, -1) if lines[pos].strip()), "")
        following = next((lines[pos].strip() for pos in range(end + 1, len(lines)) if lines[pos].strip()), "")
        previous_words = re.findall(r"[A-Za-z]+", previous)
        if (
            len(previous_words) >= 3
            and previous[-1] not in ".!?。！？:：;；”\"'"
            and re.match(r"^[a-z]", following)
        ):
            issues.append(index + 1)
    return issues


def restore_cloze_blank_numbers(text: str) -> tuple[str, list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []

    def replace_section(match: re.Match[str]) -> str:
        body = match.group("body")
        issue = _cloze_numbering_issue(body)
        if not issue:
            return match.group(0)
        restored: list[int] = []
        chunks: list[str] = []
        cursor = 0
        for position, blank in enumerate(CLOZE_BLANK_RE.finditer(body), start=1):
            chunks.append(body[cursor : blank.start()])
            if blank.group("number"):
                chunks.append(blank.group(0))
            else:
                chunks.append(r"\rule{2.0em}{0.4pt}" + str(position) + r"\rule{2.0em}{0.4pt}")
                restored.append(position)
            cursor = blank.end()
        chunks.append(body[cursor:])
        changes.append(
            {
                "source_line": text.count("\n", 0, match.start()) + 1,
                "blank_count": issue["blank_count"],
                "restored_numbers": restored,
            }
        )
        return match.group("header") + "".join(chunks)

    return CLOZE_SECTION_RE.sub(replace_section, text), changes


def missing_cloze_blank_numbers(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for match in CLOZE_SECTION_RE.finditer(text):
        issue = _cloze_numbering_issue(match.group("body"))
        if issue:
            issues.append(issue)
    return issues


def _cloze_numbering_issue(body: str) -> dict[str, Any] | None:
    blanks = list(CLOZE_BLANK_RE.finditer(body))
    explicit = [
        (position, int(match.group("number")))
        for position, match in enumerate(blanks, start=1)
        if match.group("number")
    ]
    missing = [
        position
        for position, match in enumerate(blanks, start=1)
        if not match.group("number")
    ]
    if len(blanks) < 5 or len(explicit) < 3 or not missing:
        return None
    if any(position != number for position, number in explicit):
        return None
    if max(number for _, number in explicit) != len(blanks):
        return None
    return {
        "blank_count": len(blanks),
        "explicit_numbers": [number for _, number in explicit],
        "missing_numbers": missing,
    }


def add_translation_expression_answer_spaces(text: str) -> tuple[str, list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []

    def replace_section(match: re.Match[str]) -> str:
        original_body = match.group("body")
        lines = [
            line
            for line in original_body.splitlines()
            if line.strip() not in {r"\printshortanswer", r"\Needspace{6\baselineskip}"}
        ]
        output: list[str] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            if NUMBERED_PAR_LINE_RE.match(line):
                output.extend([line, r"\printshortanswer"])
                index += 1
                continue
            if line.strip() != r"\begin{enumerate}":
                output.append(line)
                index += 1
                continue
            end = next(
                (position for position in range(index + 1, len(lines)) if lines[position].strip() == r"\end{enumerate}"),
                None,
            )
            if end is None:
                output.extend(lines[index:])
                break
            next_begin = next(
                (position for position in range(end + 1, len(lines)) if lines[position].strip() == r"\begin{enumerate}"),
                len(lines),
            )
            block = lines[index : end + 1]
            tail = lines[end + 1 : next_begin]
            output.extend([*block, *tail])
            if not re.search(r"\\item\s+A\.?\s+", "\n".join(block)):
                output.append(r"\printshortanswer")
            index = next_begin
        suffix = "\n" if original_body.endswith("\n") else ""
        normalized = "\n".join(output) + suffix
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        if normalized == original_body:
            return match.group(0)
        changes.append(
            {
                "source_line": text.count("\n", 0, match.start()) + 1,
                "answer_spaces_added": 0,
            }
        )
        return match.group("header") + normalized

    repaired = TRANSLATION_SECTION_RE.sub(replace_section, text)
    if repaired == text:
        return repaired, []
    net_added = max(0, len(ANSWER_SURFACE_RE.findall(repaired)) - len(ANSWER_SURFACE_RE.findall(text)))
    if changes:
        changes[-1]["answer_spaces_added"] = net_added
    return repaired, changes


def _answer_surfaces_outside_translation(text: str) -> int:
    return len(ANSWER_SURFACE_RE.findall(TRANSLATION_SECTION_RE.sub("", text)))


def translation_expression_items_without_space(text: str) -> int:
    missing = 0
    for match in TRANSLATION_SECTION_RE.finditer(text):
        lines = match.group("body").splitlines()
        for index, line in enumerate(lines):
            if not NUMBERED_PAR_LINE_RE.match(line):
                continue
            next_line = next((row.strip() for row in lines[index + 1 :] if row.strip()), "")
            if not ANSWER_SURFACE_RE.match(next_line):
                missing += 1
    return missing


def format_simple_word_banks(text: str) -> tuple[str, list[dict[str, Any]]]:
    lines = text.splitlines()
    output: list[str] = []
    changes: list[dict[str, Any]] = []
    expect_bank = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if re.match(
            r"^\\exerciseheading\{.*words below.*used twice.*\}$",
            stripped,
            re.I,
        ):
            expect_bank = True
            output.append(line)
            continue
        if expect_bank and not stripped:
            output.append(line)
            continue
        if expect_bank:
            words = re.findall(r"[A-Za-z][A-Za-z'-]*", stripped)
            if 3 <= len(words) <= 6 and "\\" not in stripped and len(" ".join(words)) == len(stripped):
                columns = "c" * len(words)
                output.extend(
                    [
                        r"\begin{center}",
                        r"\setlength{\tabcolsep}{1.2em}",
                        rf"\fbox{{\begin{{tabular}}{{{columns}}}",
                        " & ".join(rf"\textit{{{word}}}" for word in words),
                        r"\end{tabular}}",
                        r"\end{center}",
                    ]
                )
                changes.append({"source_line": index + 1, "words": words})
                expect_bank = False
                continue
            expect_bank = False
        output.append(line)
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix, changes


def choice_option_counts(text: str) -> dict[str, int]:
    counts = {label: 0 for label in "ABC"}
    for label in CHOICE_LABEL_RE.findall(text):
        counts[label] += 1
    return counts


def duplicate_image_ocr_labels(text: str) -> list[str]:
    return [
        match.group("labels")
        for match in FIGURE_OCR_LABEL_RE.finditer(text)
        if _looks_like_image_label_dump(match.group("labels"))
    ]


def missing_written_response_prompts(text: str) -> list[str]:
    missing: list[str] = []
    for match in WRITING_PROMPT_RE.finditer(text):
        chapter_end = text.find(r"\chapter", match.end())
        scope = text[match.end() : chapter_end if chapter_end >= 0 else len(text)]
        if not ANSWER_SURFACE_RE.search(scope):
            missing.append(" ".join(match.group(1).split()))
    return missing


def _looks_like_image_label_dump(value: str) -> bool:
    if re.search(r"[.!?。！？]", value):
        return False
    words = [word.lower() for word in re.findall(r"[A-Za-z]+", value)]
    return len(words) >= 25 and len(words) - len(set(words)) >= 5


def _text_width_fraction(options: str) -> float | None:
    for option in options.split(","):
        match = WIDTH_RE.match(option)
        if match:
            return float(match.group(1))
    return None


def _replace_image_geometry(options: str, width: float) -> str:
    kept = []
    for option in options.split(","):
        stripped = option.strip()
        if WIDTH_RE.match(stripped) or HEIGHT_RE.match(stripped) or stripped == "keepaspectratio":
            continue
        if stripped:
            kept.append(stripped)
    kept.extend([f"width={width:.2f}\\textwidth", "height=0.22\\textheight", "keepaspectratio"])
    return ",".join(kept)


def _resolve_image(project_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_dir / path


def _image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        pixmap = fitz.Pixmap(str(path))
    except Exception:
        return None
    return pixmap.width, pixmap.height


def _invariants(text: str) -> dict[str, int]:
    return {
        "chapters": len(re.findall(r"\\chapter\*?\s*\{", text)),
        "exercise_headings": len(re.findall(r"\\exerciseheading\s*\{", text)),
        "answer_surfaces": len(ANSWER_SURFACE_RE.findall(text)),
    }


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}
