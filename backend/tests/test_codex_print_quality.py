from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz

from app.services.codex_print_quality import LANDSCAPE_PAGE_EXPANSION_RATIO, MATH_OCR_RESIDUE_PATTERNS, MAX_PAGE_EXPANSION_RATIO, _is_image_only_exercise_page, _page_expansion_limit, build_print_quality_report


def _pdf(path: Path, page_texts: list[str]) -> None:
    document = fitz.open()
    for text in page_texts:
        page = document.new_page()
        page.insert_textbox(fitz.Rect(36, 36, 560, 806), text, fontsize=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(path)
    document.close()


def test_page_expansion_limit_allows_dense_landscape_source_reflow(tmp_path):
    portrait = tmp_path / "portrait.pdf"
    landscape = tmp_path / "landscape.pdf"
    for path, size in ((portrait, (595, 842)), (landscape, (842, 595))):
        document = fitz.open()
        for _ in range(4):
            document.new_page(width=size[0], height=size[1])
        document.save(path)
        document.close()
    assert _page_expansion_limit(portrait) == MAX_PAGE_EXPANSION_RATIO
    assert _page_expansion_limit(landscape) == LANDSCAPE_PAGE_EXPANSION_RATIO


def _project_evidence(
    root: Path,
    *,
    expected_units: int,
    chapters: int,
    answer_spaces: int,
    answer_command: str = "",
) -> None:
    clean_dir = root / "work" / "body-final"
    clean_dir.mkdir(parents=True)
    clean_dir.joinpath("clean.md").write_text(
        "\n".join(f"# Unit {index}\n语篇类型: reading" for index in range(1, expected_units + 1)),
        encoding="utf-8",
    )
    project_dir = root / "work" / "project"
    project_dir.joinpath("chapters").mkdir(parents=True)
    project_dir.joinpath("chapters", "content.tex").write_text(
        "\n".join(f"\\chapter{{Unit {index}}}" for index in range(1, chapters + 1)) + answer_command,
        encoding="utf-8",
    )
    root.joinpath("latex_polish_report.json").write_text(
        json.dumps(
            {
                "project_dir": "work/project",
                "after": {"print_answer_space_blocks": answer_spaces},
            }
        ),
        encoding="utf-8",
    )
    root.joinpath("main.tex").write_text("\\documentclass{book}\n\\begin{document}\n\\end{document}\n", encoding="utf-8")


def test_print_quality_blocks_non_printable_candidate(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    _pdf(
        compiled,
        [
            "Cover",
            "Contents",
            "orphan",
            "\n".join(
                [
                    "Scan the QR code to order the video.",
                    "Illustration (no text or symbols visible)",
                    "SHANGHAI STUDENTS' POST",
                    "The quick brown fox jumps over the lazy dog.",
                    "{{{{{ OCR",
                    "Translate the following expressions.",
                    "Translate the following sentences.",
                    "Complete the table according to the article.",
                    *[f"1. option {index}" for index in range(12)],
                    *[f"A. option {index}" for index in range(5)],
                    *[f"B. option {index}" for index in range(5)],
                    *[f"C. option {index}" for index in range(5)],
                ]
            ),
        ],
    )
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source"])
    _project_evidence(tmp_path, expected_units=3, chapters=1, answer_spaces=0)

    report = build_print_quality_report(tmp_path, compiled)

    codes = {row["code"] for row in report["hard_blockers"]}
    assert report["status"] == "blocked"
    assert {
        "low_text_or_orphan_pages",
        "broken_list_numbering",
        "ungrouped_choice_matrix",
        "qr_or_scan_prompt",
        "ai_image_caption",
        "ocr_placeholder_run",
        "test_string",
        "outline_coverage_incomplete",
        "page_expansion_suspicious",
        "print_answer_space_missing",
        "full_page_visual_review_missing",
    }.issubset(codes)


def test_print_quality_accepts_large_type_structural_divider_as_non_orphan(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    document = fitz.open()
    document.new_page().insert_text((40, 80), "Cover")
    document.new_page().insert_text((40, 80), "Contents")
    divider = document.new_page()
    divider.insert_text((120, 100), "2  SECTION 2: APPLYING KEY SKILLS", fontsize=20)
    document.save(compiled)
    document.close()
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source"])
    _project_evidence(tmp_path, expected_units=1, chapters=1, answer_spaces=0)

    report = build_print_quality_report(tmp_path, compiled)

    low_text = next((row for row in report["hard_blockers"] if row["code"] == "low_text_or_orphan_pages"), None)
    assert low_text is None or 3 not in low_text["pages"]
    assert report["pages"][2]["structural_divider_page"] is True


def test_structural_divider_pattern_accepts_elegantbook_chinese_chapter_prefix():
    from app.services.codex_print_quality import STRUCTURAL_DIVIDER_RE

    assert STRUCTURAL_DIVIDER_RE.search("第2 章SECTION 2: APPLYING KEY SKILLS")


def test_image_only_exercise_continuation_requires_nearby_instruction_and_large_image():
    pages = [
        {"text_chars": 42, "max_image_area_ratio": 0.0},
        {"text_chars": 2, "max_image_area_ratio": 0.13},
    ]
    texts = ["Look at the pictures. Write two sentences for each picture.", "A B"]

    assert _is_image_only_exercise_page(pages, texts, 1) is True
    assert _is_image_only_exercise_page(pages, ["Unrelated lesson", "A B"], 1) is False
    assert _is_image_only_exercise_page(pages, ["选择：下列图形中正确的是（ ）。", "A B C D"], 1) is True
    assert _is_image_only_exercise_page(
        pages,
        ["选择：下列图形中正确的是（ ）。", "1.4 2 运算律\nA\nB\nC\nD\n21\n"],
        1,
    ) is True
    assert _is_image_only_exercise_page(
        pages,
        ["Solve the equations algebraically, then illustrate the solution graphically.", "x y"],
        1,
    ) is True


def test_print_quality_passes_complete_candidate(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    body = " ".join(["Classroom-ready lesson content with complete questions and useful practice."] * 8)
    _pdf(compiled, ["Printable workbook cover", "Contents with two complete units", body])
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source page one", "source page two"])
    _project_evidence(tmp_path, expected_units=2, chapters=2, answer_spaces=3)
    review_dir = tmp_path / "04-final-review" / "rendered-all"
    review_dir.mkdir(parents=True)
    review_rows = []
    for page in range(1, 4):
        image = review_dir / f"page-{page:04d}.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 2048)
        review_rows.append(
            {
                "page": page,
                "image": image.relative_to(tmp_path).as_posix(),
                "status": "passed",
                "findings": [],
            }
        )
    tmp_path.joinpath("page_review.json").write_text(
        json.dumps(
            {
                "pdf_sha256": hashlib.sha256(compiled.read_bytes()).hexdigest(),
                "page_count": 3,
                "pages": review_rows,
            }
        ),
        encoding="utf-8",
    )

    report = build_print_quality_report(tmp_path, compiled)

    assert report["status"] == "passed"
    assert report["hard_blockers"] == []
    assert report["metrics"]["reviewed_pages"] == 3


def test_print_quality_allows_terminal_text_and_figure_tail(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    document = fitz.open()
    for text in ("Cover", "Contents", "Complete classroom content " * 20):
        page = document.new_page()
        page.insert_textbox(fitz.Rect(36, 36, 560, 806), text, fontsize=9)
    tail = document.new_page()
    tail.insert_textbox(
        fitz.Rect(36, 36, 560, 180),
        "The final geometric conclusion follows from the equations above. " * 2,
        fontsize=9,
    )
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 230, 160), False)
    pixmap.clear_with(0xDDDDDD)
    tail.insert_image(fitz.Rect(180, 200, 410, 360), pixmap=pixmap)
    document.save(compiled)
    document.close()
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source page"])
    _project_evidence(tmp_path, expected_units=0, chapters=1, answer_spaces=0)

    report = build_print_quality_report(tmp_path, compiled)

    assert 4 not in report["metrics"]["low_text_pages"]


def test_print_quality_reports_ocr_placeholder_pages(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    _pdf(compiled, ["Cover", "Contents", "normal " * 40, "broken (((( formula " * 20])
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source"])
    _project_evidence(tmp_path, expected_units=0, chapters=1, answer_spaces=0)

    report = build_print_quality_report(tmp_path, compiled)
    blocker = next(row for row in report["hard_blockers"] if row["code"] == "ocr_placeholder_run")

    assert blocker["pages"] == [4]
    assert report["pages"][3]["ocr_placeholder_runs"] > 0


def test_print_quality_reports_visible_math_ocr_residue_by_page(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    _pdf(
        compiled,
        [
            "Cover",
            "Contents",
            "normal classroom mathematics " * 20,
            "x ∧ 2 and (1)(m) and [3](x) and (l) malformed source table evidence",
        ],
    )
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source"])
    _project_evidence(tmp_path, expected_units=0, chapters=1, answer_spaces=0)

    report = build_print_quality_report(tmp_path, compiled)
    blocker = next(row for row in report["hard_blockers"] if row["code"] == "math_ocr_residue")

    assert blocker["pages"] == [4]
    assert blocker["counts"] == {
        "exponent_wedge": 0,
        "fraction_tuple": 1,
        "radical_tuple": 1,
        "source_table_evidence": 1,
        "ocr_case_marker": 1,
    }
    assert MATH_OCR_RESIDUE_PATTERNS["exponent_wedge"].findall("x ∧ 2") == ["∧ 2"]
    assert MATH_OCR_RESIDUE_PATTERNS["fraction_tuple"].findall("(2)\n(1)") == []
    assert MATH_OCR_RESIDUE_PATTERNS["fraction_tuple"].findall("(1)(m)") == ["(1)(m)"]
    assert MATH_OCR_RESIDUE_PATTERNS["radical_tuple"].findall("award [2] (b) solve") == []


def test_print_quality_blocks_page_flush_suppression_collision_and_truncated_tail(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    document = fitz.open()
    document.new_page().insert_text((36, 80), "Printable workbook cover", fontsize=11)
    document.new_page().insert_text((36, 80), "Contents", fontsize=11)
    page = document.new_page()
    page.insert_text((36, 100), "Previous lesson body continues here.", fontsize=10)
    page.insert_text((150, 102), "Chapter 1 Complete Lesson", fontsize=17)
    page.insert_text((36, 180), "Short opening only. ![Illustration of a classroom", fontsize=10)
    document.save(compiled)
    document.close()
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source page"])
    clean_dir = tmp_path / "work" / "body-final"
    clean_dir.mkdir(parents=True)
    clean_dir.joinpath("clean.md").write_text(
        "# Complete Lesson\n语篇类型: reading\n"
        "This is the opening classroom sentence with enough source words for checking.\n"
        "The final substantive source sentence must remain visible in the compiled classroom workbook.\n",
        encoding="utf-8",
    )
    project_dir = tmp_path / "work" / "project" / "chapters"
    project_dir.mkdir(parents=True)
    project_dir.joinpath("content.tex").write_text("\\chapter{Complete Lesson}\nShort opening only.\n", encoding="utf-8")
    tmp_path.joinpath("latex_polish_report.json").write_text(
        json.dumps({"project_dir": "work/project", "after": {"print_answer_space_blocks": 0}}),
        encoding="utf-8",
    )
    tmp_path.joinpath("main.tex").write_text(
        "\\documentclass{book}\n\\let\\clearpage\\relax\n\\begin{document}\n\\end{document}\n",
        encoding="utf-8",
    )

    report = build_print_quality_report(tmp_path, compiled)

    codes = {row["code"] for row in report["hard_blockers"]}
    assert "unsafe_page_flush_suppression" in codes
    assert "chapter_heading_collision" in codes
    assert "markdown_image_syntax" in codes
    assert "editorial_image_description" in codes
    assert "source_tail_anchor_missing" in codes
    assert "page_review_provenance_mismatch" in codes


def test_print_quality_counts_refiner_answer_surface_macros(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    body = " ".join(["Translate the following classroom sentences with enough practice context."] * 12)
    _pdf(compiled, ["Printable workbook cover", "Contents", body])
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source one", "source two"])
    _project_evidence(
        tmp_path,
        expected_units=2,
        chapters=2,
        answer_spaces=0,
        answer_command="\n\\printmediumanswer\n\\printwritingbox\n",
    )
    review_dir = tmp_path / "04-final-review" / "rendered-all"
    review_dir.mkdir(parents=True)
    review_rows = []
    for page in range(1, 4):
        image = review_dir / f"page-{page:04d}.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 2048)
        review_rows.append({"page": page, "image": image.relative_to(tmp_path).as_posix(), "status": "passed"})
    tmp_path.joinpath("page_review.json").write_text(
        json.dumps(
            {
                "pdf_sha256": hashlib.sha256(compiled.read_bytes()).hexdigest(),
                "page_count": 3,
                "pages": review_rows,
            }
        ),
        encoding="utf-8",
    )

    report = build_print_quality_report(tmp_path, compiled)

    assert report["metrics"]["added_answer_space_blocks"] == 2
    assert "print_answer_space_missing" not in {row["code"] for row in report["hard_blockers"]}


def test_print_quality_blocks_duplicate_image_labels_and_local_missing_writing_space(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    body = " ".join(["Printable classroom exercise content with complete source text."] * 12)
    _pdf(compiled, ["Cover", "Contents", body])
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source one", "source two"])
    _project_evidence(tmp_path, expected_units=1, chapters=1, answer_spaces=0)
    content_path = tmp_path / "work" / "project" / "chapters" / "content.tex"
    content_path.write_text(
        "\\chapter{Furniture}\n"
        "Give Sam at least four pieces of advice.\n"
        "\\begin{figure}[H]\n\\end{figure}\n"
        "\\emph{Window Washing machine Bedside table Bed Shelf Front Bedroom Bed Shelf Wardrobe Shelf "
        "Wardrobe Bedside table Bed Back Bedroom Chair Desk Shoe shelf TV cabinet Bookcase Coffee table "
        "Living Room Dining table Chairs Arm-chair Arm-chair Shower room Toilet Bathroom Kitchen Fridge "
        "Cooker Cupboard Sink Window Window South North}\n",
        encoding="utf-8",
    )

    report = build_print_quality_report(tmp_path, compiled)
    codes = {row["code"] for row in report["hard_blockers"]}

    assert "duplicate_image_ocr_labels" in codes
    assert "written_response_space_missing" in codes


def test_print_quality_blocks_lost_choice_options_and_first_chapter_layout_defects(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    body = " ".join(["Printable classroom exercise content with complete source text."] * 12)
    _pdf(compiled, ["Cover", "Contents", body])
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source one", "source two"])
    _project_evidence(tmp_path, expected_units=1, chapters=1, answer_spaces=0)
    cleanlatex = tmp_path / "work" / "02-cleanlatex"
    cleanlatex.mkdir(parents=True)
    cleanlatex.joinpath("input.tex").write_text(
        "1. A. about\\\\ B. for\\\\ C. with\\\\\n"
        "2. A. got\\\\ B. get\\\\ C. getting\\\\\n",
        encoding="utf-8",
    )
    content_path = tmp_path / "work" / "project" / "chapters" / "content.tex"
    content_path.write_text(
        r"""\chapter{Enjoy Being a Teenager}
\begin{infobox}
\begin{itemize}
\item[\textbf{语篇类型}] 随笔
\end{itemize}
\end{infobox}
\exerciseheading{I. Choose the best words or phrases to complete the passage.}
First \rule{2.0em}{0.4pt} sentence fragment
\begin{figure}[H]
\end{figure}
continues before \rule{2.0em}{0.4pt}2\rule{2.0em}{0.4pt}
third \rule{2.0em}{0.4pt}3\rule{2.0em}{0.4pt} fourth \rule{2.0em}{0.4pt}
fifth \rule{2.0em}{0.4pt}5\rule{2.0em}{0.4pt}.
\begin{vocabbox}\end{vocabbox}
\exerciseheading{II. Translate the following expressions from English to Chinese.}
\par\Needspace{2\baselineskip}\noindent\textbf{1.} nine out of ten\par
""",
        encoding="utf-8",
    )

    report = build_print_quality_report(tmp_path, compiled)
    codes = {row["code"] for row in report["hard_blockers"]}

    assert "choice_options_lost" in codes
    assert "metadata_infobox_unsafe_list" in codes
    assert "cloze_blank_numbers_missing" in codes
    assert "translation_answer_space_missing" in codes
    assert "figure_splits_sentence" in codes


def test_print_quality_accepts_low_text_image_response_page(tmp_path):
    compiled = tmp_path / "compiled.pdf"
    document = fitz.open()
    document.new_page().insert_text((36, 80), "Printable workbook cover", fontsize=11)
    document.new_page().insert_text((36, 80), "Contents", fontsize=11)
    page = document.new_page()
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 700, 500), False)
    pixmap.clear_with(230)
    page.insert_image(fitz.Rect(150, 70, 445, 300), stream=pixmap.tobytes("png"))
    for y in (345, 370, 395, 420):
        page.draw_line((56, y), (539, y), color=(0.7, 0.7, 0.7), width=0.35)
    page.insert_text((290, 800), "3", fontsize=9)
    document.save(compiled)
    document.close()
    _pdf(tmp_path / "inputs" / "source" / "source.pdf", ["source one", "source two"])
    _project_evidence(
        tmp_path,
        expected_units=1,
        chapters=1,
        answer_spaces=0,
        answer_command="\n\\printlonganswer\n",
    )
    review_dir = tmp_path / "04-final-review" / "rendered-all"
    review_dir.mkdir(parents=True)
    rows = []
    for number in range(1, 4):
        image = review_dir / f"page-{number:04d}.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 2048)
        rows.append({"page": number, "image": image.relative_to(tmp_path).as_posix(), "status": "passed"})
    tmp_path.joinpath("page_review.json").write_text(
        json.dumps(
            {
                "pdf_sha256": hashlib.sha256(compiled.read_bytes()).hexdigest(),
                "page_count": 3,
                "pages": rows,
            }
        ),
        encoding="utf-8",
    )

    report = build_print_quality_report(tmp_path, compiled)

    assert report["status"] == "passed"
    assert report["pages"][2]["structured_response_page"] is True
    assert report["metrics"]["low_text_pages"] == []
