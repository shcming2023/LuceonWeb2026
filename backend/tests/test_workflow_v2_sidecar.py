import fitz
import json
import pytest

from app.workflow_v2.sidecar import _best_fuzzy_anchor, _densest_bounded_anchor_window, _latex_invariants, _normalize_latex_line, _page_snippets, _select_target_pages, _source_page_for_line, _source_pages_for_window
from app.workflow_v2.sidecar_apply import _assert_invariants, validate_codex_response


def test_sidecar_maps_failed_page_to_bounded_latex_window(tmp_path):
    pdf = tmp_path / "candidate.pdf"
    document = fitz.open()
    page = document.new_page()
    anchor = "This unique classroom sentence identifies the broken exercise on this page."
    page.insert_text((40, 80), anchor)
    document.save(pdf)
    document.close()
    lines = ["prefix"] * 80 + [anchor, r"\exerciseheading{Practice}", "suffix"] + ["tail"] * 80
    content = "\n".join(lines)

    result = _page_snippets(pdf, content, [1])[1]

    assert result["status"] == "mapped"
    assert result["file"] == "project/chapters/content.tex"
    assert anchor in result["text"]
    assert len(result["text"].splitlines()) <= 301
    assert result["start_line"] == 11
    assert result["end_line"] == 151


def test_sidecar_window_spans_multiple_unique_anchors_on_one_page(tmp_path):
    pdf = tmp_path / "candidate.pdf"
    document = fitz.open()
    page = document.new_page()
    first = "The first unique theorem statement starts this dense mathematics page."
    last = "The final unique worked solution closes this same dense mathematics page."
    page.insert_text((40, 80), first)
    page.insert_text((40, 120), last)
    document.save(pdf)
    document.close()
    lines = ["padding"] * 20 + [first] + ["middle"] * 100 + [last] + ["tail"] * 20

    result = _page_snippets(pdf, "\n".join(lines), [1])[1]

    assert result["status"] == "mapped"
    assert first in result["text"]
    assert last in result["text"]
    assert len(result["text"].splitlines()) <= 301


def test_sidecar_chooses_densest_bounded_anchor_cluster():
    assert _densest_bounded_anchor_window([10, 20, 30, 500], max_span=160) == [10, 20, 30]
    assert _densest_bounded_anchor_window([10, 500, 510, 520], max_span=160) == [500, 510, 520]


def test_sidecar_normalizes_latex_control_words_out_of_pdf_anchors():
    line = r"\sin x = \frac{4}{8} \quad \text{to find } x \text{ use the } \sin^{-1} \text{ button}"

    assert "tofindxusethesin1button" in _normalize_latex_line(line)


def test_sidecar_binds_latex_window_to_nearest_preceding_source_page():
    lines = [
        r"% source\{\ensuremath{{}_page}\{\ensuremath{{}_idx}: 8",
        r"\chapter{Pine for Water}",
        "passage text",
        r"% source\{\ensuremath{{}_page}\{\ensuremath{{}_idx}: 9",
        "quiz text",
    ]

    assert _source_page_for_line(lines, 2) == 9
    assert _source_page_for_line(lines, 4) == 10


def test_sidecar_collects_all_source_pages_in_patch_window():
    lines = [
        r"% source_page_idx: 8",
        "first page content",
        r"% source_page_idx: 9",
        "second page content",
        r"% source_page_idx: 10",
        "third page content",
    ]

    assert _source_pages_for_window(lines, 1, 5) == [9, 10, 11]


def test_sidecar_ignores_repeated_running_header(tmp_path):
    pdf = tmp_path / "candidate.pdf"
    document = fitz.open()
    body = "A unique exercise sentence appears only on the second rendered page."
    for number in range(3):
        page = document.new_page()
        page.insert_text((40, 40), "Repeated Workbook Header Across Every Page")
        if number == 1:
            page.insert_text((40, 90), body)
    document.save(pdf)
    document.close()
    content = "Repeated Workbook Header Across Every Page\n" + "\n".join(["padding"] * 20) + "\n" + body
    result = _page_snippets(pdf, content, [2])[2]
    assert result["status"] == "mapped"
    assert body in result["text"]


def test_sidecar_maps_short_unique_orphan_line(tmp_path):
    pdf = tmp_path / "orphan.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 80), "suffering and hardship?)")
    document.save(pdf)
    document.close()
    content = "\n".join(["padding"] * 20 + ["suffering and hardship?)"] + ["tail"] * 20)

    result = _page_snippets(pdf, content, [1])[1]

    assert result["status"] == "mapped"
    assert "suffering and hardship?)" in result["text"]


def test_sidecar_fuzzy_anchor_requires_a_unique_strong_match():
    anchors = ["theorem2drawsemicirclesalongthesidesofarighttriangleusingthesidesasdiameters"]
    lines = [
        "unrelatedlessoncontentwithenoughcharactersforcomparison",
        "theorem2drawsemicirclesalongthesidesofarighttriangleusingthesidesoftherighttriangleasdiameters",
        "anotherunrelatedparagraphwithenoughcharactersforcomparison",
    ]

    assert _best_fuzzy_anchor(anchors, lines) == 1


