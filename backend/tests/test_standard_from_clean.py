import importlib.util
import json
import struct
import sys
import zlib
from pathlib import Path


def load_standard_module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "standard_from_clean.py"
    spec = importlib.util.spec_from_file_location("standard_from_clean", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["standard_from_clean"] = module
    spec.loader.exec_module(module)
    return module


def load_close_review_module():
    load_standard_module()
    script = Path(__file__).resolve().parents[1] / "scripts" / "close_standard_review_outcomes.py"
    spec = importlib.util.spec_from_file_location("close_standard_review_outcomes", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["close_standard_review_outcomes"] = module
    spec.loader.exec_module(module)
    return module


def load_clean_scope_module():
    load_standard_module()
    script = Path(__file__).resolve().parents[1] / "scripts" / "scope_clean_review_for_standard.py"
    spec = importlib.util.spec_from_file_location("scope_clean_review_for_standard", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["scope_clean_review_for_standard"] = module
    spec.loader.exec_module(module)
    return module


def load_corpus_audit_module():
    load_standard_module()
    script = Path(__file__).resolve().parents[1] / "scripts" / "audit_standard_corpus_status_consistency.py"
    spec = importlib.util.spec_from_file_location("audit_standard_corpus_status_consistency", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["audit_standard_corpus_status_consistency"] = module
    spec.loader.exec_module(module)
    return module


def write_minimal_reports(clean_dir: Path, html_tables: int = 0):
    (clean_dir / "manifest.json").write_text(
        '{"material_id":"pdf-test","run_id":"raw-test","title":"Test Book"}',
        encoding="utf-8",
    )
    (clean_dir / "media_report.json").write_text('{"items":[]}', encoding="utf-8")
    (clean_dir / "acceptance_report.json").write_text('{"status":"pass"}', encoding="utf-8")
    (clean_dir / "structure_report.json").write_text(
        f'{{"clean":{{"html_tables":{html_tables},"inline_math_delimiters":0}}}}',
        encoding="utf-8",
    )


def stub_pdf_render(monkeypatch, standard, page_count: int | None = 1):
    def fake_render_pdf(html_path, pdf_path, chrome_path):
        pdf_path.write_bytes(b"%PDF-1.4 fake")
        return True, "ok"

    monkeypatch.setattr(standard, "render_pdf", fake_render_pdf)
    monkeypatch.setattr(standard, "pdf_page_count", lambda _path: page_count)


def png_bytes(width: int, height: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw_row = b"\x00" + (b"\xff\xff\xff" * width)
    compressed = zlib.compress(raw_row * height)
    return header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


def test_build_package_creates_standard_contract(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "standard-final"
    (clean_dir / "images").mkdir(parents=True)
    raw_dir.mkdir()
    image_ref = "images/photo.jpg"
    (clean_dir / image_ref).write_bytes(b"fake image bytes")
    (clean_dir / "clean.md").write_text(
        "\n\n".join(
            [
                "# Unit 1 Amazing Animals",
                "## 1A Animal Intelligence",
                "Before You Read",
                "![A dolphin](images/photo.jpg)",
                "A. Multiple Choice. Choose the best answer.",
                "1. What is the main idea?",
                "a. Dolphins are intelligent.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    (raw_dir / "image_semantics.json").write_text(
        '{"images":[{"image_ref":"images/photo.jpg","block_ref":"content-list-1","page_idx":3,"caption":"A dolphin"}]}',
        encoding="utf-8",
    )

    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, raw_dir, chrome=None)

    assert acceptance["status"] == "pass"
    for name in [
        "standard.md",
        "standard.html",
        "standard.pdf",
        "manifest.json",
        "standard_document.json",
        "standard_issue_candidates.json",
        "issue_candidate_disposition_audit.json",
        "issue_candidate_disposition_audit.html",
        "correction_log.json",
        "layout_report.json",
        "image_relation_report.json",
        "workbook_relation_audit.json",
        "workbook_relation_audit.html",
        "image_visual_confirmation_packets.json",
        "image_visual_confirmation.html",
        "workbook_profile_report.json",
        "workbook_profile.html",
        "print_qa_report.json",
        "standard_acceptance_report.json",
        "standard_quality_score.json",
        "standard_product_status.json",
        "standard_visual_review_packets.json",
        "standard_review_outcomes.json",
        "review_outcomes.html",
        "visual_outcome_review.json",
        "visual_outcome_review.html",
        "review.html",
    ]:
        assert (out_dir / name).exists()
    assert (out_dir / image_ref).exists()
    product_status = json.loads((out_dir / "standard_product_status.json").read_text())
    assert product_status["product_layer"] == "profile_certified_output"
    assert product_status["corpus_promotion"]["basic_print_candidate"] is False
    assert product_status["corpus_promotion"]["basic_print_accepted"] is False
    assert acceptance["gates"]["outline_lock"]["status"] == "pass"
    assert acceptance["gates"]["source_fidelity"]["status"] == "pass"
    assert acceptance["gates"]["media_integrity"]["missing_images"] == []


def test_infer_math_textbook_profile_for_formula_dense_material():
    standard = load_standard_module()
    markdown = "\n\n".join([f"{idx}. $x_{idx}^2 = {idx}$" for idx in range(120)])
    manifest = {"title": "八上 数学"}

    assert standard.infer_standard_profile(markdown, manifest) == "math_textbook"


def test_math_textbook_profile_stays_review_until_visual_outcomes_close(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n\n".join(
            [
                "# Chapter 1",
                "## Lesson 1",
                "$$x^2=4$$",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, raw_dir=None, chrome=None, profile="math_textbook")

    assert acceptance["status"] == "review"
    assert acceptance["gates"]["profile_coverage"]["status"] == "review"
    assert acceptance["gates"]["profile_coverage"]["profile"] == "math_textbook"
    workbook_profile = json.loads((out_dir / "workbook_profile_report.json").read_text())
    assert workbook_profile["profile"] == "math_textbook"
    assert workbook_profile["status"] == "review"
    assert "math_profile_contract_not_pass" in workbook_profile["basic_print_blockers"]
    product_status = json.loads((out_dir / "standard_product_status.json").read_text())
    assert product_status["product_layer"] == "blocked_needs_reconstruction"
    assert "math_profile_contract_not_pass" in product_status["reasons"]


def test_table_review_output_is_standard_review_draft_not_candidate(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n\n".join(
            [
                "# Chapter 1",
                "## Lesson 1",
                "<table><tr><td>Term</td><td>Meaning</td></tr><tr><td>source</td><td>evidence</td></tr></table>",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir, html_tables=1)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, raw_dir=None, chrome=None, profile="reading_textbook")

    assert acceptance["status"] == "review"
    product_status = json.loads((out_dir / "standard_product_status.json").read_text())
    assert product_status["product_layer"] == "standard_review_draft"
    assert product_status["deliverable_use"] == "conservative_fallback_review_draft"
    assert product_status["corpus_promotion"]["status"] == "not_promoted_by_compiler"


def test_workbook_paired_vocabulary_grouping_is_generic(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n\n".join(
            [
                "# Topic 1",
                "## Topic 1 Topic Review",
                "Vocabulary Review",
                "Complete each definition and then provide an example of each vocabulary word used.",
                "Vocabulary",
                "term one",
                "term two",
                "<table><tr><td>Definition</td><td>Example</td></tr><tr><td>1. A ____ is a thing.</td><td></td></tr><tr><td>2. Another ____ term.</td><td></td></tr></table>",
                "Use Vocabulary in Writing",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir, html_tables=1)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, raw_dir=None, chrome=None, profile="exercise_workbook")

    assert acceptance["status"] == "review"
    paired = json.loads((out_dir / "paired_vocabulary_report.json").read_text())
    assert paired["group_count"] == 1
    assert paired["patched_table_count"] == 1
    relation = json.loads((out_dir / "workbook_relation_audit.json").read_text())
    assert not [
        item
        for item in relation["items"]
        if item["kind"] == "orphan_table_question" and item["disposition"] == "real_profile_gap"
    ]
    html = (out_dir / "standard.html").read_text()
    assert "paired-vocab-group" in html
    assert html.count('class="answer-space"') == 2


def test_workbook_paired_vocabulary_grouping_allows_long_word_bank(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    word_bank = [f"term {number}" for number in range(1, 9)]
    (clean_dir / "clean.md").write_text(
        "\n\n".join(
            [
                "# Topic 9",
                "## Topic 9 Topic Review",
                "Vocabulary Review",
                "Complete each definition, and then provide an example of each vocabulary word.",
                "Vocabulary",
                *word_bank,
                "<table><tr><td>Definition</td><td>Example</td></tr><tr><td>1. The first definition.</td><td></td></tr><tr><td>2. The second definition.</td><td></td></tr></table>",
                "Use Vocabulary in Writing",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir, html_tables=1)
    stub_pdf_render(monkeypatch, standard)

    standard.build_package(clean_dir, out_dir, raw_dir=None, chrome=None, profile="exercise_workbook")

    paired = json.loads((out_dir / "paired_vocabulary_report.json").read_text())
    assert paired["group_count"] == 1
    assert paired["patched_table_count"] == 1
    group = paired["groups"][0]
    assert group["layout"] == "word_bank_paragraphs_plus_definition_table"
    assert len(group["children"]) == 10
    assert group["children"][0] != group["table_ids"][0]


def test_clean_review_scope_report_never_promotes_clean_review(tmp_path):
    scope = load_clean_scope_module()
    clean_dir = tmp_path / "clean-final"
    standard_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    standard_dir.mkdir()
    (clean_dir / "manifest.json").write_text('{"material_id":"pdf-test"}', encoding="utf-8")
    (clean_dir / "acceptance_report.json").write_text(
        json.dumps(
            {
                "status": "review",
                "gates": [
                    {"name": "heading_lock", "status": "pass"},
                    {
                        "name": "media_review_threshold",
                        "status": "review",
                        "details": {"review_image_count": 12},
                    },
                    {
                        "name": "llm_structure_revert_threshold",
                        "status": "review",
                        "details": {"reverted_structure_count": 2},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (clean_dir / "structure_report.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "violations": [],
                "raw": {
                    "numbered_question_lines": 3,
                    "blank_marker_count": 4,
                    "html_tables": 1,
                    "image_refs": 2,
                    "inline_math_delimiters": 0,
                },
                "clean": {
                    "numbered_question_lines": 3,
                    "blank_marker_count": 4,
                    "html_tables": 1,
                    "image_refs": 2,
                    "inline_math_delimiters": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    (clean_dir / "loss_audit.json").write_text('{"status":"pass","forbidden_losses":[]}', encoding="utf-8")
    (clean_dir / "render_report.json").write_text('{"pdf_ok":true,"missing_images":[]}', encoding="utf-8")
    (standard_dir / "manifest.json").write_text('{"profile":"grammar_workbook","outputs":{}}', encoding="utf-8")
    (standard_dir / "workbook_profile_report.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "exercise_relation_contract": {"status": "pass"},
                "image_relation_contract": {"status": "pass"},
            }
        ),
        encoding="utf-8",
    )
    (standard_dir / "basic_print_closure_report.json").write_text(
        '{"review_outcomes":{"count":4,"closed_count":4,"open_blocking_count":0}}',
        encoding="utf-8",
    )
    (standard_dir / "standard_acceptance_report.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "quality_score": {"score": 100},
                "summary": {
                    "issue_candidate_unresolved_blocking_count": 0,
                    "review_outcome_count": 4,
                    "review_outcome_closed_count": 4,
                    "review_outcome_open_blocking_count": 0,
                    "image_visual_confirmation_source_crop_count": 2,
                    "visual_review_source_crop_count": 1,
                    "pdf_page_count": 5,
                },
                "gates": {
                    "source_fidelity": {
                        "status": "pass",
                        "clean_text_hash": "abc",
                        "standard_text_hash": "abc",
                    },
                    "correction_evidence": {
                        "status": "pass",
                        "correction_count": 0,
                        "corrections_without_evidence": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    report = scope.build_clean_review_scope_report(clean_dir, standard_dir)

    assert report["status"] == "review_scoped_not_promoted"
    assert report["promotion_candidate"] is False
    assert report["clean_acceptance"]["review_gates"] == [
        "media_review_threshold",
        "llm_structure_revert_threshold",
    ]
    assert [item["scope_decision"] for item in report["clean_review_gate_scope"]] == [
        "covered_for_standard_basic_print_review",
        "risk_contained_for_standard_from_this_clean_candidate",
    ]


def test_clean_review_scope_report_marks_clean_pass_as_no_scope_needed(tmp_path):
    scope = load_clean_scope_module()
    clean_dir = tmp_path / "clean-final"
    standard_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    standard_dir.mkdir()
    (clean_dir / "manifest.json").write_text('{"material_id":"pdf-test"}', encoding="utf-8")
    (clean_dir / "acceptance_report.json").write_text(
        '{"status":"pass","gates":[{"name":"heading_lock","status":"pass"}]}',
        encoding="utf-8",
    )
    (clean_dir / "structure_report.json").write_text(
        '{"status":"pass","violations":[],"raw":{"image_refs":1},"clean":{"image_refs":1}}',
        encoding="utf-8",
    )
    (clean_dir / "loss_audit.json").write_text('{"status":"pass","forbidden_losses":[]}', encoding="utf-8")
    (clean_dir / "render_report.json").write_text('{"pdf_ok":true,"missing_images":[]}', encoding="utf-8")
    (standard_dir / "manifest.json").write_text('{"profile":"reading_textbook","outputs":{}}', encoding="utf-8")
    (standard_dir / "workbook_profile_report.json").write_text("{}", encoding="utf-8")
    (standard_dir / "basic_print_closure_report.json").write_text("{}", encoding="utf-8")
    (standard_dir / "standard_acceptance_report.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "quality_score": {"score": 97},
                "summary": {"pdf_page_count": 12},
                "gates": {
                    "source_fidelity": {
                        "status": "pass",
                        "clean_text_hash": "abc",
                        "standard_text_hash": "abc",
                    },
                    "media_integrity": {"image_refs": 1, "missing_images": []},
                },
            }
        ),
        encoding="utf-8",
    )

    report = scope.build_clean_review_scope_report(clean_dir, standard_dir)

    assert report["status"] == "clean_pass_no_scope_needed"
    assert report["promotion_candidate"] is False
    assert report["clean_acceptance"]["review_gates"] == []
    assert report["clean_review_gate_scope"] == []


def test_issue_candidate_disposition_audit_closes_helper_and_accepted_image_outcomes():
    standard = load_standard_module()
    issue_candidates = [
        {
            "type": "missing_raw_image_semantics",
            "severity": "review",
            "block_id": "b-00001",
            "line": 10,
            "image": "images/key.png",
        },
        {
            "type": "missing_raw_image_semantics",
            "severity": "review",
            "block_id": "b-00002",
            "line": 12,
            "image": "images/icon.png",
        },
    ]
    image_relation_report = {
        "items": [
            {
                "block_id": "b-00001",
                "category": "exercise_key_figure",
                "action": "keep_with_exercise",
                "requires_source_visual_check": True,
            },
            {
                "block_id": "b-00002",
                "category": "helper_icon",
                "action": "compress_keep_near",
                "requires_source_visual_check": False,
            },
        ]
    }
    review_outcomes = {
        "items": [
            {
                "outcome_id": "image:exercise_key_figure:b-00001",
                "packet_type": "image_source_visual_confirmation",
                "block_id": "b-00001",
                "status": "closed",
                "decision": "accepted_by_rule",
                "basic_print_blocking": False,
            }
        ]
    }

    audit = standard.build_issue_candidate_disposition_audit(issue_candidates, image_relation_report, review_outcomes)
    context_gate, threshold_gate = standard.issue_candidate_gate_payloads(audit)

    assert audit["unresolved_blocking_count"] == 0
    assert audit["disposition_counts"]["covered_by_visual_outcome"] == 1
    assert audit["disposition_counts"]["helper_icon_compact_rendering"] == 1
    assert context_gate["status"] == "pass"
    assert threshold_gate["status"] == "pass"


def test_issue_candidate_disposition_audit_keeps_open_key_figure_blocking():
    standard = load_standard_module()
    issue_candidates = [
        {
            "type": "missing_raw_image_semantics",
            "severity": "review",
            "block_id": "b-00001",
            "line": 10,
            "image": "images/key.png",
        }
    ]
    image_relation_report = {
        "items": [
            {
                "block_id": "b-00001",
                "category": "exercise_key_figure",
                "action": "keep_with_exercise",
                "requires_source_visual_check": True,
            }
        ]
    }
    review_outcomes = {
        "items": [
            {
                "outcome_id": "image:exercise_key_figure:b-00001",
                "packet_type": "image_source_visual_confirmation",
                "block_id": "b-00001",
                "status": "open",
                "decision": "needs_source_crop",
                "basic_print_blocking": True,
            }
        ]
    }

    audit = standard.build_issue_candidate_disposition_audit(issue_candidates, image_relation_report, review_outcomes)
    context_gate, threshold_gate = standard.issue_candidate_gate_payloads(audit)

    assert audit["unresolved_blocking_count"] == 1
    assert audit["disposition_counts"]["real_context_gap"] == 1
    assert context_gate["status"] == "review"
    assert threshold_gate["status"] == "pass"


def test_corpus_status_audit_uses_status_policy_not_known_material_ids(tmp_path):
    audit_module = load_corpus_audit_module()
    corpus_dir = tmp_path / "corpus"
    cases_dir = corpus_dir / "cases"
    runs_dir = corpus_dir / "runs"
    candidates_dir = corpus_dir / "golden" / "candidates"
    accepted_dir = corpus_dir / "golden" / "accepted"
    for directory in [cases_dir, runs_dir, candidates_dir, accepted_dir]:
        directory.mkdir(parents=True)

    (runs_dir / "pdf-new.review-draft.run.json").write_text(
        json.dumps({"material_id": "pdf-new", "status": "standard_review_draft"}),
        encoding="utf-8",
    )
    (cases_dir / "pdf-new.case.json").write_text(
        json.dumps(
            {
                "material_id": "pdf-new",
                "profile": "reading_textbook",
                "role": "new_review_draft_case",
                "current_status": "standard_review_draft",
                "latest_run_record": "../runs/pdf-new.review-draft.run.json",
                "candidate_record": "",
                "accepted_golden_record": "",
                "golden": False,
            }
        ),
        encoding="utf-8",
    )

    report = audit_module.audit_corpus(corpus_dir)

    assert report["issue_count"] == 0
    assert report["items"][0]["material_id"] == "pdf-new"
    assert report["items"][0]["expected"]["layer"] == "standard_review_draft"


def test_multiline_html_table_does_not_leak_visible_tags(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "<table>",
                "<tr><td>A</td><td>B</td></tr>",
                "</table>",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir, html_tables=1)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None)
    html = (out_dir / "standard.html").read_text(encoding="utf-8")
    print_qa = standard.read_json(out_dir / "print_qa_report.json")

    assert "<tr><td>A</td><td>B</td></tr>" in html
    assert "&lt;tr&gt;" not in html
    assert print_qa["visible_artifacts"]["count"] == 0
    assert acceptance["gates"]["visible_artifacts"]["status"] == "pass"


def test_html_comments_are_not_rendered_or_counted_as_source_change(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "# Unit 1\n<!-- source_empty_chunk page=3 -->\nVisible content.\n",
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None)
    standard_md = (out_dir / "standard.md").read_text(encoding="utf-8")
    html = (out_dir / "standard.html").read_text(encoding="utf-8")

    assert "source_empty_chunk" not in standard_md
    assert "source_empty_chunk" not in html
    assert acceptance["gates"]["source_fidelity"]["status"] == "pass"
    assert acceptance["gates"]["visible_artifacts"]["status"] == "pass"


def test_source_pdf_argument_marks_visual_packets_available(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    source_pdf = tmp_path / "source.pdf"
    clean_dir.mkdir()
    source_pdf.write_bytes(b"%PDF-1.4 source")
    (clean_dir / "clean.md").write_text("# Unit 1\n<table><tr><td>A</td></tr></table>\n", encoding="utf-8")
    write_minimal_reports(clean_dir, html_tables=1)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, source_pdf_path=source_pdf)
    packets = standard.read_json(out_dir / "standard_visual_review_packets.json")

    assert packets["source_pdf_available"] is True
    assert packets["items"][0]["source_pdf"] == str(source_pdf.resolve())
    assert acceptance["gates"]["source_evidence"]["status"] == "pass"


def test_visible_artifact_detector_flags_escaped_table_tags():
    standard = load_standard_module()
    detected = standard.detect_visible_artifacts("<p>&lt;tr&gt;&lt;td&gt;A&lt;/td&gt;&lt;/tr&gt;</p>")

    assert detected["count"] > 0
    assert detected["items"][0]["type"] == "escaped_table_tag"


def test_auto_profile_detects_grammar_workbook_and_groups_exercises(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Present forms",
                "1 Complete the sentences. Use the verbs in brackets.",
                "1 I \\_\\_\\_\\_ (go) to school every day.",
                "2 She \\_\\_\\_\\_ (read) now.",
                "2 Write questions.",
                "<table><tr><td>1</td><td>you / like / music?</td></tr></table>",
                "a. Do you like music?",
                "![image](images/pencil.png)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (clean_dir / "images").mkdir()
    (clean_dir / "images" / "pencil.png").write_bytes(png_bytes(40, 80))
    (clean_dir / "manifest.json").write_text(
        '{"material_id":"pdf-grammar","run_id":"raw-test","title":"Grammar Practice Workbook.pdf"}',
        encoding="utf-8",
    )
    (clean_dir / "media_report.json").write_text('{"items":[]}', encoding="utf-8")
    (clean_dir / "acceptance_report.json").write_text('{"status":"pass"}', encoding="utf-8")
    (clean_dir / "structure_report.json").write_text('{"clean":{"html_tables":1,"inline_math_delimiters":0}}', encoding="utf-8")
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None)
    document = standard.read_json(out_dir / "standard_document.json")
    layout = standard.read_json(out_dir / "layout_report.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert document["profile"] == "grammar_workbook"
    assert layout["relation_summary"]["question_groups"] == 2
    assert layout["relation_summary"]["questions"] == 2
    assert layout["relation_summary"]["fill_blank_questions"] == 2
    assert layout["relation_summary"]["options"] == 1
    assert layout["relation_summary"]["parented_options"] == 1
    assert layout["relation_summary"]["table_questions"] == 1
    assert layout["relation_summary"]["figure_relation_candidates"] == 1
    assert workbook_report["applicable"] is True
    assert workbook_report["profile_contract"]["status"] == "pass"
    assert workbook_report["exercise_relation_contract"]["metrics"]["parented_options"] == 1
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"
    assert acceptance["gates"]["image_relation_integrity"]["status"] == "pass"
    assert acceptance["gates"]["image_visual_confirmation"]["status"] == "pass"


def test_workbook_groups_change_and_rewrite_instructions(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Comparative adjectives",
                "1 Change the adjectives into comparative adjectives.",
                "1 white whiter",
                "2 comfortable \\_\\_\\_\\_",
                "3 tall \\_\\_\\_\\_",
                "4 Rewrite these expressions. Use every, once, twice or three times.",
                "1 one time once",
                "2 two times \\_\\_\\_\\_",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    layout = standard.read_json(out_dir / "layout_report.json")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert layout["relation_summary"]["question_groups"] == 2
    assert layout["relation_summary"]["questions"] == 5
    assert layout["relation_summary"]["grouped_questions"] == 5
    assert layout["relation_summary"]["ungrouped_questions"] == 0
    assert audit["real_profile_gap_count"] == 0
    assert workbook_report["exercise_relation_contract"]["status"] == "pass"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_groups_explicit_exercise_headings(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Subject pronouns",
                "EXERCISE 1 Fill in the blanks with the correct subject pronoun.",
                "1. We are immigrants.",
                "2. Dorota is from Poland. \\_\\_\\_\\_ is a U.S. citizen now.",
                "Exercise 2 Circle the correct word.",
                "1. He / They is my brother.",
                "2. We / It are students.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    layout = standard.read_json(out_dir / "layout_report.json")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert layout["relation_summary"]["question_groups"] == 2
    assert layout["relation_summary"]["questions"] == 4
    assert layout["relation_summary"]["grouped_questions"] == 4
    assert layout["relation_summary"]["ungrouped_questions"] == 0
    assert audit["real_profile_gap_count"] == 0
    assert workbook_report["exercise_relation_contract"]["status"] == "pass"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_h3_sections_do_not_reset_exercise_group_on_hint_paragraphs(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "### 5.2 Modal: Should--Affirmative and Negative",
                "EXERCISE 2 Complete the conversations with should or shouldn't and the words given.",
                "1. A: I have my written test tomorrow.",
                "B: You should read \\_\\_\\_\\_ the handbook again tonight.",
                "you/read",
                "2. A: My car is dirty.",
                "B: \\_\\_\\_\\_ it today!",
                "you/wash",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    layout = standard.read_json(out_dir / "layout_report.json")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    document = standard.read_json(out_dir / "standard_document.json")
    h3_block = next(block for block in document["blocks"] if "5.2 Modal" in block["markdown"])

    assert h3_block["type"] == "section"
    assert layout["relation_summary"]["question_groups"] == 1
    assert layout["relation_summary"]["questions"] == 2
    assert layout["relation_summary"]["grouped_questions"] == 2
    assert layout["relation_summary"]["ungrouped_questions"] == 0
    assert audit["real_profile_gap_count"] == 0
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_groups_unnumbered_about_you_and_comprehension_prompts(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Time expressions",
                "ABOUT YOU Write how often you do each activity.",
                "1. take the bus",
                "2. relax",
                "COMPREHENSION Based on the reading, write T for true or F for false.",
                "1. \\_\\_\\_\\_ Anna cannot sit in her old car seat.",
                "2. \\_\\_\\_\\_ The outlet mall is expensive.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    layout = standard.read_json(out_dir / "layout_report.json")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert layout["relation_summary"]["question_groups"] == 2
    assert layout["relation_summary"]["questions"] == 4
    assert layout["relation_summary"]["grouped_questions"] == 4
    assert audit["real_profile_gap_count"] == 0
    assert workbook_report["exercise_relation_contract"]["status"] == "pass"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_section_headings_can_hold_reflection_prompts(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "# PART 4 Learner's Log",
                "1. Write one sentence about each of these topics:",
                "- shopping in the United States",
                "2. Write any questions you still have about shopping.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    layout = standard.read_json(out_dir / "layout_report.json")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert layout["relation_summary"]["question_groups"] == 1
    assert layout["relation_summary"]["questions"] == 2
    assert layout["relation_summary"]["grouped_questions"] == 2
    assert audit["real_profile_gap_count"] == 0
    assert workbook_report["exercise_relation_contract"]["status"] == "pass"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_relation_audit_treats_numbered_equivalence_as_explanation(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## How often...? and adverbs of time",
                "1 = one time once",
                "2 = two times twice",
                "1 Rewrite these expressions.",
                "1 two times a week twice a week",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert audit["kind_counts"]["ungrouped_question"] == 2
    assert audit["disposition_counts"]["explanation_artifact"] == 2
    assert audit["real_profile_gap_count"] == 0
    assert workbook_report["exercise_relation_contract"]["status"] == "pass"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_relation_audit_treats_numbered_grammar_notes_as_explanation(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Be--Affirmative Statements",
                "Notes:",
                "1. describe the subject (helpful, big)",
                "2. tell where the subject is from (from Mexico, from Poland)",
                "EXERCISE 1 Fill in the blanks.",
                "1. The laundromat \\_\\_\\_\\_ different.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert audit["kind_counts"]["ungrouped_question"] == 2
    assert audit["disposition_counts"]["explanation_artifact"] == 2
    assert audit["real_profile_gap_count"] == 0
    assert workbook_report["exercise_relation_contract"]["status"] == "pass"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_image_relation_report_buckets_helper_and_key_figures(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "standard-final"
    source_pdf = tmp_path / "source.pdf"
    image_dir = clean_dir / "images"
    image_dir.mkdir(parents=True)
    raw_dir.mkdir()
    source_pdf.write_bytes(b"%PDF-1.4 source")
    (image_dir / "small.png").write_bytes(png_bytes(40, 80))
    (image_dir / "large.png").write_bytes(png_bytes(500, 300))
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Present forms",
                "1 Complete the sentences.",
                "![image](images/large.png)",
                "1 I \\_\\_\\_\\_ (go) every day.",
                "We use the present simple for habits.",
                "![image](images/small.png)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (clean_dir / "manifest.json").write_text(
        '{"material_id":"pdf-grammar","run_id":"raw-test","title":"Grammar Practice Workbook.pdf"}',
        encoding="utf-8",
    )
    (clean_dir / "media_report.json").write_text('{"items":[]}', encoding="utf-8")
    (clean_dir / "acceptance_report.json").write_text('{"status":"pass"}', encoding="utf-8")
    (clean_dir / "structure_report.json").write_text('{"clean":{"html_tables":0,"inline_math_delimiters":0}}', encoding="utf-8")
    (raw_dir / "content_list.json").write_text(
        json.dumps(
            [
                {
                    "type": "image",
                    "img_path": "images/large.png",
                    "page_idx": 4,
                    "bbox": [10, 20, 400, 260],
                    "content": "A workbook exercise image",
                    "sub_type": "text_image",
                }
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "manifest.json").write_text(
        json.dumps({"source_root": str(raw_dir), "content_file": "content_list.json"}),
        encoding="utf-8",
    )
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, raw_dir, chrome=None, source_pdf_path=source_pdf)
    report = standard.read_json(out_dir / "image_relation_report.json")
    packets = standard.read_json(out_dir / "image_visual_confirmation_packets.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")

    assert report["category_counts"]["exercise_key_figure"] == 1
    assert report["category_counts"]["helper_icon"] == 1
    assert report["source_visual_check_count"] == 1
    assert packets["count"] == 1
    assert packets["category_counts"]["exercise_key_figure"] == 1
    assert packets["crop_status_counts"]["ready_for_source_crop"] == 1
    assert packets["excluded_category_counts"]["helper_icon"] == 1
    assert packets["source_crop_summary"]["source_crop_generation"] == "skipped"
    assert packets["source_crop_summary"]["source_crop_status_counts"]["not_generated"] == 1
    assert not (out_dir / "source_crops").exists()
    assert packets["items"][0]["source_page_number"] == 5
    assert packets["items"][0]["source_bbox"] == [10, 20, 400, 260]
    assert acceptance["gates"]["image_relation_integrity"]["status"] == "review"
    assert acceptance["gates"]["image_visual_confirmation"]["status"] == "review"
    assert acceptance["gates"]["review_outcomes"]["status"] == "review"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"
    assert workbook_report["status"] == "review"
    assert workbook_report["regression_verdict"] == "expected_negative_regression_review"
    assert "image_relation_contract_not_pass" in workbook_report["basic_print_blockers"]
    assert workbook_report["image_relation_contract"]["open_image_review_outcome_count"] == 1


def test_workbook_relation_audit_separates_instruction_and_explanation_table(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Passive",
                "We use the passive when the action is more important.",
                "<table><tr><td>Active</td><td>Passive</td></tr><tr><td>They make cars.</td><td>Cars are made.</td></tr></table>",
                "1 Are the sentences active (A) or passive (P)? Write A or P.",
                "1 I was given a lovely present. P",
                "2 She made me a cake. \\_\\_\\_\\_",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir, html_tables=1)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None)
    layout = standard.read_json(out_dir / "layout_report.json")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    workbook_report = standard.read_json(out_dir / "workbook_profile_report.json")
    document = standard.read_json(out_dir / "standard_document.json")
    table = next(block for block in document["blocks"] if block["type"] == "table")

    assert layout["relation_summary"]["question_groups"] == 1
    assert layout["relation_summary"]["questions"] == 2
    assert layout["relation_summary"]["grouped_questions"] == 2
    assert layout["relation_summary"]["table_questions"] == 0
    assert table["subtype"] == "explanation_table"
    assert audit["disposition_counts"]["explanation_artifact"] == 1
    assert audit["real_profile_gap_count"] == 0
    assert workbook_report["exercise_relation_contract"]["status"] == "pass"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_workbook_relation_audit_separates_grammar_paradigm_tables(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Possessive pronouns",
                "<table><tr><td>Possessive adjectives</td><td>Possessive pronouns</td></tr><tr><td>my</td><td>mine</td></tr></table>",
                "## The present perfect",
                "<table><tr><td>Affirmative</td><td>Short form</td><td>Negative</td></tr><tr><td>I have finished</td><td>I've finished</td><td>I haven't finished</td></tr></table>",
                "## Be--Affirmative Statements",
                "<table><tr><td>SUBJECT</td><td>BE</td><td></td></tr><tr><td>I</td><td>am</td><td>a citizen.</td></tr></table>",
                "1 Complete the sentences.",
                "1 This book is \\_\\_\\_\\_.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_minimal_reports(clean_dir, html_tables=2)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="grammar_workbook")
    layout = standard.read_json(out_dir / "layout_report.json")
    audit = standard.read_json(out_dir / "workbook_relation_audit.json")
    document = standard.read_json(out_dir / "standard_document.json")
    table_subtypes = [block["subtype"] for block in document["blocks"] if block["type"] == "table"]

    assert layout["relation_summary"]["table_questions"] == 0
    assert table_subtypes == ["explanation_table", "explanation_table", "explanation_table"]
    assert audit["kind_counts"]["unparented_explanation_table"] == 3
    assert audit["disposition_counts"]["explanation_artifact"] == 3
    assert audit["real_profile_gap_count"] == 0
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"


def test_grammar_paradigm_table_reflows_run_together_cells_for_print():
    standard = load_standard_module()
    cases = [
        (
            "<table><tr><td>Affirmative</td><td>Negative</td><td>Questions</td><td>Short answers</td><td></td></tr>"
            "<tr><td>I’m playingyou’re playingit’s playingwe’re playingthey’re playing</td>"
            "<td>I’m not playingyou aren’t playingit isn’t playingwe aren’t playingthey aren’t playing</td>"
            "<td>Am I playing?Are you playing?Is it playing?Are we playing?Are they playing?</td>"
            "<td>Yes, I am.Yes, you are.Yes, it is.Yes, we are.Yes, they are.</td>"
            "<td>No, I’m not.No, you aren’t.No, it isn’t.No, we aren’t.No, they aren’t.</td></tr></table>",
            ["playingyou", "am.Yes"],
        ),
        (
            "<table><tr><td>Affirmative</td><td>Negative</td><td>Questions</td><td>Short answers</td><td></td></tr>"
            "<tr><td>I've playedyou've playedit's playedwe've playedthey've played</td>"
            "<td>I haven't playedyou haven't playedit hasn't playedwe haven't playedthey haven't played</td>"
            "<td>Have I played?Have you played?Has it played?Have we played?Have they played?</td>"
            "<td>Yes, I have.Yes, you have.Yes, it has.Yes, we have.Yes, they have.</td>"
            "<td>No, I haven't.No, you haven't.No, it hasn't.No, we haven't.No, they haven't.</td></tr></table>",
            ["playedyou", "have.Yes"],
        ),
        (
            "<table><tr><td>Affirmative</td><td>Negative</td><td>Questions</td><td>Short answers</td><td></td></tr>"
            "<tr><td>I was playingyou were playingit was playingwe were playingthey were playing</td>"
            "<td>I wasn't playingyou weren't playingit wasn't playingwe weren't playingthey weren't playing</td>"
            "<td>Was I playing?Were you playing?Was it playing?Were we playing?Were they playing?</td>"
            "<td>Yes, I was.Yes, you were.Yes, it was.Yes, we were.Yes, they were.</td>"
            "<td>No, I wasn't.No, you weren't.No, it wasn't.No, we weren't.No, they weren't.</td></tr></table>",
            ["playingyou", "was.Yes"],
        ),
    ]

    for table_html, collapsed_fragments in cases:
        reflowed = standard.reflow_grammar_paradigm_table(table_html)
        assert reflowed.count("<tr>") == 6
        assert '<table class="grammar-paradigm-table">' in reflowed
        for fragment in collapsed_fragments:
            assert fragment not in reflowed

    rendered = standard.render_block({"id": "b-01544", "type": "table", "markdown": cases[0][0]})
    assert "<td>I’m playing</td><td>I’m not playing</td><td>Am I playing?</td>" in rendered
    assert "<td>Yes, they are.</td><td>No, they aren’t.</td>" in rendered


def test_table_visual_packets_get_source_bbox_and_review_outcome(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "standard-final"
    source_pdf = tmp_path / "source.pdf"
    clean_dir.mkdir()
    raw_dir.mkdir()
    source_pdf.write_bytes(b"%PDF-1.4 source")
    table_html = "<table><tr><td>artists</td><td>popular</td></tr><tr><td>earn</td><td>trainers</td></tr></table>"
    (clean_dir / "clean.md").write_text(f"# Unit 1\n{table_html}\n", encoding="utf-8")
    write_minimal_reports(clean_dir, html_tables=1)
    (raw_dir / "content_list.json").write_text(
        json.dumps(
            [
                {
                    "type": "table",
                    "table_body": table_html,
                    "page_idx": 14,
                    "bbox": [125, 196, 340, 252],
                }
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "manifest.json").write_text(
        json.dumps({"source_root": str(raw_dir), "content_file": "content_list.json"}),
        encoding="utf-8",
    )
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, raw_dir, chrome=None, source_pdf_path=source_pdf)
    packets = standard.read_json(out_dir / "standard_visual_review_packets.json")
    outcomes = standard.read_json(out_dir / "standard_review_outcomes.json")
    visual_review = standard.read_json(out_dir / "visual_outcome_review.json")

    assert packets["count"] == 1
    assert packets["items"][0]["source_page_number"] == 15
    assert packets["items"][0]["source_bbox"] == [125, 196, 340, 252]
    assert packets["items"][0]["crop_status"] == "ready_for_source_crop"
    assert packets["items"][0]["block_subtype"] == "table_question"
    assert outcomes["count"] == 1
    assert outcomes["items"][0]["source_evidence_ready"] is True
    assert outcomes["open_blocking_count"] == 1
    assert visual_review["packet_type_counts"]["table_visual_review"] == 1
    assert acceptance["gates"]["review_outcomes"]["status"] == "review"


def test_table_visual_packets_match_compact_raw_table_text(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "standard-final"
    source_pdf = tmp_path / "source.pdf"
    clean_dir.mkdir()
    raw_dir.mkdir()
    source_pdf.write_bytes(b"%PDF-1.4 source")
    clean_table = (
        "<table><tr><td>Possessive adjectives</td><td>Possessive pronouns</td></tr>"
        "<tr><td>my</td><td>mine</td></tr><tr><td>your</td><td>yours</td></tr></table>"
    )
    raw_table = (
        "<table><tr><td>Possessiveadjectives</td><td>Possessivepronouns</td></tr>"
        "<tr><td>my</td><td>mine</td></tr><tr><td>your</td><td>yours</td></tr></table>"
    )
    (clean_dir / "clean.md").write_text(f"# Unit 1\n{clean_table}\n", encoding="utf-8")
    write_minimal_reports(clean_dir, html_tables=1)
    (raw_dir / "content_list.json").write_text(
        json.dumps(
            [
                {
                    "type": "table",
                    "table_body": raw_table,
                    "page_idx": 21,
                    "bbox": [118, 324, 482, 600],
                }
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "manifest.json").write_text(
        json.dumps({"source_root": str(raw_dir), "content_file": "content_list.json"}),
        encoding="utf-8",
    )
    stub_pdf_render(monkeypatch, standard)

    standard.build_package(clean_dir, out_dir, raw_dir, chrome=None, source_pdf_path=source_pdf)
    packets = standard.read_json(out_dir / "standard_visual_review_packets.json")

    assert packets["items"][0]["source_page_number"] == 22
    assert packets["items"][0]["source_bbox"] == [118, 324, 482, 600]
    assert packets["items"][0]["crop_status"] == "ready_for_source_crop"


def test_table_source_fallback_uses_text_cell_coverage_for_manual_review():
    close_review = load_close_review_module()
    clean_table = (
        "<table><tr><td>Affirmative</td><td>Negative</td><td>Questions</td><td>Short answers</td></tr>"
        "<tr><td>I've playedyou've playedit's playedwe've playedthey've played</td>"
        "<td>I haven't playedyou haven't playedit hasn't playedwe haven't playedthey haven't played</td>"
        "<td>Have I played?Have you played?Has it played?Have we played?Have they played?</td>"
        "<td>Yes, I have.Yes, you have.Yes, it has.Yes, we have.Yes, they have.</td>"
        "<td>No, I haven't.No, you haven't.No, it hasn't.No, we haven't.No, they haven't.</td></tr></table>"
    )
    raw_rows = [
        {"type": "text", "text": "Affirmative", "page_idx": 79, "bbox": [37, 89, 144, 108], "_raw_index": 1},
        {"type": "text", "text": "I've played\nyou've played\nit's played\nwe've played\nthey've played", "page_idx": 79, "bbox": [37, 109, 176, 195], "_raw_index": 2},
        {"type": "text", "text": "Negative", "page_idx": 79, "bbox": [198, 90, 281, 108], "_raw_index": 3},
        {"type": "text", "text": "I haven't played\nyou haven't played\nit hasn't played\nwe haven't played\nthey haven't played", "page_idx": 79, "bbox": [196, 109, 380, 194], "_raw_index": 4},
        {"type": "text", "text": "Questions", "page_idx": 79, "bbox": [395, 90, 488, 106], "_raw_index": 5},
        {"type": "text", "text": "Have I played?\nHave you played?\nHas it played?\nHave we played?\nHave they played?", "page_idx": 79, "bbox": [395, 109, 565, 194], "_raw_index": 6},
        {"type": "text", "text": "Short answers", "page_idx": 79, "bbox": [584, 90, 713, 104], "_raw_index": 7},
        {"type": "text", "text": "Yes, I have.\nYes, you have.\nYes, it has.\nYes, we have.\nYes, they have.", "page_idx": 79, "bbox": [584, 109, 717, 193], "_raw_index": 8},
        {"type": "text", "text": "No, I haven't.\nNo, you haven't.\nNo, it hasn't.\nNo, we haven't.\nNo, they haven't.", "page_idx": 79, "bbox": [735, 108, 890, 193], "_raw_index": 9},
    ]

    evidence = close_review.find_table_source_fallback(clean_table, raw_rows)

    assert evidence["raw_type"] == "text_cell_coverage_bbox_union"
    assert evidence["match_rule"] == "raw_content_list.text_cell_coverage_bbox_union_for_manual_review"
    assert evidence["page_number"] == 80
    assert evidence["bbox"] == [37, 89, 890, 195]
    assert evidence["match_score"] == 1.0


def test_table_source_fallback_prefers_compact_window_with_repeated_headers():
    close_review = load_close_review_module()
    clean_table = (
        "<table><tr><td>Affirmative</td><td>Negative</td><td>Questions</td><td>Short answers</td></tr>"
        "<tr><td>I was playingyou were playingit was playingwe were playingthey were playing</td>"
        "<td>I wasn't playingyou weren't playingit wasn't playingwe weren't playingthey weren't playing</td>"
        "<td>Was I playing?Were you playing?Was it playing?Were we playing?Were they playing?</td>"
        "<td>Yes, I was.Yes, you were.Yes, it was.Yes, we were.Yes, they were.</td>"
        "<td>No, I wasn't.No, you weren't.No, it wasn't.No, we weren't.No, they weren't.</td></tr></table>"
    )
    raw_rows = [
        {"type": "text", "text": "Affirmative", "page_idx": 79, "bbox": [37, 89, 144, 108], "_raw_index": 1},
        {"type": "text", "text": "I've played\nyou've played\nit's played\nwe've played\nthey've played", "page_idx": 79, "bbox": [37, 109, 176, 195], "_raw_index": 2},
        {"type": "text", "text": "Negative", "page_idx": 79, "bbox": [198, 90, 281, 108], "_raw_index": 3},
        {"type": "text", "text": "Short answers", "page_idx": 79, "bbox": [584, 90, 713, 104], "_raw_index": 4},
        {"type": "text", "text": "Affirmative", "page_idx": 79, "bbox": [38, 283, 144, 303], "_raw_index": 5},
        {"type": "text", "text": "I was playing\nyou were playing\nit was playing\nwe were playing\nthey were playing", "page_idx": 79, "bbox": [38, 304, 205, 388], "_raw_index": 6},
        {"type": "text", "text": "Negative", "page_idx": 79, "bbox": [222, 285, 304, 301], "_raw_index": 7},
        {"type": "text", "text": "I wasn't playing\nyou weren't playing\nit wasn't playing\nwe weren't playing\nthey weren't playing", "page_idx": 79, "bbox": [220, 303, 412, 388], "_raw_index": 8},
        {"type": "text", "text": "Questions", "page_idx": 79, "bbox": [430, 283, 521, 300], "_raw_index": 9},
        {"type": "text", "text": "Was I playing?\nWere you playing?\nWas it playing?\nWere we playing?\nWere they playing?", "page_idx": 79, "bbox": [430, 303, 607, 388], "_raw_index": 10},
        {"type": "text", "text": "Short answers", "page_idx": 79, "bbox": [624, 283, 754, 300], "_raw_index": 11},
        {"type": "text", "text": "Yes, I was.\nYes, you were.\nYes, it was.\nYes, we were.\nYes, they were.", "page_idx": 79, "bbox": [624, 303, 759, 387], "_raw_index": 12},
        {"type": "text", "text": "No, I wasn't.\nNo, you weren't.\nNo, it wasn't.\nNo, we weren't.\nNo, they weren't.", "page_idx": 79, "bbox": [774, 301, 930, 387], "_raw_index": 13},
    ]

    evidence = close_review.find_table_source_fallback(clean_table, raw_rows)

    assert evidence["match_rule"] == "raw_content_list.text_cell_coverage_bbox_union_for_manual_review"
    assert evidence["bbox"] == [38, 283, 930, 388]


def test_table_visual_packets_keep_full_text_for_rule_matching(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    raw_dir = tmp_path / "raw"
    out_dir = tmp_path / "standard-final"
    source_pdf = tmp_path / "source.pdf"
    clean_dir.mkdir()
    raw_dir.mkdir()
    source_pdf.write_bytes(b"%PDF-1.4 source")
    rows = "".join(f"<tr><td>{index}</td><td>{'word ' * 12}</td></tr>" for index in range(80))
    table_html = f"<table><tr><td>Index</td><td>Text</td></tr>{rows}</table>"
    assert len(table_html) > 1000
    (clean_dir / "clean.md").write_text(f"# Unit 1\n{table_html}\n", encoding="utf-8")
    write_minimal_reports(clean_dir, html_tables=1)
    (raw_dir / "content_list.json").write_text(
        json.dumps([{"type": "table", "table_body": table_html, "page_idx": 2, "bbox": [10, 20, 900, 940]}]),
        encoding="utf-8",
    )
    (raw_dir / "manifest.json").write_text(
        json.dumps({"source_root": str(raw_dir), "content_file": "content_list.json"}),
        encoding="utf-8",
    )
    stub_pdf_render(monkeypatch, standard)

    standard.build_package(clean_dir, out_dir, raw_dir, chrome=None, source_pdf_path=source_pdf)
    packet = standard.read_json(out_dir / "standard_visual_review_packets.json")["items"][0]

    assert len(packet["clean_text"]) > 1000
    assert len(packet["source_content"]) > 1000
    assert standard.normalize_review_text(packet["clean_text"]) == standard.normalize_review_text(packet["source_content"])


def test_paired_vocabulary_table_reconstructs_source_blank_boxes():
    standard = load_standard_module()
    table_html = (
        "<table><tr><td>Definition</td><td>Example</td></tr>"
        "<tr><td>1. You when something happens.</td><td>Use the to explain it.</td></tr>"
        "<tr><td>2. A is a(n).</td><td>3. The states a fact & compares x < y.</td></tr>"
        "</table>"
    )

    rendered = standard.render_table_with_answer_spaces(table_html)

    assert rendered.count("answer-line-source") == 5
    assert "x &lt; y" in rendered
    assert "<td>1. You <span" in rendered


def test_profile_can_be_forced_to_reading_textbook(tmp_path, monkeypatch):
    standard = load_standard_module()
    clean_dir = tmp_path / "clean"
    out_dir = tmp_path / "standard-final"
    clean_dir.mkdir()
    (clean_dir / "clean.md").write_text("# Unit 1\n1 Complete the sentences.\n", encoding="utf-8")
    write_minimal_reports(clean_dir)
    stub_pdf_render(monkeypatch, standard)

    acceptance = standard.build_package(clean_dir, out_dir, None, chrome=None, profile="reading_textbook")
    document = standard.read_json(out_dir / "standard_document.json")

    assert document["profile"] == "reading_textbook"
    assert acceptance["gates"]["profile_coverage"]["status"] == "pass"
