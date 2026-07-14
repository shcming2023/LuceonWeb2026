import json

import fitz

from app.workflow_v2.models import ModelCall, StageRun
from app.workflow_v2.visual_qa import _discard_blank_space_false_positives, _discard_unverified_source_footer_claims, _normalize_visual_rows, consensus_findings, review_all_pages
from test_workflow_v2 import make_sessions


class FakeResponse:
    status_code = 200
    text = ""

    def __init__(self, pages):
        self.pages = pages

    def json(self):
        return {"id": "vision-1", "choices": [{"message": {"content": json.dumps({"pages": [{"page": page, "status": "passed", "findings": [], "summary": "ok"} for page in self.pages]})}}], "usage": {"total_tokens": 10}}


class FakeClient:
    def __init__(self, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def post(self, *_args, **kwargs):
        text = kwargs["json"]["messages"][1]["content"][0]["text"]
        pages = json.loads(text.split("order ", 1)[1].split(". Return", 1)[0])
        return FakeResponse(pages)


def test_retained_visual_qa_utility_reviews_every_page_without_rejoining_core_workflow(monkeypatch, tmp_path):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test")
    monkeypatch.setattr("app.workflow_v2.visual_qa.httpx.Client", FakeClient)
    _old_db, db, material = make_sessions()
    from app.workflow_v2.service import create_workflow_job
    job, _ = create_workflow_job(db, user_id="u1", material=material)
    assert "independent_final_review" not in {row.stage_key for row in db.query(StageRun).all()}
    stage = StageRun(
        workflow_job_id=job.id,
        stage_key="independent_final_review",
        stage_version="retained-utility-only",
        attempt=1,
        status="running",
        owner="legacy_visual_qa",
    )
    db.add(stage)
    job.current_stage_key = "independent_final_review"
    db.flush()
    pdf = tmp_path / "book.pdf"
    document = fitz.open()
    for number in range(1, 6):
        page = document.new_page()
        page.insert_text((50, 80), f"Page {number}")
    document.save(pdf)
    document.close()

    report = review_all_pages(db, job=job, stage=stage, pdf=pdf, render_dir=tmp_path / "renders", batch_size=2)

    assert report["page_count"] == 5
    assert [row["page"] for row in report["pages"]] == [1, 2, 3, 4, 5]
    assert db.query(ModelCall).count() == 3


def test_visual_qa_contract_discards_non_layout_and_normal_page_break_findings():
    rows = _normalize_visual_rows([
        {
            "page": 2,
            "status": "failed",
            "summary": "mixed",
            "findings": [
                {"code": "PAGE_NUMBER_MISMATCH", "detail": "printed folio differs from physical page"},
                {"code": "WORKFLOW_RESIDUE", "detail": "normal 教材链接 metadata"},
                {"code": "SPLIT_SENTENCE", "detail": "paragraph continues normally across the page break"},
                {"code": "BROKEN_GLYPHS", "detail": "missing glyph boxes are visible"},
            ],
        }
    ])

    assert rows == [{
        "page": 2,
        "status": "failed",
        "findings": [{"code": "BROKEN_GLYPHS", "detail": "missing glyph boxes are visible"}],
        "summary": "mixed",
    }]


def test_visual_qa_consensus_keeps_only_independently_confirmed_codes():
    initial = [
        {"code": "OVERLAP", "detail": "initial overlap"},
        {"code": "BROKEN_GLYPHS", "detail": "initial glyph report"},
    ]
    confirmed = [
        {"code": "OVERLAP", "detail": "confirmed overlap"},
        {"code": "CLIPPING", "detail": "new unconfirmed code"},
    ]

    assert consensus_findings(initial, confirmed) == [{"code": "OVERLAP", "detail": "initial overlap"}]


def test_visual_qa_three_way_consensus_requires_both_single_page_confirmations():
    initial = [{"code": "OVERLAP", "detail": "initial overlap"}]

    assert consensus_findings(initial, [{"code": "OVERLAP"}], []) == []
    assert consensus_findings(initial, [{"code": "OVERLAP"}], [{"code": "OVERLAP"}]) == initial


def test_visual_qa_discards_source_footer_claim_absent_from_current_page_ocr(monkeypatch, tmp_path):
    image = tmp_path / "page.png"
    image.write_bytes(b"png")
    monkeypatch.setattr("app.workflow_v2.visual_qa.shutil.which", lambda _name: "/usr/bin/tesseract")
    monkeypatch.setattr(
        "app.workflow_v2.visual_qa.subprocess.run",
        lambda *_args, **_kwargs: type("Result", (), {"stdout": "Angelina Jolie speech page"})(),
    )
    rows = [{
        "page": 71,
        "image": str(image),
        "status": "failed",
        "findings": [{"code": "OVERLAP", "detail": "The text '84 Section 1: Building key skills' overlaps the photo."}],
    }]

    _discard_unverified_source_footer_claims(rows)

    assert rows[0]["status"] == "passed"
    assert rows[0]["findings"] == []
    assert rows[0]["evidence_adjustments"][0]["claim"] == "84 Section 1: Building key skills"


def test_blank_space_finding_requires_low_page_text_density(tmp_path):
    pdf = tmp_path / "dense.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(fitz.Rect(40, 40, 550, 800), "Dense textbook text " * 80, fontsize=10)
    document.save(pdf)
    document.close()
    rows = [{"page": 1, "status": "failed", "findings": [{"code": "EXCESSIVE_BLANK_SPACE", "detail": "claimed blank"}]}]

    _discard_blank_space_false_positives(pdf, rows)

    assert rows[0]["status"] == "passed"
    assert rows[0]["findings"] == []


def test_visual_qa_discards_text_layer_proven_glyph_and_continuation_false_positives(tmp_path):
    pdf = tmp_path / "continuation.pdf"
    document = fitz.open()
    first = document.new_page()
    first.insert_text((40, 80), "No matter how")
    second = document.new_page()
    second.insert_text((40, 80), "good your opinions are, soccer's history remains clear.")
    document.save(pdf)
    document.close()
    rows = [{
        "page": 2,
        "status": "failed",
        "findings": [
            {"code": "CLIPPING", "detail": "The first line begins mid-sentence."},
            {"code": "BROKEN_GLYPHS", "detail": "The word 'soccer's' has a detached apostrophe."},
        ],
    }]

    _discard_blank_space_false_positives(pdf, rows)

    assert rows[0]["status"] == "passed"
    assert rows[0]["findings"] == []


def test_visual_qa_accepts_ruled_chapter_end_practice_space(tmp_path):
    pdf = tmp_path / "chapter-tail.pdf"
    document = fitz.open()
    tail = document.new_page()
    tail.insert_text((40, 80), "5. Complete the final translation exercise on this ruled page.")
    tail.draw_line((40, 120), (550, 120))
    tail.draw_line((40, 180), (550, 180))
    chapter = document.new_page()
    chapter.insert_text((40, 80), "Chapter 2 New Lesson")
    document.save(pdf)
    document.close()
    rows = [{"page": 1, "status": "failed", "findings": [{"code": "EXCESSIVE_BLANK_SPACE", "detail": "mostly blank"}]}]

    _discard_blank_space_false_positives(pdf, rows)

    assert rows[0]["status"] == "passed"


def test_visual_qa_accepts_image_only_writing_page_with_four_rules_before_chapter(tmp_path):
    pdf = tmp_path / "image-writing-page.pdf"
    document = fitz.open()
    tail = document.new_page()
    tail.draw_rect(fitz.Rect(120, 60, 420, 260))
    for y in (320, 370, 420, 470):
        tail.draw_line((40, y), (550, y))
    chapter = document.new_page()
    chapter.insert_text((40, 80), "Chapter 3 New Lesson")
    document.save(pdf)
    document.close()
    rows = [{"page": 1, "status": "failed", "findings": [{"code": "EXCESSIVE_BLANK_SPACE", "detail": "mostly blank"}]}]

    _discard_blank_space_false_positives(pdf, rows)

    assert rows[0]["status"] == "passed"


def test_visual_qa_accepts_complete_scored_exercise_tail_before_chapter(tmp_path):
    pdf = tmp_path / "scored-exercise-tail.pdf"
    document = fitz.open()
    tail = document.new_page()
    tail.insert_text((40, 80), "5.4 Probability and Statistics")
    tail.insert_text((40, 110), "Find the value of a and the value of b. [1]")
    tail.insert_text((40, 140), "(d) Use the table in part (c) to calculate a new estimate of the mean time. [3]")
    chapter = document.new_page()
    chapter.insert_text((40, 80), "Chapter 6 Unit 6")
    document.save(pdf)
    document.close()
    rows = [{"page": 1, "status": "failed", "findings": [{"code": "EXCESSIVE_BLANK_SPACE", "detail": "mostly blank"}]}]

    _discard_blank_space_false_positives(pdf, rows)

    assert rows[0]["status"] == "passed"


def test_visual_qa_keeps_incomplete_short_tail_before_chapter(tmp_path):
    pdf = tmp_path / "incomplete-tail.pdf"
    document = fitz.open()
    tail = document.new_page()
    tail.insert_text((40, 80), "5.4 Probability and Statistics")
    tail.insert_text((40, 110), "(d) Use the missing table to calculate")
    chapter = document.new_page()
    chapter.insert_text((40, 80), "Chapter 6 Unit 6")
    document.save(pdf)
    document.close()
    rows = [{"page": 1, "status": "failed", "findings": [{"code": "EXCESSIVE_BLANK_SPACE", "detail": "mostly blank"}]}]

    _discard_blank_space_false_positives(pdf, rows)

    assert rows[0]["status"] == "failed"
