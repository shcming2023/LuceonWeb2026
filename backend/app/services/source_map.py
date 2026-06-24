import re
from typing import Any


def _coerce_number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return None
        if number.is_integer():
            return int(number)
        return number
    return None


def _flatten_numbers(value: Any) -> list[int | float]:
    if isinstance(value, list | tuple):
        numbers: list[int | float] = []
        for item in value:
            numbers.extend(_flatten_numbers(item))
        return numbers
    number = _coerce_number(value)
    return [number] if number is not None else []


def _normalize_bbox(value: Any) -> list[int | float] | None:
    numbers = _flatten_numbers(value)
    if len(numbers) == 4:
        return numbers
    if len(numbers) >= 8 and len(numbers) % 2 == 0:
        xs = numbers[0::2]
        ys = numbers[1::2]
        return [min(xs), min(ys), max(xs), max(ys)]
    return None


def _extract_bbox(item: dict[str, Any]) -> list[int | float] | None:
    for key in ("bbox", "layout_bbox", "line_bbox", "span_bbox", "poly"):
        bbox = _normalize_bbox(item.get(key))
        if bbox:
            return bbox
    return None


def _clean_source_text(value: Any) -> str:
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _join_source_text(parts: list[str]) -> str:
    seen = set()
    unique_parts = []
    for part in parts:
        if part and part not in seen:
            seen.add(part)
            unique_parts.append(part)
    return " ".join(unique_parts).strip()


def _source_text_signature(text: str) -> str:
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE).lower()


def _merge_duplicate_source_block(
    blocks: list[dict[str, Any]],
    bbox: list[int | float],
    block_type: str,
    text: str,
) -> bool:
    text_signature = _source_text_signature(text)
    if not text_signature:
        return False

    for block in blocks:
        if block.get("type") != block_type or block.get("bbox") != bbox:
            continue

        existing_text = str(block.get("text") or "")
        existing_signature = _source_text_signature(existing_text)
        if not existing_signature:
            continue
        if text_signature not in existing_signature and existing_signature not in text_signature:
            continue

        if len(text_signature) > len(existing_signature):
            block["text"] = text
        return True
    return False


def _extract_text(value: Any) -> str:
    if isinstance(value, str):
        return _clean_source_text(value)
    if isinstance(value, list):
        return _join_source_text([_extract_text(item) for item in value])
    if not isinstance(value, dict):
        return ""

    parts = []
    for key in ("text", "content"):
        item = value.get(key)
        if isinstance(item, str):
            parts.append(_clean_source_text(item))
        elif isinstance(item, dict | list):
            parts.append(_extract_text(item))
    if parts:
        return _join_source_text(parts)

    for key in ("spans", "lines", "blocks"):
        item = value.get(key)
        if isinstance(item, dict | list):
            parts.append(_extract_text(item))
    return _join_source_text(parts)


def _extract_block_type(item: dict[str, Any]) -> str:
    for key in ("type", "block_type", "category_type", "sub_type"):
        value = item.get(key)
        if value:
            return str(value)
    return "block"


def _page_index(page_info: dict[str, Any], fallback_index: int) -> int:
    page_idx = _coerce_number(page_info.get("page_idx"))
    return int(page_idx) if page_idx is not None else fallback_index


def _page_dimensions(page_info: dict[str, Any]) -> tuple[int | float | None, int | float | None]:
    size = page_info.get("page_size") or page_info.get("size")
    if isinstance(size, dict):
        return _coerce_number(size.get("width")), _coerce_number(size.get("height"))
    numbers = _flatten_numbers(size)
    if len(numbers) >= 2:
        return numbers[0], numbers[1]

    width = (
        _coerce_number(page_info.get("width"))
        or _coerce_number(page_info.get("page_width"))
        or _coerce_number(page_info.get("w"))
    )
    height = (
        _coerce_number(page_info.get("height"))
        or _coerce_number(page_info.get("page_height"))
        or _coerce_number(page_info.get("h"))
    )
    return width, height


