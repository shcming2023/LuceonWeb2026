from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
POST_PROCESSING_DIR = REPO_ROOT / "post_processing"
DATA_ENGINE_DIR = REPO_ROOT / "data_engine"
sys.path.insert(0, str(POST_PROCESSING_DIR))
sys.path.insert(0, str(DATA_ENGINE_DIR))

import inference  # type: ignore  # noqa: E402


def _safe_doc_stem(value: str) -> str:
    return inference.safe_doc_stem(value)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_pages(path: Path, pdf_path: Path) -> tuple[str, dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"normalized input must be a JSON object: {path}")
    input_label = str(payload.get("input_label") or pdf_path)
    pages = payload.get("pages") if isinstance(payload.get("pages"), dict) else payload
    if not isinstance(pages, dict):
        raise ValueError(f"normalized pages must be a JSON object: {path}")
    return input_label, pages


def _prepare_doc_blocks(pages: dict[str, Any]) -> list[dict[str, Any]]:
    doc_blocks: list[dict[str, Any]] = []
    idx = 1
    for page_num in sorted(pages.keys(), key=lambda value: int(value) if str(value).isdigit() else str(value)):
        blocks = pages[page_num]
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            item = copy.deepcopy(block)
            item["page"] = int(page_num)
            item["id"] = idx
            idx += 1
            item["contd"] = -1
            item["level"] = -1
            item["image"] = -1
            doc_blocks.append(item)
    return doc_blocks


def _chunk_path(raw_doc_dir: Path, task: str, index: int) -> Path:
    return raw_doc_dir / f"{task}_chunk_{index:04d}.json"


def _read_raw_records(raw_doc_dir: Path, task: str) -> list[dict[str, Any]]:
    records = []
    for path in sorted(raw_doc_dir.glob(f"{task}_chunk_*.json")):
        try:
            data = _read_json(path)
        except Exception:
            continue
        if isinstance(data, dict):
            records.append(data)
    return sorted(records, key=lambda item: int(item.get("chunk_index") or 0))


