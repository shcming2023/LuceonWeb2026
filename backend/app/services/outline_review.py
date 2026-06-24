import re
from typing import Any


TOC_WORDS = ("contents", "table of contents", "目录")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PAGE_COMMENT_RE = re.compile(r"<!--\s*page_(?:idx|index)\s*:\s*(\d+)\s*-->", re.IGNORECASE)
MAX_UNIT_TEXT_CHARS: int | None = None


def _text(value: Any) -> str:
    return str(value or "").strip()


def _first_page(location: Any) -> int | None:
    if isinstance(location, list):
        for item in location:
            page = _first_page(item)
            if page:
                return page
    if isinstance(location, dict):
        value = location.get("page") or location.get("page_number")
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def _is_toc_like(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in TOC_WORDS)


def _outline_item(title: str, page: int | None, level: int = 1, source: str = "") -> dict[str, Any]:
    return {
        "title": title,
        "page": page,
        "level": max(1, min(int(level or 1), 6)),
        "source": source,
    }


def _bounded_text(text: str, limit: int | None = MAX_UNIT_TEXT_CHARS) -> tuple[str, bool]:
    if not limit:
        return text, False
    if len(text) <= limit:
        return text, False
    return text[:limit].rstrip() + "\n\n[内容过长，已截断显示]", True


def _title_signature(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\u4e00-\u9fff]+", " ", title).strip()).lower()


def _path_signature(path: list[str]) -> str:
    return " / ".join(_title_signature(item) for item in path if _title_signature(item))