def _collect_source_blocks(value: Any, page_number: int, blocks: list[dict[str, Any]], seen: set[tuple]) -> None:
    if isinstance(value, list):
        for item in value:
            _collect_source_blocks(item, page_number, blocks, seen)
        return
    if not isinstance(value, dict):
        return

    bbox = _extract_bbox(value)
    text = _extract_text(value)
    block_type = _extract_block_type(value)
    if bbox and text:
        bounded_text = text[:1200]
        if _merge_duplicate_source_block(blocks, bbox, block_type, bounded_text):
            return
        key = (tuple(bbox), bounded_text, block_type)
        if key not in seen:
            seen.add(key)
            blocks.append(
                {
                    "id": f"p{page_number}-b{len(blocks) + 1}",
                    "type": block_type,
                    "text": bounded_text,
                    "bbox": bbox,
                }
            )
        return

    for item in value.values():
        if isinstance(item, dict | list):
            _collect_source_blocks(item, page_number, blocks, seen)


def normalize_source_map(middle_json: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    pdf_info = middle_json.get("pdf_info")
    if not isinstance(pdf_info, list):
        return {"pages": []}

    pages = []
    for index, page_info in enumerate(pdf_info):
        if not isinstance(page_info, dict):
            continue
        page_idx = _page_index(page_info, index)
        page_number = page_idx + 1
        width, height = _page_dimensions(page_info)
        blocks: list[dict[str, Any]] = []
        _collect_source_blocks(page_info, page_number, blocks, set())
        pages.append(
            {
                "page": page_number,
                "page_idx": page_idx,
                "width": width,
                "height": height,
                "blocks": blocks,
            }
        )
    return {"pages": pages}


def synthesize_page_markdown(source_map: dict[str, Any]) -> str:
    sections = []
    for page in source_map.get("pages", []):
        page_number = page.get("page")
        if not page_number:
            continue
        lines = [f"# Page {page_number}"]
        for block in page.get("blocks", []):
            text = str(block.get("text") or "").strip()
            if text:
                lines.append(text)
        sections.append("\n\n".join(lines))
    return "\n\n".join(sections)


def _content_list_text(item: dict[str, Any]) -> str:
    for key in ("text", "content", "latex", "html"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _markdown_image_alt(item: dict[str, Any]) -> str:
    captions = item.get("image_caption")
    if isinstance(captions, list):
        caption_text = " ".join(str(caption).strip() for caption in captions if str(caption).strip())
        if caption_text:
            return re.sub(r"\s+", " ", caption_text)[:120]
    text = _content_list_text(item)
    return re.sub(r"\s+", " ", text)[:120]


def _content_list_image_notes(item: dict[str, Any], alt: str) -> list[str]:
    notes: list[str] = []
    seen: set[str] = set()

    def append_note(value: Any) -> None:
        if isinstance(value, list):
            for part in value:
                append_note(part)
            return
        if not isinstance(value, str):
            return
        text = value.strip()
        if not text:
            return
        signature = re.sub(r"\s+", " ", text)
        if signature in seen:
            return
        seen.add(signature)
        notes.append(text)

    append_note(item.get("image_caption"))
    append_note(_content_list_text(item))
    append_note(item.get("image_footnote"))
    if not notes and alt:
        notes.append(alt)
    return notes


def _content_list_item_markdown(item: dict[str, Any]) -> str:
    item_type = str(item.get("type") or "").lower()
    image_path = item.get("img_path") or item.get("image_path")
    if isinstance(image_path, str) and image_path.strip():
        alt = _markdown_image_alt(item)
        lines = [f"![{alt}]({image_path.strip()})"]
        lines.extend(_content_list_image_notes(item, alt))
        return "\n\n".join(lines)

    text = _content_list_text(item)
    if not text:
        return ""
    if item_type in {"interline_equation", "equation"} and not text.lstrip().startswith("$"):
        return f"$$\n{text}\n$$"
    return text


def synthesize_page_markdown_from_content_list(content_list: Any) -> str:
    if isinstance(content_list, dict):
        for key in ("content_list", "items", "blocks"):
            value = content_list.get(key)
            if isinstance(value, list):
                content_list = value
                break
    if not isinstance(content_list, list):
        return ""

    by_page: dict[int, list[str]] = {}
    for item in content_list:
        if not isinstance(item, dict):
            continue
        page_idx = _coerce_number(item.get("page_idx"))
        if page_idx is None:
            page_idx = _coerce_number(item.get("page"))
            page_number = int(page_idx) if page_idx is not None else None
        else:
            page_number = int(page_idx) + 1
        if not page_number:
            continue
        markdown = _content_list_item_markdown(item)
        if markdown:
            by_page.setdefault(page_number, []).append(markdown)

    sections = []
    for page_number in sorted(by_page):
        sections.append("\n\n".join([f"# Page {page_number}", *by_page[page_number]]))
    return "\n\n".join(sections)
