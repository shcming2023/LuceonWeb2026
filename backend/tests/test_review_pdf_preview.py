import shutil
from pathlib import Path
from types import SimpleNamespace

import fitz

from app.services.review_pdf_preview import ensure_review_pdf_preview, ensure_review_pdf_preview_isolated


def _source_pdf(page_count: int = 3) -> bytes:
    document = fitz.open()
    for index in range(page_count):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Review page {index + 1}", fontsize=24)
        page.draw_rect(fitz.Rect(72, 140, 520, 760), color=(0.1, 0.4, 0.8), fill=(0.95, 0.97, 1))
    content = document.tobytes(garbage=4, deflate=True)
    document.close()
    return content


def test_review_pdf_preview_preserves_pages_and_reuses_cache(tmp_path: Path):
    source = _source_pdf()
    output = tmp_path / "preview.pdf"

    preview = ensure_review_pdf_preview(
        source,
        output,
        source_size=50 * 1024 * 1024,
        dpi=72,
        jpeg_quality=50,
    )

    assert preview is not None
    assert preview.path == output
    assert preview.page_count == 3
    assert preview.size == output.stat().st_size
    if shutil.which("qpdf"):
        assert preview.linearized is True
    with fitz.open(output) as document:
        assert document.page_count == 3
        assert document[0].get_pixmap().width > 0
        assert document[-1].get_pixmap().height > 0

    cached = ensure_review_pdf_preview(b"", output, source_size=50 * 1024 * 1024)
    assert cached is not None
    assert cached.size == preview.size


def test_review_pdf_preview_skips_output_that_is_not_smaller(tmp_path: Path):
    output = tmp_path / "preview.pdf"

    preview = ensure_review_pdf_preview(_source_pdf(1), output, source_size=1, dpi=72, jpeg_quality=50)

    assert preview is None
    assert not output.exists()
    assert output.with_suffix(".skip").exists()
    assert ensure_review_pdf_preview(b"", output, source_size=1) is None


def test_review_pdf_preview_isolated_worker_builds_cache(tmp_path: Path):
    output = tmp_path / "preview.pdf"

    preview = ensure_review_pdf_preview_isolated(
        _source_pdf(4),
        output,
        source_size=50 * 1024 * 1024,
        dpi=72,
        jpeg_quality=50,
        max_edge=1000,
    )

    assert preview is not None
    assert preview.page_count == 4
    assert output.exists()
    assert not list(tmp_path.glob("*.source.pdf"))
    assert not list(tmp_path.glob("*.pages"))


def test_review_pdf_preview_isolated_worker_failure_is_safe(monkeypatch, tmp_path: Path):
    output = tmp_path / "preview.pdf"
    monkeypatch.setattr(
        "app.services.review_pdf_preview.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=137, stderr="killed"),
    )

    preview = ensure_review_pdf_preview_isolated(
        _source_pdf(2),
        output,
        source_size=50 * 1024 * 1024,
    )

    assert preview is None
    assert not output.exists()
    assert not list(tmp_path.glob("*.source.pdf"))
