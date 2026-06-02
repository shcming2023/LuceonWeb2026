from __future__ import annotations

import json
import sys
import tempfile
import time
import types
from pathlib import Path

sys.modules.setdefault("boto3", types.SimpleNamespace(client=lambda *args, **kwargs: None))


def _fake_adaptive_chunk(items, chunk_size=None, overlap=1):
    size = max(1, int(chunk_size or 10))
    ranges = []
    chunks = []
    for start in range(0, len(items), size):
        chunk = items[start:start + size]
        if not chunk:
            continue
        ranges.append([chunk[0]["page"], chunk[-1]["page"]])
        chunks.append(chunk)
    return ranges, chunks


sys.modules.setdefault("inference", types.SimpleNamespace(
    safe_doc_stem=lambda value: str(value),
    filter_contd=lambda blocks: blocks,
    add_contd=lambda blocks: blocks,
    filter_title=lambda blocks: blocks,
    add_title=lambda blocks: blocks,
    filter_image=lambda blocks: (blocks, {}),
    add_image=lambda blocks: blocks,
    parse_string_notype=lambda blocks: blocks,
    parse_string_type=lambda blocks: blocks,
    adaptive_chunk=_fake_adaptive_chunk,
))

from luceon_service import service
from luceon_service import chunk_checkpoint_runner


def make_pages(count: int) -> dict[str, list[dict]]:
    return {
        str(page): [
            {"type": "text", "content": f"page {page} text", "bbox": [0.1, 0.1, 0.2, 0.2]},
            {"type": "title", "content": f"heading {page}", "bbox": [0.1, 0.2, 0.2, 0.3]},
        ]
        for page in range(1, count + 1)
    }


def test_wrapped_normalized_label_counts_pages_and_chunks():
    payload = {
        "model": "mineru",
        "doc_id": "4134323036518274",
        "input_label": "4134323036518274",
        "pages": make_pages(891),
    }

    estimate = service._estimate_toc_rebuild(payload, chunk_size=10)

    assert estimate["normalized_pages"] == 891
    assert estimate["normalized_blocks"] == 1782
    assert estimate["inference_chunks_total"] > 250
    assert estimate["inference_chunks_total"] < 320
    assert estimate["chunks_by_task"]["contd"] > 80
    assert estimate["chunks_by_task"]["title"] > 80
    assert estimate["chunks_by_task"]["image"] > 80


def test_bounded_payload_keeps_large_original_estimate_but_limits_selected_work():
    payload = {
        "model": "mineru",
        "doc_id": "4134323036518274",
        "input_label": "4134323036518274",
        "pages": make_pages(891),
    }

    bounded_payload, plan = service._build_bounded_payload(payload, chunk_size=10)

    assert plan["mode"] == "bounded-preview"
    assert plan["original"]["normalized_pages"] == 891
    assert plan["selected"]["normalized_pages"] <= service.BOUNDED_PAGE_LIMIT
    assert plan["selected"]["inference_chunks_total"] <= service.BOUNDED_CHUNK_LIMIT
    assert len(bounded_payload["pages"]) == plan["selected"]["normalized_pages"]
    assert bounded_payload["luceon_invocation"]["mode"] == "bounded-preview"
    assert bounded_payload["luceon_invocation"]["source_pages"] == 891


def test_live_progress_reads_real_pages_and_raw_chunk_metadata():
    payload = {
        "model": "mineru",
        "doc_id": "4134323036518274",
        "input_label": "4134323036518274",
        "pages": make_pages(891),
    }

    with tempfile.TemporaryDirectory() as tmp:
        old_work_root = service.WORK_ROOT
        try:
            service.WORK_ROOT = Path(tmp)
            job_id = "luceon-task-1780291805535-toc-rebuild-v2-1780298498453"
            outputs = service.WORK_ROOT / job_id / "outputs"
            label_dir = outputs / "label_normalization" / "mineru"
            raw_dir = outputs / "inference_raw" / "mineru" / "4134323036518274"
            label_dir.mkdir(parents=True)
            raw_dir.mkdir(parents=True)
            (label_dir / "4134323036518274.json").write_text(json.dumps(payload), encoding="utf-8")
            (raw_dir / "contd_chunk_0000.json").write_text(json.dumps({
                "task": "contd",
                "chunk_index": 0,
                "range": [1, 16],
                "pages": [1, 2, 3, 4, 5, 12, 13, 14, 15, 16],
                "parsed": [[{"src_id": 1, "tgt_id": 2}]],
            }), encoding="utf-8")

            progress = service._get_live_progress({
                "payload": {"job_id": job_id, "material_id": "4134323036518274"},
                "start_time": time.time(),
                "current_step": "running_inference",
            })
        finally:
            service.WORK_ROOT = old_work_root

    assert progress["normalized_pages"] == 891
    assert progress["inference_chunks_total"] > 250
    assert progress["inference_chunks_completed"] == 1
    assert progress["chunks_by_task"] == {"contd": 1}
    assert progress["last_completed_chunk"] == "contd_chunk_0000.json"
    assert progress["active_chunk"] == "contd_chunk_0001.json"
    assert progress["inference_blocks_validated"] == 1


def test_full_background_runner_uses_explicit_micro_chunk_size():
    doc_blocks = []
    for page in range(1, 31):
        doc_blocks.append({
            "id": page,
            "type": "text",
            "page": page,
            "box": [0, 0, 10, 10],
            "content": f"page {page}",
            "contd": -1,
            "level": -1,
            "image": -1,
        })

    large_chunks, _ = chunk_checkpoint_runner._build_chunks(doc_blocks, chunk_size=10)
    micro_chunks, _ = chunk_checkpoint_runner._build_chunks(doc_blocks, chunk_size=4)

    assert len(micro_chunks["contd"]["chunks"]) > len(large_chunks["contd"]["chunks"])
    assert len(micro_chunks["title"]["chunks"]) > len(large_chunks["title"]["chunks"])
    assert len(micro_chunks["image"]["chunks"]) > len(large_chunks["image"]["chunks"])


def test_profile_change_archives_legacy_raw_chunks_before_micro_resume():
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir = Path(tmp)
        legacy = raw_dir / "contd_chunk_0000.json"
        legacy.write_text(json.dumps({
            "task": "contd",
            "chunk_index": 0,
            "range": [1, 16],
            "pages": [1, 2, 3],
            "parsed": [],
        }), encoding="utf-8")

        chunk_checkpoint_runner._archive_incompatible_chunks(raw_dir, chunk_size=4)

        assert not legacy.exists()
        archived = list((raw_dir / "profile_archive").rglob("contd_chunk_0000.json"))
        assert len(archived) == 1
        checkpoint = json.loads((raw_dir / "checkpoint.json").read_text(encoding="utf-8"))
        assert checkpoint["status"] == "profile_reset"
        assert checkpoint["chunk_size"] == 4


if __name__ == "__main__":
    test_wrapped_normalized_label_counts_pages_and_chunks()
    test_bounded_payload_keeps_large_original_estimate_but_limits_selected_work()
    test_live_progress_reads_real_pages_and_raw_chunk_metadata()
    test_full_background_runner_uses_explicit_micro_chunk_size()
    test_profile_change_archives_legacy_raw_chunks_before_micro_resume()
    print("PASS popo invocation boundary tests")