def _unique_extend(target: list[dict[str, Any]], values: list[dict[str, Any]]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _chunk_pages(chunk: list[dict[str, Any]], rng: list[int]) -> list[int]:
    pages = sorted(set(block["page"] for block in chunk))
    return [page for page in pages if rng[0] <= page <= rng[1]]


def _run_contd_chunk(raw_doc_dir: Path, input_label: str, index: int, rng: list[int], chunk: list[dict[str, Any]]) -> None:
    pages = _chunk_pages(chunk, rng)
    image = inference.concatenate_pdf_pages_with_border(input_label, pages)
    prompt = "\n".join(
        f"<|id|>{block['id']}<|page|>{block['page']}<|box|>{block['box']}<|content|>{block['content']}"
        for block in chunk
    )
    prompt = "<image>\nTruncation Detection: " + prompt
    raw_response = inference.popo_generate(prompt, image)
    parsed = inference.extract_label1(raw_response.replace("<|from|>", "<|src_id|>").replace("<|to|>", "<|tgt_id|>"))
    inference.write_raw_record(str(raw_doc_dir), "contd", index, rng, pages, prompt, raw_response, parsed)


def _run_title_chunk(raw_doc_dir: Path, input_label: str, index: int, rng: list[int], chunk: list[dict[str, Any]]) -> None:
    pages = _chunk_pages(chunk, rng)
    image = inference.concatenate_pdf_pages_with_border(input_label, pages)
    prompt = "\n".join(
        f"<|id|>{block['id']}<|page|>{block['page']}<|box|>{block['box']}<|content|>{block['content']}"
        for block in chunk
    )
    prompt = "<image>\nTitle Level Analysis: " + prompt
    raw_response = inference.popo_generate(prompt, image)
    parsed = inference.extract_label2(raw_response)
    inference.write_raw_record(str(raw_doc_dir), "title", index, rng, pages, prompt, raw_response, parsed)


def _run_image_chunk(raw_doc_dir: Path, input_label: str, index: int, rng: list[int], chunk: list[dict[str, Any]]) -> None:
    pages = _chunk_pages(chunk, rng)
    image = inference.concatenate_pdf_pages_with_border(input_label, pages)
    prompt = "\n".join(
        f"<|id|>{block['id']}<|type|>{block['type']}<|page|>{block['page']}<|box|>{block['box']}<|content|>{block['content']}"
        for block in chunk
    )
    prompt = "<image>\nImage-Text Correlation Analysis: " + prompt
    raw_response = inference.popo_generate(prompt, image)
    parsed = inference.extract_label1(raw_response)
    inference.write_raw_record(str(raw_doc_dir), "image", index, rng, pages, prompt, raw_response, parsed)


def _build_chunks(doc_blocks: list[dict[str, Any]], chunk_size: int | None = None) -> tuple[dict[str, Any], dict[int, int]]:
    contd = inference.add_contd(inference.filter_contd(doc_blocks))
    title = inference.add_title(inference.filter_title(doc_blocks))
    image_judge_blocks, large_block_linking = inference.filter_image(doc_blocks)
    image = inference.add_image(image_judge_blocks)

    contd_ranges, contd_chunks = inference.adaptive_chunk(inference.parse_string_notype(contd), chunk_size=chunk_size)
    title_ranges, title_chunks = inference.adaptive_chunk(inference.parse_string_notype(title), chunk_size=chunk_size)
    image_ranges, image_chunks = inference.adaptive_chunk(inference.parse_string_type(image), chunk_size=chunk_size)

    return {
        "contd": {"ranges": contd_ranges, "chunks": contd_chunks},
        "title": {"ranges": title_ranges, "chunks": title_chunks},
        "image": {"ranges": image_ranges, "chunks": image_chunks},
    }, large_block_linking


def _apply_primary_labels(doc_blocks: list[dict[str, Any]], raw_doc_dir: Path, large_block_linking: dict[int, int]) -> None:
    contd_results: list[dict[str, Any]] = []
    for record in _read_raw_records(raw_doc_dir, "contd"):
        parsed = record.get("parsed") if isinstance(record.get("parsed"), list) else []
        _unique_extend(contd_results, parsed)

    image_results: list[dict[str, Any]] = []
    for record in _read_raw_records(raw_doc_dir, "image"):
        parsed = record.get("parsed") if isinstance(record.get("parsed"), list) else []
        _unique_extend(image_results, parsed)

    title_records = _read_raw_records(raw_doc_dir, "title")
    order_res: dict[int, list[dict[str, Any]]] = {}
    for record in title_records:
        rng = record.get("range")
        parsed = record.get("parsed") if isinstance(record.get("parsed"), list) else []
        if isinstance(rng, list) and len(rng) == 2:
            order_res[int(rng[0]) + int(rng[1])] = parsed

    title_results: list[dict[str, Any]] = []
    for _, id_pairs in sorted(order_res.items()):
        bias = []
        for pair in id_pairs:
            idx = pair.get("id")
            for exist in title_results:
                if idx == exist.get("id"):
                    if pair.get("level", -1) < 0 or exist.get("level", -1) < 0:
                        pair["level"] = -1
                        exist["level"] = -1
                    else:
                        bias.append(pair["level"] - exist["level"])
                        pair["level"] = exist["level"]
                    break

        avg_bias = round(sum(bias) / len(bias)) if bias else 0
        for pair in id_pairs:
            idx = pair.get("id")
            ext_flag = any(idx == exist.get("id") for exist in title_results)
            if not ext_flag:
                pair["level"] = pair["level"] - avg_bias if pair.get("level", -1) > 0 else pair.get("level", -1)
                title_results.append(pair)

    for label_pair in contd_results:
        try:
            doc_blocks[label_pair["src_id"]]["contd"] = label_pair["tgt_id"] + 1
        except Exception:
            pass
    for label_pair in image_results:
        try:
            doc_blocks[label_pair["src_id"]]["image"] = label_pair["tgt_id"] + 1
        except Exception:
            pass
    for label_pair in title_results:
        try:
            doc_blocks[label_pair["id"]]["level"] = label_pair["level"]
        except Exception:
            pass

    for src, tgt in large_block_linking.items():
        try:
            doc_blocks[src]["image"] = tgt + 1
        except Exception:
            pass


def _run_table_merge_chunk(raw_doc_dir: Path, index: int, merge_input: dict[str, Any]) -> None:
    prompt = inference.add_table_merge(merge_input["upper_row_ss"], merge_input["lower_row_ss"])
    raw_response = inference.popo_generate(prompt, None)
    parsed = inference.extract_last_coordinates(raw_response)
    inference.write_raw_record(
        str(raw_doc_dir),
        "table_merge",
        index,
        None,
        [],
        prompt,
        raw_response,
        parsed,
        extra={"table1_idx": merge_input["table1_idx"], "table2_idx": merge_input["table2_idx"]},
    )


def _apply_table_merge_labels(doc_blocks: list[dict[str, Any]], raw_doc_dir: Path) -> None:
    for block in doc_blocks:
        if block.get("type") == "table":
            block["table_merge"] = -1

    for record in _read_raw_records(raw_doc_dir, "table_merge"):
        parsed = record.get("parsed")
        table1_idx = record.get("table1_idx")
        table2_idx = record.get("table2_idx")
        if not parsed or not isinstance(parsed, list):
            continue
        if not isinstance(table1_idx, int) or not isinstance(table2_idx, int):
            continue
        try:
            doc_blocks[table1_idx]["table_merge"] = doc_blocks[table2_idx]["id"]
            doc_blocks[table2_idx]["table_merge"] = doc_blocks[table1_idx]["id"]
            doc_blocks[table1_idx]["cell_list"] = parsed
            doc_blocks[table2_idx]["cell_list"] = parsed
        except Exception:
            pass


def _write_checkpoint(raw_doc_dir: Path, payload: dict[str, Any]) -> None:
    payload = {**payload, "updated_at": time.time()}
    _write_json(raw_doc_dir / "checkpoint.json", payload)


def _read_existing_chunk_size(path: Path) -> int | None:
    try:
        data = _read_json(path)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    try:
        return int(data.get("chunk_size"))
    except (TypeError, ValueError):
        return None


def _annotate_chunk_size(path: Path, chunk_size: int) -> None:
    try:
        data = _read_json(path)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    data["chunk_size"] = chunk_size
    data["chunk_profile"] = "full-background-microchunk-v1"
    _write_json(path, data)


def _archive_incompatible_chunks(raw_doc_dir: Path, chunk_size: int) -> None:
    chunk_paths = sorted(raw_doc_dir.glob("*_chunk_*.json"))
    if not chunk_paths:
        return
    if all(_read_existing_chunk_size(path) == chunk_size for path in chunk_paths):
        return

    archive_dir = raw_doc_dir / "profile_archive" / f"chunk-size-{chunk_size}-{int(time.time())}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    for path in chunk_paths:
        path.rename(archive_dir / path.name)
    summary = raw_doc_dir / "summary.json"
    if summary.exists():
        summary.rename(archive_dir / summary.name)
    _write_checkpoint(raw_doc_dir, {
        "status": "profile_reset",
        "chunk_size": chunk_size,
        "archived_to": str(archive_dir),
        "reason": "existing raw chunks were produced by a different or unknown chunk profile",
    })


def _assemble_output(
    doc_blocks: list[dict[str, Any]],
    raw_doc_dir: Path,
    output_dir: Path,
    doc_stem: str,
    input_label: str,
    large_block_linking: dict[int, int],
) -> None:
    _apply_primary_labels(doc_blocks, raw_doc_dir, large_block_linking)
    _apply_table_merge_labels(doc_blocks, raw_doc_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / f"{doc_stem}.json"
    _write_json(output_json, doc_blocks)
    inference.write_raw_summary(
        str(raw_doc_dir),
        {
            "input_label": input_label,
            "output_json": str(output_json),
            "contd_records": len(_read_raw_records(raw_doc_dir, "contd")),
            "title_records": len(_read_raw_records(raw_doc_dir, "title")),
            "image_records": len(_read_raw_records(raw_doc_dir, "image")),
            "table_merge_records": len(_read_raw_records(raw_doc_dir, "table_merge")),
        },
    )


def run_next_chunk(args: argparse.Namespace) -> dict[str, Any]:
    normalized_input = Path(args.normalized_input)
    pdf_path = Path(args.pdf_path)
    output_dir = Path(args.output_dir)
    raw_doc_dir = Path(args.raw_doc_dir)
    raw_doc_dir.mkdir(parents=True, exist_ok=True)
    chunk_size = int(args.chunk_size)
    _archive_incompatible_chunks(raw_doc_dir, chunk_size)

    input_label, pages = _load_pages(normalized_input, pdf_path)
    if not Path(input_label).exists():
        input_label = str(pdf_path)
    doc_stem = args.doc_id or _safe_doc_stem(input_label)
    doc_blocks = _prepare_doc_blocks(pages)
    chunks_by_task, large_block_linking = _build_chunks(doc_blocks, chunk_size=chunk_size)
    plan = {task: len(value["chunks"]) for task, value in chunks_by_task.items()}

    for task in ("contd", "title", "image"):
        ranges = chunks_by_task[task]["ranges"]
        chunks = chunks_by_task[task]["chunks"]
        for index, (rng, chunk) in enumerate(zip(ranges, chunks)):
            if _chunk_path(raw_doc_dir, task, index).exists():
                continue
            _write_checkpoint(raw_doc_dir, {
                "status": "running_chunk",
                "task": task,
                "chunk_index": index,
                "chunk_size": chunk_size,
                "plan": plan,
            })
            if task == "contd":
                _run_contd_chunk(raw_doc_dir, input_label, index, rng, chunk)
            elif task == "title":
                _run_title_chunk(raw_doc_dir, input_label, index, rng, chunk)
            else:
                _run_image_chunk(raw_doc_dir, input_label, index, rng, chunk)
            _annotate_chunk_size(_chunk_path(raw_doc_dir, task, index), chunk_size)
            result = {
                "status": "partial",
                "completed_task": task,
                "completed_chunk_index": index,
                "chunk_size": chunk_size,
                "plan": plan,
            }
            _write_checkpoint(raw_doc_dir, result)
            return result

    _apply_primary_labels(doc_blocks, raw_doc_dir, large_block_linking)
    merge_inputs = inference.filter_table_merge(doc_blocks)
    for index, merge_input in enumerate(merge_inputs):
        if _chunk_path(raw_doc_dir, "table_merge", index).exists():
            continue
        _write_checkpoint(raw_doc_dir, {
            "status": "running_chunk",
            "task": "table_merge",
            "chunk_index": index,
            "chunk_size": chunk_size,
            "plan": {**plan, "table_merge": len(merge_inputs)},
        })
        _run_table_merge_chunk(raw_doc_dir, index, merge_input)
        _annotate_chunk_size(_chunk_path(raw_doc_dir, "table_merge", index), chunk_size)
        result = {
            "status": "partial",
            "completed_task": "table_merge",
            "completed_chunk_index": index,
            "chunk_size": chunk_size,
            "plan": {**plan, "table_merge": len(merge_inputs)},
        }
        _write_checkpoint(raw_doc_dir, result)
        return result

    _assemble_output(doc_blocks, raw_doc_dir, output_dir, doc_stem, input_label, large_block_linking)
    result = {
        "status": "completed",
        "output_json": str(output_dir / f"{doc_stem}.json"),
        "chunk_size": chunk_size,
        "plan": {**plan, "table_merge": len(merge_inputs)},
    }
    _write_checkpoint(raw_doc_dir, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run exactly one resumable MinerU-Popo chunk for Luceon.")
    parser.add_argument("--normalized-input", required=True)
    parser.add_argument("--pdf-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--raw-doc-dir", required=True)
    parser.add_argument("--doc-id", default="")
    default_chunk_size = int(os.environ.get(
        "POPO_FULL_BACKGROUND_CHUNK_SIZE",
        os.environ.get("POPO_MPS_CHUNK_SIZE", "10"),
    ))
    parser.add_argument("--chunk-size", type=int, default=default_chunk_size)
    return parser.parse_args()


def main() -> None:
    result = run_next_chunk(parse_args())
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
