import argparse
import logging
import os
import shutil
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

import fitz


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReviewPdfPreview:
    path: Path
    page_count: int
    size: int
    linearized: bool


_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.Lock:
    key = str(path)
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.Lock())


def _inspect_preview(path: Path) -> ReviewPdfPreview:
    with path.open("rb") as handle:
        linearized = b"/Linearized" in handle.read(4096)
    with fitz.open(path) as document:
        page_count = document.page_count
    return ReviewPdfPreview(
        path=path,
        page_count=page_count,
        size=path.stat().st_size,
        linearized=linearized,
    )


def _linearize_pdf(source: Path, target: Path) -> bool:
    qpdf = shutil.which("qpdf")
    if not qpdf:
        source.replace(target)
        return False
    completed = subprocess.run(
        [qpdf, "--linearize", "--object-streams=generate", "--compression-level=9", str(source), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode not in {0, 3} or not target.exists():
        source.replace(target)
        return False
    source.unlink(missing_ok=True)
    return True


def _merge_page_pdfs(page_paths: list[Path], target: Path) -> None:
    qpdf = shutil.which("qpdf")
    if qpdf:
        completed = subprocess.run(
            [qpdf, "--empty", "--pages", *(str(path) for path in page_paths), "--", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0 and target.exists():
            return
        target.unlink(missing_ok=True)

    merged = fitz.open()
    try:
        for page_path in page_paths:
            with fitz.open(page_path) as page_document:
                merged.insert_pdf(page_document)
        merged.save(target, garbage=4, deflate=True)
    finally:
        merged.close()


def _rasterize_pdf_bounded(
    source_pdf: bytes,
    target: Path,
    page_dir: Path,
    *,
    dpi: int,
    jpeg_quality: int,
    max_edge: int,
) -> int:
    """Rasterize one page at a time so a whole book is never retained as pixmaps in memory."""
    page_dir.mkdir(parents=True, exist_ok=False)
    source_path = page_dir / "source.pdf"
    source_path.write_bytes(source_pdf)
    source_document = fitz.open(source_path)
    page_paths: list[Path] = []
    try:
        page_count = source_document.page_count
        for page_index in range(page_count):
            source_page = source_document.load_page(page_index)
            try:
                scale = dpi / 72
                longest_edge = max(source_page.rect.width, source_page.rect.height)
                if longest_edge * scale > max_edge:
                    scale = max_edge / longest_edge
                pixmap = source_page.get_pixmap(
                    matrix=fitz.Matrix(scale, scale),
                    colorspace=fitz.csRGB,
                    alpha=False,
                )
                jpeg = pixmap.tobytes("jpeg", jpg_quality=jpeg_quality)
                page_document = fitz.open()
                try:
                    preview_page = page_document.new_page(
                        width=source_page.rect.width,
                        height=source_page.rect.height,
                    )
                    preview_page.insert_image(preview_page.rect, stream=jpeg)
                    page_path = page_dir / f"{page_index + 1:06d}.pdf"
                    page_document.save(page_path, garbage=4, deflate=True)
                    page_paths.append(page_path)
                finally:
                    page_document.close()
            finally:
                fitz.TOOLS.store_shrink(100)
        _merge_page_pdfs(page_paths, target)
        return page_count
    finally:
        source_document.close()


def ensure_review_pdf_preview(
    source_pdf: bytes,
    output_path: Path,
    *,
    source_size: int,
    dpi: int = 120,
    jpeg_quality: int = 58,
    max_edge: int = 2000,
) -> ReviewPdfPreview | None:
    """Build an immutable visual-only review PDF; return None when it is not smaller."""
    skip_path = output_path.with_suffix(".skip")
    with _lock_for(output_path):
        if output_path.exists():
            try:
                return _inspect_preview(output_path)
            except Exception:
                output_path.unlink(missing_ok=True)
        if skip_path.exists():
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        token = f"{os.getpid()}-{threading.get_ident()}-{uuid.uuid4().hex}"
        raster_path = output_path.with_name(f"{output_path.stem}.{token}.raster.pdf")
        final_path = output_path.with_name(f"{output_path.stem}.{token}.final.pdf")
        page_dir = output_path.with_name(f"{output_path.stem}.{token}.pages")
        try:
            page_count = _rasterize_pdf_bounded(
                source_pdf,
                raster_path,
                page_dir,
                dpi=dpi,
                jpeg_quality=jpeg_quality,
                max_edge=max_edge,
            )
            _linearize_pdf(raster_path, final_path)
            result = _inspect_preview(final_path)
            if result.page_count != page_count:
                raise ValueError(f"review PDF page count mismatch: {result.page_count} != {page_count}")
            if result.size >= source_size:
                skip_path.write_text("preview is not smaller than source\n", encoding="utf-8")
                return None
            final_path.replace(output_path)
            return _inspect_preview(output_path)
        finally:
            raster_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            shutil.rmtree(page_dir, ignore_errors=True)


def _cleanup_preview_temporary_files(output_path: Path) -> None:
    for path in output_path.parent.glob(f"{output_path.stem}.*"):
        if path == output_path or path == output_path.with_suffix(".skip"):
            continue
        if path.is_dir() and path.name.endswith(".pages"):
            shutil.rmtree(path, ignore_errors=True)
        elif path.name.endswith((".raster.pdf", ".final.pdf", ".source.pdf")):
            path.unlink(missing_ok=True)


def ensure_review_pdf_preview_isolated(
    source_pdf: bytes,
    output_path: Path,
    *,
    source_size: int,
    dpi: int = 120,
    jpeg_quality: int = 58,
    max_edge: int = 2000,
    timeout_seconds: int = 180,
) -> ReviewPdfPreview | None:
    """Build the preview in a memory-limited child so a hostile PDF cannot kill the API."""
    skip_path = output_path.with_suffix(".skip")
    with _lock_for(output_path):
        if output_path.exists():
            try:
                return _inspect_preview(output_path)
            except Exception:
                output_path.unlink(missing_ok=True)
        if skip_path.exists():
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        token = f"{os.getpid()}-{threading.get_ident()}-{uuid.uuid4().hex}"
        source_path = output_path.with_name(f"{output_path.stem}.{token}.source.pdf")
        source_path.write_bytes(source_pdf)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    str(source_path),
                    str(output_path),
                    str(source_size),
                    str(dpi),
                    str(jpeg_quality),
                    str(max_edge),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
            if completed.returncode != 0:
                logger.warning(
                    "review PDF preview worker failed with code %s: %s",
                    completed.returncode,
                    completed.stderr.strip(),
                )
                return None
            if output_path.exists():
                return _inspect_preview(output_path)
            return None
        except subprocess.TimeoutExpired:
            logger.warning("review PDF preview worker timed out after %s seconds", timeout_seconds)
            return None
        finally:
            source_path.unlink(missing_ok=True)
            _cleanup_preview_temporary_files(output_path)


def _set_worker_memory_limit() -> None:
    try:
        import resource

        limit = 3 * 1024 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    except (ImportError, OSError, ValueError):
        pass


def _worker_main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("source_size", type=int)
    parser.add_argument("dpi", type=int)
    parser.add_argument("jpeg_quality", type=int)
    parser.add_argument("max_edge", type=int)
    options = parser.parse_args(arguments)
    if not options.worker:
        return 2
    _set_worker_memory_limit()
    preview = ensure_review_pdf_preview(
        Path(options.source).read_bytes(),
        Path(options.output),
        source_size=options.source_size,
        dpi=options.dpi,
        jpeg_quality=options.jpeg_quality,
        max_edge=options.max_edge,
    )
    return 0 if preview or Path(options.output).with_suffix(".skip").exists() else 1


if __name__ == "__main__":
    raise SystemExit(_worker_main(sys.argv[1:]))