def _candidate_debug_row(candidate: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        return {}
    evidence = candidate.get("evidence") if isinstance(candidate.get("evidence"), dict) else {}
    block_ids = candidate.get("block_ids") if isinstance(candidate.get("block_ids"), list) else []
    return {
        "candidate_id": _text(candidate.get("candidate_id")),
        "title": _text(candidate.get("title_text") or candidate.get("title")),
        "candidate_type": _text(candidate.get("candidate_type")),
        "source": _text(candidate.get("source") or candidate.get("source_path")),
        "page": candidate.get("page"),
        "bbox": candidate.get("bbox"),
        "parent_hint": _text(candidate.get("parent_hint")),
        "level_hint": candidate.get("level_hint"),
        "confidence": candidate.get("confidence"),
        "needs_llm": bool(candidate.get("needs_llm")),
        "needs_visual": bool(candidate.get("needs_visual")),
        "block_ids": block_ids[:12],
        "evidence": {
            "anchor_title": evidence.get("anchor_title"),
            "anchor_method": evidence.get("anchor_method"),
            "kind": evidence.get("kind"),
            "depth": evidence.get("depth"),
            "popo_level": evidence.get("popo_level"),
        },
    }


def _page_from_comment(line: str) -> int | None:
    match = PAGE_COMMENT_RE.search(line)
    if not match:
        return None
    try:
        return int(match.group(1)) + 1
    except ValueError:
        return None


def _nearby_page(lines: list[str], index: int, current_page: int | None) -> int | None:
    if current_page:
        return current_page
    for line in lines[index + 1 : min(len(lines), index + 7)]:
        page = _page_from_comment(line)
        if page:
            return page
        if HEADING_RE.match(line):
            break
    return None


def _outline_entries_from_popo_outline(popo_outline: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(popo_outline, dict):
        return []
    rows = popo_outline.get("outline")
    if not isinstance(rows, list):
        return []
    items: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = _text(row.get("title") or row.get("anchor_title"))
        if not title:
            continue
        page = row.get("start_page")
        if not page:
            start_idx = row.get("start_page_idx")
            try:
                page = int(start_idx) + 1
            except (TypeError, ValueError):
                page = None
        try:
            page_int = int(page) if page else None
        except (TypeError, ValueError):
            page_int = None
        items.append(
            {
                "title": title,
                "page": page_int,
                "level": max(1, min(int(row.get("level") or 1), 6)),
                "source": str(row.get("source") or "popo_outline"),
                "kind": row.get("kind") or "",
                "printed_page": row.get("printed_page") or "",
            }
        )
    return items


def _outline_page_lookup(popo_outline: dict[str, Any] | None) -> dict[str, int]:
    lookup: dict[str, int] = {}
    for item in _outline_entries_from_popo_outline(popo_outline):
        page = item.get("page")
        if page and item.get("title"):
            lookup.setdefault(_title_signature(str(item["title"])), int(page))
    return lookup


def markdown_units(markdown: str, source: str, popo_outline: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    lines = markdown.splitlines()
    headings: list[dict[str, Any]] = []
    current_page: int | None = None
    page_lookup = _outline_page_lookup(popo_outline)

    for index, line in enumerate(lines):
        page = _page_from_comment(line)
        if page:
            current_page = page
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = match.group(2).strip().strip("#").strip()
        title = re.sub(r"\s+", " ", title)
        if not title:
            continue
        level = len(match.group(1))
        headings.append(
            {
                "line": index,
                "title": title,
                "level": level,
                "page": page_lookup.get(_title_signature(title)) or _nearby_page(lines, index, current_page),
            }
        )

    stack: list[tuple[int, str]] = []
    units: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        next_line = headings[index + 1]["line"] if index + 1 < len(headings) else len(lines)
        level = int(heading["level"])
        while stack and stack[-1][0] >= level:
            stack.pop()
        path = [item[1] for item in stack] + [str(heading["title"])]
        raw_text = "\n".join(lines[int(heading["line"]) : next_line]).strip()
        bounded, truncated = _bounded_text(raw_text)
        units.append(
            {
                "id": f"{source}-{index + 1}",
                "index": index + 1,
                "title": heading["title"],
                "level": level,
                "path": path,
                "path_label": " / ".join(path),
                "page": heading["page"],
                "page_start": heading["page"],
                "page_end": heading["page"],
                "text": bounded,
                "text_char_count": len(raw_text),
                "truncated": truncated,
                "source": source,
                "path_signature": _path_signature(path),
                "title_signature": _title_signature(str(heading["title"])),
            }
        )
        stack.append((level, str(heading["title"])))

    for index, unit in enumerate(units):
        page = unit.get("page_start")
        next_page = None
        for candidate in units[index + 1 :]:
            candidate_page = candidate.get("page_start")
            if candidate_page:
                next_page = candidate_page
                break
        if page and next_page and next_page > page:
            unit["page_end"] = next_page - 1
    return units


def _raw_text_rows_from_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for unit in units[:200]:
        rows.append(
            {
                "title": unit.get("title") or f"未命名单元 {len(rows) + 1}",
                "page": unit.get("page_start") or unit.get("page"),
                "level": unit.get("level") or 1,
                "text": str(unit.get("text") or "")[:2000],
            }
        )
    return rows


def _outline_from_units(units: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    return [
        _outline_item(
            str(unit.get("title") or ""),
            unit.get("page_start") or unit.get("page"),
            int(unit.get("level") or 1),
            source,
        )
        for unit in units
        if unit.get("title")
    ]


def _match_clean_units(raw_units: list[dict[str, Any]], clean_units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    by_path = {unit.get("path_signature"): unit for unit in clean_units if unit.get("path_signature")}
    by_title: dict[str, list[dict[str, Any]]] = {}
    for unit in clean_units:
        title_key = str(unit.get("title_signature") or "")
        if title_key:
            by_title.setdefault(title_key, []).append(unit)

    matched_clean_ids = set()
    directory_units = []
    for raw_unit in raw_units:
        clean_unit = by_path.get(raw_unit.get("path_signature"))
        if not clean_unit:
            candidates = by_title.get(str(raw_unit.get("title_signature") or ""), [])
            clean_unit = candidates[0] if len(candidates) == 1 else None
        if clean_unit:
            matched_clean_ids.add(clean_unit.get("id"))

        clean_text = str(clean_unit.get("text") or "") if clean_unit else ""
        directory_units.append(
            {
                "id": f"unit-{raw_unit.get('index')}",
                "index": raw_unit.get("index"),
                "title": raw_unit.get("title"),
                "level": raw_unit.get("level"),
                "path": raw_unit.get("path") or [],
                "path_label": raw_unit.get("path_label") or raw_unit.get("title") or "",
                "page": raw_unit.get("page_start") or raw_unit.get("page"),
                "page_start": raw_unit.get("page_start") or raw_unit.get("page"),
                "page_end": raw_unit.get("page_end") or raw_unit.get("page_start") or raw_unit.get("page"),
                "raw_text": raw_unit.get("text") or "",
                "clean_text": clean_text,
                "raw_char_count": raw_unit.get("text_char_count") or 0,
                "clean_char_count": clean_unit.get("text_char_count") if clean_unit else 0,
                "raw_truncated": bool(raw_unit.get("truncated")),
                "clean_truncated": bool(clean_unit.get("truncated")) if clean_unit else False,
                "clean_status": "matched" if clean_unit else ("pending" if not clean_units else "missing"),
                "heading_match": bool(clean_unit),
            }
        )

    extra_count = len([unit for unit in clean_units if unit.get("id") not in matched_clean_ids])
    return directory_units, extra_count


def pdf_outline_from_source_map(source_map: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in source_map.get("pages", []):
        page_number = page.get("page")
        for block in page.get("blocks", []):
            title = _text(block.get("text"))
            block_type = _text(block.get("type")).lower()
            if not title:
                continue
            if block_type == "index" or _is_toc_like(title):
                items.append(_outline_item(title, page_number, 1, block_type or "pdf"))

    if items:
        return items[:200]

    title_items = []
    for page in source_map.get("pages", []):
        page_number = page.get("page")
        for block in page.get("blocks", []):
            title = _text(block.get("text"))
            if _text(block.get("type")).lower() == "title" and len(title) >= 4:
                title_items.append(_outline_item(title, page_number, 1, "title"))
    return title_items[:200]


def _walk_tree(node: Any, items: list[dict[str, Any]], raw_text: list[dict[str, Any]], depth: int = 0) -> None:
    if not isinstance(node, dict):
        return

    title = _text(node.get("title"))
    content = _text(node.get("content"))
    node_type = _text(node.get("type"))
    level = int(node.get("level") or depth or 1)
    page = _first_page(node.get("location"))
    if title:
        items.append(_outline_item(title, page, level, node_type or "raw"))
    if title or content:
        raw_text.append(
            {
                "title": title or f"未命名单元 {len(raw_text) + 1}",
                "page": page,
                "level": max(1, min(level, 6)),
                "text": content[:2000],
            }
        )

    for child in node.get("children") or []:
        _walk_tree(child, items, raw_text, depth + 1)


def raw_outline_from_document_tree(document_tree: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    raw_text: list[dict[str, Any]] = []
    _walk_tree(document_tree, items, raw_text)
    return items[:500], raw_text[:200]


def build_outline_review(
    source_map: dict[str, Any],
    document_tree: dict[str, Any] | None,
    clean_document_tree: dict[str, Any] | None = None,
    raw_manifest: dict[str, Any] | None = None,
    raw_markdown: str | None = None,
    clean_manifest: dict[str, Any] | None = None,
    clean_markdown: str | None = None,
    popo_outline: dict[str, Any] | None = None,
    outline_candidates: list[dict[str, Any]] | None = None,
    outline_candidates_summary: dict[str, Any] | None = None,
    outline_decision: dict[str, Any] | None = None,
    visual_decisions: dict[str, Any] | None = None,
    chunk_boundary_report: dict[str, Any] | None = None,
    outline_apply_report: dict[str, Any] | None = None,
    image_closure_report: dict[str, Any] | None = None,
    stage_refs: dict[str, Any] | None = None,
    material: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pdf_outline = pdf_outline_from_source_map(source_map)
    raw_outline: list[dict[str, Any]] = []
    raw_text: list[dict[str, Any]] = []
    raw_units = markdown_units(raw_markdown or "", "raw", popo_outline) if raw_markdown else []
    if raw_units:
        raw_outline = _outline_from_units(raw_units, "raw_markdown")
        raw_text = _raw_text_rows_from_units(raw_units)
    elif document_tree:
        raw_outline, raw_text = raw_outline_from_document_tree(document_tree)
    elif popo_outline:
        raw_outline = _outline_entries_from_popo_outline(popo_outline)

    clean_outline: list[dict[str, Any]] = []
    clean_text: list[dict[str, Any]] = []
    clean_units = markdown_units(clean_markdown or "", "clean", popo_outline) if clean_markdown else []
    if clean_units:
        clean_outline = _outline_from_units(clean_units, "clean_markdown")
        clean_text = _raw_text_rows_from_units(clean_units)
    elif clean_document_tree:
        clean_outline, clean_text = raw_outline_from_document_tree(clean_document_tree)

    directory_units, extra_clean_count = _match_clean_units(raw_units, clean_units)

    findings = []
    if not pdf_outline:
        findings.append("未识别到 PDF 目录线索，需要人工核对原书目录页")
    if not raw_units and not raw_outline:
        findings.append("未识别到 Raw 目录/切分结果")
    if raw_manifest and not raw_markdown:
        findings.append("Raw manifest 已接入，但未找到 raw Markdown 主文件")
    if clean_manifest and not clean_markdown:
        findings.append("Clean manifest 已接入，但未找到 clean Markdown 主文件")
    if not clean_outline:
        findings.append("Clean 目录暂未接入或未产出")
    if clean_units and extra_clean_count:
        findings.append(f"Clean 中存在 {extra_clean_count} 个未匹配 Raw 目录的标题")

    selected_decisions = outline_decision.get("final_outline") if isinstance(outline_decision, dict) else []
    if not selected_decisions and isinstance(outline_decision, dict):
        selected_decisions = outline_decision.get("selected_outline")
    rejected_decisions = outline_decision.get("rejected_candidates") if isinstance(outline_decision, dict) else []
    visual_results = visual_decisions.get("results") if isinstance(visual_decisions, dict) else []
    debug_by_title: dict[str, Any] = {}
    candidate_by_id = {
        str(candidate.get("candidate_id")): candidate
        for candidate in (outline_candidates or [])
        if isinstance(candidate, dict) and candidate.get("candidate_id")
    }
    for item in selected_decisions or []:
        title = _text(item.get("title"))
        if not title:
            continue
        row = debug_by_title.setdefault(title.lower(), {"decisions": [], "visual": [], "candidates": [], "rejected": []})
        row["decisions"].append(item)
        for candidate_id in item.get("candidate_ids") or []:
            candidate = candidate_by_id.get(str(candidate_id))
            if candidate:
                row["candidates"].append(_candidate_debug_row(candidate))
    for item in rejected_decisions or []:
        candidate_id = str(item.get("candidate_id") or "")
        candidate = candidate_by_id.get(candidate_id)
        title = _text(item.get("title") or (candidate or {}).get("title_text"))
        if not title:
            continue
        row = debug_by_title.setdefault(title.lower(), {"decisions": [], "visual": [], "candidates": [], "rejected": []})
        row["rejected"].append(
            {
                "candidate_id": candidate_id,
                "title": title,
                "reason": item.get("reason") or item.get("llm_reason") or item.get("decision_reason") or "",
                "decision": item.get("decision") or item.get("llm_decision") or "rejected",
                "candidate": _candidate_debug_row(candidate) if candidate else {},
            }
        )
    for item in visual_results or []:
        title = _text(item.get("title"))
        if not title:
            continue
        debug_by_title.setdefault(title.lower(), {"decisions": [], "visual": [], "candidates": [], "rejected": []})["visual"].append(item)

    candidate_preview = [_candidate_debug_row(candidate) for candidate in (outline_candidates or [])[:120] if isinstance(candidate, dict)]

    return {
        "summary": {
            "pdf_outline_count": len(pdf_outline),
            "raw_outline_count": len(raw_outline),
            "raw_text_count": len(raw_text),
            "clean_outline_count": len(clean_outline),
            "directory_unit_count": len(directory_units),
            "raw_markdown_available": bool(raw_markdown),
            "clean_markdown_available": bool(clean_markdown),
            "clean_extra_heading_count": extra_clean_count,
            "outline_candidate_count": (outline_candidates_summary or {}).get("candidate_count") if outline_candidates_summary else len(outline_candidates or []),
            "outline_decision_method": (outline_decision or {}).get("decision_method") if outline_decision else "",
            "outline_llm": (outline_decision or {}).get("llm") if outline_decision else {},
            "visual_candidate_count": (visual_decisions or {}).get("candidate_count") if visual_decisions else 0,
            "visual_enabled": (visual_decisions or {}).get("enabled") if visual_decisions else False,
            "assigned_block_count": (outline_apply_report or {}).get("assigned_block_count") if outline_apply_report else 0,
            "unassigned_block_count": (outline_apply_report or chunk_boundary_report or {}).get("unassigned_block_count") if (outline_apply_report or chunk_boundary_report) else 0,
            "missing_image_count": (image_closure_report or chunk_boundary_report or {}).get("missing_image_count") if (image_closure_report or chunk_boundary_report) else 0,
            "findings": findings,
        },
        "material": material or {},
        "stage_refs": stage_refs or {},
        "pdf_outline": pdf_outline,
        "raw_outline": raw_outline,
        "raw_text": raw_text,
        "clean_outline": clean_outline,
        "clean_text": clean_text,
        "directory_units": directory_units,
        "debug_artifacts": {
            "outline_candidates_summary": outline_candidates_summary or {},
            "outline_candidates_preview": candidate_preview,
            "outline_decision_summary": {
                "decision_method": (outline_decision or {}).get("decision_method"),
                "selected_count": (outline_decision or {}).get("selected_count"),
                "final_outline_count": (outline_decision or {}).get("final_outline_count"),
                "final_outline_source": (outline_decision or {}).get("final_outline_source"),
                "rejected_count": (outline_decision or {}).get("rejected_count"),
                "needs_llm_count": (outline_decision or {}).get("needs_llm_count"),
                "needs_visual_count": (outline_decision or {}).get("needs_visual_count"),
                "llm": (outline_decision or {}).get("llm"),
                "visual_application": (outline_decision or {}).get("visual_application"),
            },
            "visual_decisions_summary": {
                "enabled": (visual_decisions or {}).get("enabled"),
                "provider": (visual_decisions or {}).get("provider"),
                "model": (visual_decisions or {}).get("model"),
                "candidate_count": (visual_decisions or {}).get("candidate_count"),
                "validated_count": (visual_decisions or {}).get("validated_count"),
                "truncated": (visual_decisions or {}).get("truncated"),
                "usage": (visual_decisions or {}).get("usage"),
                "error_count": len((visual_decisions or {}).get("errors") or []),
            },
            "chunk_boundary_report": chunk_boundary_report or {},
            "outline_apply_report": outline_apply_report or {},
            "image_closure_report": image_closure_report or {},
            "by_title": debug_by_title,
        },
    }