def test_sidecar_fuzzy_anchor_rejects_ambiguous_matches():
    anchors = ["repeatedchapterheadingwithsubstantialsharedcontent"]
    lines = [
        "repeatedchapterheadingwithsubstantialsharedcontentone",
        "repeatedchapterheadingwithsubstantialsharedcontenttwo",
    ]

    assert _best_fuzzy_anchor(anchors, lines) is None


def test_sidecar_invariants_cover_structure_answers_and_options():
    text = r"""\chapter{One}
\exerciseheading{Practice}
\printwritingbox
A. alpha
B. beta
C. gamma
"""
    invariants = _latex_invariants(text)
    assert invariants["chapter_count"] == 1
    assert invariants["exercise_heading_count"] == 1
    assert invariants["answer_surface_count"] == 1
    assert invariants["explicit_writing_rule_count"] == 0
    assert invariants["choice_option_counts"] == {"A": 1, "B": 1, "C": 1}


def test_sidecar_invariants_do_not_count_sequence_labels_as_choices():
    invariants = _latex_invariants(
        "a Find the nth term of sequence A. b Find the nth term of sequence B. "
        "c Use both answers to find sequence C.\n"
    )

    assert invariants["choice_option_counts"] == {"A": 0, "B": 0, "C": 0}


def test_sidecar_invariants_count_explicit_long_writing_rules():
    invariants = _latex_invariants(r"\item prompt \hfill \rule{0.55\linewidth}{0.4pt}")

    assert invariants["explicit_writing_rule_count"] == 1


def test_sidecar_target_selection_is_small_and_finding_diverse():
    rows = [
        {"page": page, "status": "failed", "findings": [{"code": "qr" if page % 2 else "options"}]}
        for page in range(1, 40)
    ]
    selected = _select_target_pages(rows, limit=6)
    assert len(selected) == 6
    assert {row["findings"][0]["code"] for row in selected} == {"qr", "options"}


def _write_sidecar_response(root, diff):
    (root / "repair.diff").write_text(diff, encoding="utf-8")
    (root / "rationale.json").write_text(json.dumps({"summary": "bounded repair"}), encoding="utf-8")
    (root / "rule-suggestions.json").write_text(json.dumps([]), encoding="utf-8")


def _repair_request():
    return {
        "allowed_patch_files": ["project/chapters/content.tex"],
        "failed_pages": [
            {
                "page": 5,
                "latex_snippet": {
                    "status": "mapped",
                    "file": "project/chapters/content.tex",
                    "start_line": 40,
                    "end_line": 80,
                },
            }
        ],
    }


def test_sidecar_response_accepts_hunk_inside_evidence_window(tmp_path):
    _write_sidecar_response(
        tmp_path,
        "--- a/project/chapters/content.tex\n+++ b/project/chapters/content.tex\n@@ -50,3 +50,3 @@\n-old\n+new\n",
    )
    result = validate_codex_response(tmp_path, _repair_request())
    assert result["files"] == ["project/chapters/content.tex"]
    assert result["hunks"][0]["evidence_pages"] == [5]


def test_sidecar_response_rejects_disallowed_file(tmp_path):
    _write_sidecar_response(
        tmp_path,
        "--- a/backend/main.py\n+++ b/backend/main.py\n@@ -50,1 +50,1 @@\n-old\n+new\n",
    )
    with pytest.raises(ValueError, match="disallowed"):
        validate_codex_response(tmp_path, _repair_request())


def test_sidecar_response_rejects_hunk_outside_evidence_window(tmp_path):
    _write_sidecar_response(
        tmp_path,
        "--- a/project/chapters/content.tex\n+++ b/project/chapters/content.tex\n@@ -120,1 +120,1 @@\n-old\n+new\n",
    )
    with pytest.raises(ValueError, match="outside mapped"):
        validate_codex_response(tmp_path, _repair_request())


def test_sidecar_invariants_allow_source_evidenced_heading_restoration():
    protected = {"chapter_count": 2, "exercise_heading_count": 3, "choice_option_counts": {}}
    before = {"chapter_count": 2, "exercise_heading_count": 3, "answer_surface_count": 1, "explicit_writing_rule_count": 0, "choice_option_counts": {}}
    after = {"chapter_count": 2, "exercise_heading_count": 4, "answer_surface_count": 0, "explicit_writing_rule_count": 2, "choice_option_counts": {}}

    _assert_invariants(protected, before, after)


def test_sidecar_invariants_reject_heading_removal():
    protected = {"chapter_count": 2, "exercise_heading_count": 3, "choice_option_counts": {}}
    before = {"chapter_count": 2, "exercise_heading_count": 3, "answer_surface_count": 1, "explicit_writing_rule_count": 0, "choice_option_counts": {}}
    after = {"chapter_count": 2, "exercise_heading_count": 2, "answer_surface_count": 1, "explicit_writing_rule_count": 0, "choice_option_counts": {}}

    with pytest.raises(ValueError, match="removed protected exercise headings"):
        _assert_invariants(protected, before, after)
