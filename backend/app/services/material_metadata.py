import json
import re
import time
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.material_metadata import MaterialMetadata
from app.services.luceon_review import ObjectRef, read_object, resolve_manifest
from app.services.runtime_settings import _chat_completions_url, load_runtime_config


METADATA_FIELDS = [
    "original_title",
    "publication_date",
    "publication_year",
    "edition",
    "subject",
    "publication_country",
    "series_name",
    "publisher",
    "isbn",
    "language",
    "grade_level",
]
SAMPLE_TARGET_CHARS = 9000
FRONT_SAMPLE_CHARS = 4200
KEYWORD_WINDOW_CHARS = 900
CATALOG_CONTEXT_MAX_CHARS = 5000
CATALOG_CONTEXT_MAX_EXAMPLES = 14
CATALOG_CONTEXT_MAX_VALUES = 24
CATALOG_CONTEXT_MAX_TITLE_PATTERNS = 10
MANUAL_CONTEXT_MIN_SIMILARITY = 0.25
MANUAL_CONTEXT_STABLE_FIELDS = [
    "subject",
    "series_name",
    "language",
    "publication_country",
    "publisher",
    "edition",
]
TITLE_ROLE_TERMS = {
    "student",
    "students",
    "learner",
    "learners",
    "workbook",
    "coursebook",
    "practice",
    "teacher",
    "teachers",
    "resource",
    "book",
}
KEYWORDS = [
    "isbn",
    "copyright",
    "©",
    "published",
    "publisher",
    "edition",
    "first published",
    "second edition",
    "third edition",
    "cambridge",
    "pearson",
    "oxford",
    "hodder",
    "出版",
    "出版社",
    "版",
    "版权",
    "书号",
    "教材",
]


class MetadataExtractionError(RuntimeError):
    pass


def metadata_for_materials(db: Session, user_id: str, material_ids: list[int]) -> dict[int, MaterialMetadata]:
    if not material_ids:
        return {}
    rows = (
        db.query(MaterialMetadata)
        .filter(MaterialMetadata.user_id == user_id, MaterialMetadata.material_pk.in_(material_ids))
        .all()
    )
    return {row.material_pk: row for row in rows}


def metadata_options(db: Session, user_id: str) -> dict[str, list[str]]:
    return {
        "subjects": _distinct_values(db, user_id, MaterialMetadata.subject),
        "countries": _distinct_values(db, user_id, MaterialMetadata.publication_country),
        "series": _distinct_values(db, user_id, MaterialMetadata.series_name),
        "publishers": _distinct_values(db, user_id, MaterialMetadata.publisher),
        "languages": _distinct_values(db, user_id, MaterialMetadata.language),
        "editions": _distinct_values(db, user_id, MaterialMetadata.edition),
    }


def upsert_manual_metadata(db: Session, user_id: str, material: Material, payload: dict[str, Any]) -> MaterialMetadata:
    metadata = get_or_create_metadata(db, user_id, material)
    for field in METADATA_FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if field == "publication_year":
            metadata.publication_year = normalize_year(value)
        else:
            setattr(metadata, field, normalize_text(value))
    evidence = payload.get("evidence")
    if isinstance(evidence, list):
        metadata.update_evidence([item for item in evidence if isinstance(item, dict)])
    metadata.status = "manual"
    metadata.source = "mixed" if metadata.source == "ai" else "manual"
    metadata.manual_override = True
    metadata.confidence = payload.get("confidence") if isinstance(payload.get("confidence"), (int, float)) else metadata.confidence
    metadata.extraction_error = None
    return metadata


def extract_metadata_with_ai(
    db: Session,
    user_id: str,
    material: Material,
    *,
    force: bool = False,
) -> MaterialMetadata:
    metadata = get_or_create_metadata(db, user_id, material)
    if metadata.manual_override and not force:
        raise MetadataExtractionError("manual_override")
    sample = build_metadata_sample(material)
    catalog_context = build_catalog_context(db, user_id, material)
    sample["catalog_context"] = catalog_context.get("summary", {})
    result = call_metadata_model(material, sample, catalog_context)
    apply_ai_result(metadata, result, sample, catalog_context, material)
    return metadata


def build_catalog_context(db: Session, user_id: str, material: Material) -> dict[str, Any]:
    rows = (
        db.query(Material, MaterialMetadata)
        .join(MaterialMetadata, MaterialMetadata.material_pk == Material.id)
        .filter(
            Material.user_id == user_id,
            MaterialMetadata.user_id == user_id,
            Material.ignored.is_(False),
            MaterialMetadata.material_pk != material.id,
            MaterialMetadata.status.in_(["manual", "ai_extracted"]),
        )
        .all()
    )
    manual_examples: list[tuple[float, dict[str, Any]]] = []
    ai_examples: list[tuple[float, dict[str, Any]]] = []
    values: dict[str, dict[str, dict[str, Any]]] = {
        "subject": {},
        "series_name": {},
        "grade_level": {},
        "edition": {},
        "language": {},
    }
    target_tokens = catalog_tokens(material.title or material.filename or "")
    for row_material, metadata in rows:
        score = catalog_similarity(target_tokens, catalog_tokens(catalog_source_text(row_material, metadata)))
        example = catalog_example(row_material, metadata, score)
        if metadata.manual_override:
            manual_examples.append((score, example))
        else:
            if score > 0:
                ai_examples.append((score, example))
        for field in values:
            value = normalize_text(getattr(metadata, field, ""))
            if not value:
                continue
            bucket = values[field].setdefault(
                value,
                {
                    "value": value,
                    "count": 0,
                    "manual_count": 0,
                    "avg_confidence": 0.0,
                    "authority": "ai_observed",
                },
            )
            bucket["count"] += 1
            bucket["avg_confidence"] += float(metadata.confidence or 0)
            if metadata.manual_override:
                bucket["manual_count"] += 1
                bucket["authority"] = "manual_confirmed"
    manual_examples.sort(key=lambda item: (item[0], float(item[1].get("confidence") or 0)), reverse=True)
    ai_examples.sort(key=lambda item: (item[0], float(item[1].get("confidence") or 0)), reverse=True)
    for field, field_values in values.items():
        for item in field_values.values():
            count = item["count"] or 1
            item["avg_confidence"] = round(float(item["avg_confidence"]) / count, 3)
        values[field] = dict(
            sorted(
                field_values.items(),
                key=lambda item: (item[1]["manual_count"], item[1]["count"], item[1]["avg_confidence"]),
                reverse=True,
            )[:CATALOG_CONTEXT_MAX_VALUES]
        )
    context = {
        "version": "catalog_context_v1",
        "authority_order": [
            "manual_confirmed metadata for similar materials",
            "current document filename and sampled text evidence",
            "similar AI-extracted catalog examples",
            "catalog vocabulary counts",
        ],
        "schema": metadata_output_schema(),
        "manual_confirmed_examples": [example for _, example in manual_examples[:CATALOG_CONTEXT_MAX_EXAMPLES]],
        "similar_ai_examples": [example for _, example in ai_examples[:CATALOG_CONTEXT_MAX_EXAMPLES]],
        "catalog_values": {field: list(field_values.values()) for field, field_values in values.items()},
    }
    context["similar_title_patterns"] = build_title_patterns(
        context["manual_confirmed_examples"] + context["similar_ai_examples"]
    )
    context["summary"] = {
        "version": context["version"],
        "manual_examples": len(context["manual_confirmed_examples"]),
        "similar_examples": len(context["similar_ai_examples"]),
        "similar_title_patterns": len(context["similar_title_patterns"]),
        "catalog_value_counts": {field: len(items) for field, items in context["catalog_values"].items()},
    }
    return trim_catalog_context(context)


def metadata_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "original_title",
            "publication_date",
            "publication_year",
            "edition",
            "subject",
            "publication_country",
            "series_name",
            "publisher",
            "isbn",
            "language",
            "grade_level",
            "confidence",
            "evidence",
        ],
        "properties": {
            "original_title": "string; formal title without file extension or source noise",
            "publication_date": "string; source wording or empty string",
            "publication_year": "integer year or null",
            "edition": "string; edition only, not series/title",
            "subject": "string; coarse stable subject label",
            "publication_country": "string; country/region or empty string",
            "series_name": "string; stable reusable series/family name or empty string",
            "publisher": "string; publisher or empty string",
            "isbn": "string; ISBN or empty string",
            "language": "string; primary language or empty string",
            "grade_level": "string; grade/stage/exam-system/course-code or empty string",
            "confidence": "number between 0 and 1",
            "evidence": "array of {field, quote, source}; each quote <= 80 chars",
        },
    }


def catalog_source_text(material: Material, metadata: MaterialMetadata) -> str:
    return " ".join(
        [
            material.filename or "",
            material.title or "",
            metadata.original_title or "",
            metadata.series_name or "",
            metadata.grade_level or "",
        ]
    )


def catalog_example(material: Material, metadata: MaterialMetadata, similarity: float = 0) -> dict[str, Any]:
    return {
        "filename": material.filename or material.title or "",
        "original_title": metadata.original_title or "",
        "publication_date": metadata.publication_date or "",
        "publication_year": metadata.publication_year,
        "subject": metadata.subject or "",
        "publication_country": metadata.publication_country or "",
        "series_name": metadata.series_name or "",
        "publisher": metadata.publisher or "",
        "isbn": metadata.isbn or "",
        "grade_level": metadata.grade_level or "",
        "edition": metadata.edition or "",
        "language": metadata.language or "",
        "confidence": metadata.confidence,
        "similarity": round(similarity, 3),
        "authority": "manual_confirmed" if metadata.manual_override else "ai_observed",
    }


def catalog_tokens(text: str) -> set[str]:
    lowered = re.sub(r"\.pdf$", "", normalize_space(text).lower())
    raw_tokens = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", lowered)
    ignored = {
        "pdf",
        "student",
        "students",
        "book",
        "workbook",
        "coursebook",
        "practice",
        "teacher",
        "teachers",
        "resource",
        "edition",
        "z",
        "library",
    }
    tokens = set()
    for token in raw_tokens:
        if len(token) <= 1 or token in ignored:
            continue
        if re.fullmatch(r"(?:19|20|21)\d{2}", token):
            continue
        tokens.add(token)
    return tokens


def catalog_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    if not intersection:
        return 0.0
    return intersection / max(len(left), len(right))


def trim_catalog_context(context: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(context, ensure_ascii=False)
    if len(text) <= CATALOG_CONTEXT_MAX_CHARS:
        return context
    trimmed = dict(context)
    trimmed["similar_ai_examples"] = trimmed.get("similar_ai_examples", [])[:6]
    trimmed["manual_confirmed_examples"] = trimmed.get("manual_confirmed_examples", [])[:10]
    trimmed["catalog_values"] = {
        field: items[:12] for field, items in dict(trimmed.get("catalog_values") or {}).items()
    }
    trimmed["similar_title_patterns"] = trimmed.get("similar_title_patterns", [])[:6]
    trimmed["summary"] = {
        **dict(trimmed.get("summary") or {}),
        "trimmed": True,
    }
    return trimmed


def build_title_patterns(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for example in examples:
        series_name = normalize_text(example.get("series_name"))
        original_title = normalize_text(example.get("original_title"))
        if not series_name or not original_title:
            continue
        candidate = title_pattern_candidate(original_title, series_name)
        if not candidate:
            continue
        key = (series_name.lower(), candidate["role_suffix_key"])
        bucket = buckets.setdefault(
            key,
            {
                "series_name": series_name,
                "pattern": f"{series_name} {{level}} {candidate['role_suffix']}",
                "role_suffix": candidate["role_suffix"],
                "role_terms": sorted(candidate["role_terms"]),
                "count": 0,
                "manual_count": 0,
                "examples": [],
                "authority": "ai_observed",
            },
        )
        bucket["count"] += 1
        if example.get("authority") == "manual_confirmed":
            bucket["manual_count"] += 1
            bucket["authority"] = "manual_confirmed"
        if len(bucket["examples"]) < 3:
            bucket["examples"].append(original_title)
    patterns = sorted(
        buckets.values(),
        key=lambda item: (item["manual_count"], item["count"], len(item["examples"])),
        reverse=True,
    )
    return patterns[:CATALOG_CONTEXT_MAX_TITLE_PATTERNS]


def title_pattern_candidate(original_title: str, series_name: str) -> dict[str, Any] | None:
    title = normalize_space(original_title)
    series = normalize_space(series_name)
    if not title.lower().startswith(series.lower()):
        return None
    remainder = title[len(series):].strip()
    match = re.match(r"^(?P<level>[A-Za-z]?\d+[A-Za-z]?)(?P<suffix>.*)$", remainder)
    if not match:
        return None
    suffix = normalize_space(match.group("suffix") or "")
    if not suffix:
        return None
    role_terms = title_role_terms(suffix)
    if not role_terms:
        return None
    role_suffix = canonical_title_suffix(suffix)
    return {
        "level": match.group("level"),
        "role_suffix": role_suffix,
        "role_suffix_key": re.sub(r"\s+", " ", role_suffix.lower()),
        "role_terms": role_terms,
    }


def title_role_terms(text: str) -> set[str]:
    tokens = re.findall(r"[a-z]+", normalize_space(text).lower())
    return {token for token in tokens if token in TITLE_ROLE_TERMS}


def canonical_title_suffix(suffix: str) -> str:
    words = re.sub(r"\s+", " ", suffix.strip())
    if words.startswith("(") and words.endswith(")"):
        inner = words[1:-1].strip()
        return f"({canonical_title_words(inner)})"
    return canonical_title_words(words)


def canonical_title_words(text: str) -> str:
    normalized_words = []
    for word in re.split(r"(\s+)", text):
        if not word.strip():
            normalized_words.append(word)
            continue
        lowered = word.lower()
        if lowered in TITLE_ROLE_TERMS:
            normalized_words.append(lowered[:1].upper() + lowered[1:])
        else:
            normalized_words.append(word)
    return "".join(normalized_words)


def apply_context_title_patterns(result: dict[str, Any], catalog_context: dict[str, Any], material: Material) -> None:
    original_title = normalize_text(result.get("original_title"))
    series_name = normalize_text(result.get("series_name"))
    if not original_title or not series_name:
        return
    source_text = " ".join([material.filename or "", material.title or "", original_title]).lower()
    current_terms = title_role_terms(original_title)
    for pattern in catalog_context.get("similar_title_patterns") or []:
        if normalize_text(pattern.get("series_name")).lower() != series_name.lower():
            continue
        if int(pattern.get("count") or 0) < 2 and int(pattern.get("manual_count") or 0) < 1:
            continue
        pattern_terms = set(pattern.get("role_terms") or [])
        if not pattern_terms:
            continue
        source_terms = title_role_terms(source_text)
        conflicting_terms = source_terms - pattern_terms - {"book"}
        if conflicting_terms:
            continue
        level = title_level_for_series(original_title, series_name) or title_level_for_series(material.filename or "", series_name)
        if not level:
            continue
        candidate = normalize_space(f"{series_name} {level} {normalize_text(pattern.get('role_suffix'))}")
        if not current_terms or current_terms <= pattern_terms:
            result["original_title"] = candidate
            raw_source = f"{material.filename or ''} {material.title or ''}".lower()
            if candidate != original_title or candidate.lower() not in raw_source:
                append_title_pattern_evidence(result, pattern)
            return


def title_level_for_series(title: str, series_name: str) -> str:
    clean_title = re.sub(r"\.pdf$", "", normalize_space(title), flags=re.IGNORECASE)
    series = normalize_space(series_name)
    if not clean_title.lower().startswith(series.lower()):
        return ""
    remainder = clean_title[len(series):].strip()
    match = re.match(r"^([A-Za-z]?\d+[A-Za-z]?)\b", remainder)
    return match.group(1) if match else ""


def append_title_pattern_evidence(result: dict[str, Any], pattern: dict[str, Any]) -> None:
    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        evidence = []
    quote = f"同系列标题模板: {normalize_text(pattern.get('pattern'))}"[:80]
    if not any(item.get("source") == "catalog_context" and item.get("quote") == quote for item in evidence if isinstance(item, dict)):
        evidence.append({"field": "original_title", "quote": quote, "source": "catalog_context"})
    result["evidence"] = evidence


def apply_manual_confirmed_context(result: dict[str, Any], catalog_context: dict[str, Any], material: Material) -> None:
    example = best_manual_context_example(result, catalog_context, material)
    if not example:
        return
    same_series = same_catalog_value(result.get("series_name"), example.get("series_name"))
    for field in MANUAL_CONTEXT_STABLE_FIELDS:
        example_value = normalize_text(example.get(field))
        if not example_value:
            continue
        current_value = normalize_text(result.get(field))
        if not current_value or same_series:
            if current_value != example_value:
                result[field] = example_value
                append_manual_context_evidence(result, field, example)
    example_year = normalize_year(example.get("publication_year"))
    current_year = normalize_year(result.get("publication_year"))
    if example_year and (not current_year or same_series):
        if current_year != example_year:
            result["publication_year"] = example_year
            append_manual_context_evidence(result, "publication_year", example)
    example_date = normalize_text(example.get("publication_date"))
    if example_date and (not normalize_text(result.get("publication_date")) or same_series):
        if normalize_text(result.get("publication_date")) != example_date:
            result["publication_date"] = example_date
            append_manual_context_evidence(result, "publication_date", example)
    grade_hint = chinese_grade_hint(" ".join([material.filename or "", material.title or "", normalize_text(result.get("grade_level"))]))
    if grade_hint and (not normalize_text(result.get("grade_level")) or same_series):
        if normalize_text(result.get("grade_level")) != grade_hint["grade_level"]:
            result["grade_level"] = grade_hint["grade_level"]
            append_manual_context_evidence(result, "grade_level", example)
    candidate_title = manual_context_title_candidate(example, material, result)
    if candidate_title and normalize_text(result.get("original_title")) != candidate_title:
        result["original_title"] = candidate_title
        append_manual_context_evidence(result, "original_title", example)


def best_manual_context_example(result: dict[str, Any], catalog_context: dict[str, Any], material: Material) -> dict[str, Any] | None:
    result_series = normalize_text(result.get("series_name"))
    target_tokens = catalog_tokens(" ".join([material.filename or "", material.title or "", normalize_text(result.get("original_title"))]))
    candidates: list[tuple[float, dict[str, Any]]] = []
    for example in catalog_context.get("manual_confirmed_examples") or []:
        if not isinstance(example, dict):
            continue
        same_series = same_catalog_value(result_series, example.get("series_name"))
        similarity = float(example.get("similarity") or 0)
        if not similarity:
            similarity = catalog_similarity(target_tokens, catalog_tokens(" ".join([
                normalize_text(example.get("filename")),
                normalize_text(example.get("original_title")),
                normalize_text(example.get("series_name")),
                normalize_text(example.get("grade_level")),
            ])))
        if same_series or similarity >= MANUAL_CONTEXT_MIN_SIMILARITY:
            candidates.append((similarity + (1 if same_series else 0), example))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def same_catalog_value(left: Any, right: Any) -> bool:
    return bool(normalize_text(left) and normalize_text(left).lower() == normalize_text(right).lower())


def manual_context_title_candidate(example: dict[str, Any], material: Material, result: dict[str, Any]) -> str:
    example_title = normalize_text(example.get("original_title"))
    if not example_title:
        return ""
    hint = chinese_grade_hint(
        " ".join(
            [
                material.filename or "",
                material.title or "",
                normalize_text(result.get("original_title")),
                normalize_text(result.get("grade_level")),
            ]
        )
    )
    if not hint:
        return ""
    candidate = replace_chinese_grade_title(example_title, hint)
    return candidate if candidate != example_title else ""


def chinese_grade_hint(text: str) -> dict[str, str] | None:
    normalized = normalize_space(text)
    shorthand = re.search(r"([一二三四五六七八九十]|\d{1,2})([上下])", normalized)
    if shorthand:
        grade = chinese_grade_text(shorthand.group(1))
        term = shorthand.group(2)
        return {"grade": grade, "term": term, "grade_level": f"{grade}年级{term}册"}
    grade_match = re.search(r"([一二三四五六七八九十]|\d{1,2})年级", normalized)
    term_match = re.search(r"[（(]([上下])[）)]", normalized)
    if grade_match and term_match:
        grade = chinese_grade_text(grade_match.group(1))
        term = term_match.group(1)
        return {"grade": grade, "term": term, "grade_level": f"{grade}年级{term}册"}
    return None


def chinese_grade_text(value: str) -> str:
    digits = {
        "1": "一",
        "2": "二",
        "3": "三",
        "4": "四",
        "5": "五",
        "6": "六",
        "7": "七",
        "8": "八",
        "9": "九",
        "10": "十",
        "11": "十一",
        "12": "十二",
    }
    return digits.get(value, value)


def replace_chinese_grade_title(title: str, hint: dict[str, str]) -> str:
    candidate = re.sub(r"([一二三四五六七八九十]|\d{1,2})年级", f"{hint['grade']}年级", title, count=1)
    candidate = re.sub(r"[（(][上下][）)]", f"（{hint['term']}）", candidate, count=1)
    return normalize_space(candidate)


def append_manual_context_evidence(result: dict[str, Any], field: str, example: dict[str, Any]) -> None:
    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        evidence = []
    example_title = normalize_text(example.get("original_title")) or normalize_text(example.get("filename"))
    quote = f"人工确认同系列: {example_title}"[:80]
    exists = any(
        item.get("field") == field and item.get("source") == "catalog_context manual" and item.get("quote") == quote
        for item in evidence
        if isinstance(item, dict)
    )
    if not exists:
        evidence.append({"field": field, "quote": quote, "source": "catalog_context manual"})
    result["evidence"] = evidence


def build_metadata_sample(material: Material) -> dict[str, Any]:
    text_sources = collect_text_sources(material)
    chunks = [
        f"文件名: {material.filename or ''}",
        f"现有标题: {material.title or ''}",
        f"material_id: {material.material_id or ''}",
    ]
    evidence_sources: list[dict[str, Any]] = []
    for source in text_sources:
        text = normalize_space(source["text"])
        if not text:
            continue
        front = text[:FRONT_SAMPLE_CHARS]
        if front:
            chunks.append(f"\n--- {source['label']} 前部样本 ---\n{front}")
            evidence_sources.append({"label": source["label"], "kind": "front", "chars": len(front)})
        for index, window in enumerate(keyword_windows(text), start=1):
            chunks.append(f"\n--- {source['label']} 关键词窗口 {index} ---\n{window}")
            evidence_sources.append({"label": source["label"], "kind": "keyword", "chars": len(window)})
        if sum(len(item) for item in chunks) >= SAMPLE_TARGET_CHARS:
            break
    sample_text = "\n".join(chunks)
    if len(sample_text) > SAMPLE_TARGET_CHARS:
        sample_text = sample_text[:SAMPLE_TARGET_CHARS]
    return {
        "text": sample_text,
        "sampled_chars": len(sample_text),
        "sources": evidence_sources[:12],
        "strategy": "filename + front matter sample + keyword windows; no full-document LLM input",
    }


def collect_text_sources(material: Material) -> list[dict[str, str]]:
    refs = metadata_text_refs(material)
    sources: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for label, ref in refs:
        if not ref or not ref.bucket or not ref.object:
            continue
        key = (ref.bucket, ref.object)
        if key in seen:
            continue
        seen.add(key)
        try:
            text = read_object(ref.bucket, ref.object).decode("utf-8", errors="replace")
        except Exception:
            continue
        sources.append({"label": label, "text": text})
    return sources


def metadata_text_refs(material: Material) -> list[tuple[str, ObjectRef | None]]:
    refs: list[tuple[str, ObjectRef | None]] = []
    for label, bucket, object_name in (
        ("Popo Markdown", material.popo_manifest_bucket, material.popo_manifest_object),
        ("MinerU Markdown", material.mineru_manifest_bucket, material.mineru_manifest_object),
    ):
        if not bucket or not object_name:
            continue
        try:
            resolved = resolve_manifest(ObjectRef(bucket, object_name), title=material.title or material.filename or "")
        except Exception:
            continue
        if label.startswith("Popo"):
            refs.extend(
                [
                    ("Popo tree text", resolved.popo_markdown),
                    ("MinerU pages markdown", resolved.page_markdown),
                    ("MinerU full markdown", resolved.markdown),
                ]
            )
        else:
            refs.extend(
                [
                    ("MinerU pages markdown", resolved.page_markdown),
                    ("MinerU full markdown", resolved.markdown),
                ]
            )
    return refs


def keyword_windows(text: str) -> list[str]:
    lowered = text.lower()
    windows: list[str] = []
    spans: list[tuple[int, int]] = []
    for keyword in KEYWORDS:
        start = 0
        needle = keyword.lower()
        while True:
            index = lowered.find(needle, start)
            if index < 0:
                break
            left = max(0, index - KEYWORD_WINDOW_CHARS // 2)
            right = min(len(text), index + KEYWORD_WINDOW_CHARS // 2)
            if not any(abs(left - old_left) < 240 for old_left, _ in spans):
                spans.append((left, right))
                windows.append(text[left:right])
            start = index + len(needle)
            if len(windows) >= 6:
                return windows
    return windows


def call_metadata_model(material: Material, sample: dict[str, Any], catalog_context: dict[str, Any] | None = None) -> dict[str, Any]:
    config = load_runtime_config(include_secrets=True)
    llm = config.get("models", {}).get("llm", {})
    deepseek = llm.get("deepseek", {}) if isinstance(llm.get("deepseek"), dict) else {}
    model = str(llm.get("default_model") or "deepseek-v4-flash")
    base_url = str(deepseek.get("base_url") or "")
    api_key = str(deepseek.get("api_key") or "")
    if not api_key:
        raise MetadataExtractionError("missing_deepseek_api_key")
    if not base_url:
        raise MetadataExtractionError("missing_deepseek_base_url")

    prompt = metadata_prompt(material, sample["text"], catalog_context or {})
    started = time.monotonic()
    parsed: dict[str, Any] | None = None
    last_error: Exception | None = None
    for attempt in range(2):
        response = httpx.post(
            _chat_completions_url(base_url),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You extract and normalize bibliographic metadata for an educational-material catalog. "
                            "Prefer consistent catalog labels over one-off wording. Return one compact JSON object only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt
                        if attempt == 0
                        else prompt + "\n\n上一次输出不是可解析 JSON。请只返回一个紧凑 JSON 对象，不要解释，不要 Markdown。",
                    },
                ],
                "temperature": 0,
                "max_tokens": 2400,
            },
            timeout=60,
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise MetadataExtractionError(model_error_summary(response))
        data = response.json()
        content = str(data.get("choices", [{}])[0].get("message", {}).get("content") or "")
        try:
            parsed = parse_json_content(content)
            break
        except MetadataExtractionError as exc:
            last_error = exc
    if parsed is None:
        raise last_error if last_error else MetadataExtractionError("invalid_model_json")
    parsed["_model"] = model
    parsed["_latency_ms"] = int((time.monotonic() - started) * 1000)
    return parsed


def metadata_prompt(material: Material, sample_text: str, catalog_context: dict[str, Any] | None = None) -> str:
    context_json = json.dumps(catalog_context or {}, ensure_ascii=False, indent=2)
    return f"""
请只根据给出的文件名和抽样文本提取教材元数据。不要根据常识补全，不确定就留空字符串或 null。
目标不是逐字复述文件名，而是生成可用于查询、筛选、归类的稳定元数据。
你会收到一个 catalog_context。它来自同一目录下既有判断，不是外部知识。

需要输出严格 JSON，字段如下：
{{
  "original_title": "正式书名，不含.pdf后缀、压缩标记、作者尾注、Z-Library等来源噪音",
  "publication_date": "出版日期或年份原文",
  "publication_year": 2024,
  "edition": "版别，如 2nd Edition / 第二版；不要把版别放进书名或系列名",
  "subject": "稳定的粗粒度学科，如 Mathematics / English / Science；不要包含考试体系、课程代码、等级、商标、册次、Student Book/Workbook等角色",
  "publication_country": "出版国家或地区",
  "series_name": "稳定系列名或教材族名，没有则空",
  "publisher": "出版社，没有则空",
  "isbn": "ISBN，没有则空",
  "language": "主要语言",
  "grade_level": "年级、阶段、课程体系、考试体系或等级，如 Grade 7 / Cambridge Primary / IGCSE 0580 / AS & A Level；没有则空",
  "confidence": 0.0,
  "evidence": [
    {{"field": "original_title", "quote": "短证据片段", "source": "filename/sample"}}
  ]
}}

约束：
- confidence 是 0 到 1。
- evidence quote 每条不超过 80 字。
- 如果只从文件名推断，confidence 不应超过 0.55。
- original_title 应保留该册的区分信息，例如级别、册号、Student Book、Workbook、Coursebook、Practice Book；但应移除 .pdf、_compress、Z-Library、作者括号等非书名噪音。
- series_name 应用于把同一套书归在一起：去掉级别/册号/年级、版别、Student Book/Workbook/Coursebook/Practice Book/Teacher Resource、年份、作者、出版社、文件扩展名和来源噪音；保留能跨多册复用的核心系列/教材族名称。
- subject 必须比书名更粗粒度、更稳定。不要因为 First Language / Second Language / Core / Extended / Additional / International / Coursebook / Workbook / trademark 符号而创造新学科；这些信息应保留在 original_title 或 grade_level。
- 出现课程代码、考试体系、阶段或体系名时，优先放入 grade_level，不要放入 subject。例：IGCSE、O Level、AS & A Level、Cambridge Primary、Lower Secondary、Grade 8。
- 对同一批命名相近的材料，应使用一致的大小写、空格、标点和字段边界；不要把明显同系列材料拆成不同 series_name 或不同 subject。
- 如果 catalog_context.similar_title_patterns 中存在同系列稳定书名模板，且当前文件名/抽样文本没有 Workbook、Teacher Resource、Practice Book 等冲突证据，应复用该模板规范 original_title，包括 Student Book/Workbook/Coursebook 等角色后缀的大小写和位置。
- 如果只有文件名且文件名明显是一套书的稳定前缀，可以基于文件名提取 series_name；但不要凭外部常识补出版社、国家或年份。
- catalog_context 中 authority=manual_confirmed 的样例是人工确认结果，权重最高；如果当前材料与人工确认样例属于同一系列/同一命名模式，应复用其 subject、series_name、language、publisher、publication_country、publication_year、edition 等稳定字段；册次/年级/上下册等只替换当前材料对应部分。
- catalog_context 中 authority=ai_observed 的样例只作为弱参考。若它和当前抽样证据冲突，以当前抽样证据为准；若它只是命名细节不同，应保持同一字段边界。
- catalog_values 不是强制枚举，但如果语义相同，应优先复用已有标签的大小写和写法，避免产生 English Grammar / Grammar / Reading / English 这种不必要分裂。
- 不要输出 Markdown，不要输出解释，只输出 JSON。

catalog_context：
{context_json}

文件名：{material.filename or ""}
当前 title：{material.title or ""}

抽样文本：
{sample_text}
""".strip()


def apply_ai_result(
    metadata: MaterialMetadata,
    result: dict[str, Any],
    sample: dict[str, Any],
    catalog_context: dict[str, Any],
    material: Material,
) -> None:
    apply_manual_confirmed_context(result, catalog_context, material)
    apply_context_title_patterns(result, catalog_context, material)
    for field in METADATA_FIELDS:
        value = result.get(field)
        if field == "publication_year":
            metadata.publication_year = normalize_year(value)
        else:
            setattr(metadata, field, normalize_text(value))
    confidence = result.get("confidence")
    metadata.confidence = float(confidence) if isinstance(confidence, (int, float)) else None
    evidence = result.get("evidence")
    metadata.update_evidence(evidence if isinstance(evidence, list) else [])
    metadata.update_sample(
        {
            "strategy": sample.get("strategy"),
            "sampled_chars": sample.get("sampled_chars"),
            "sources": sample.get("sources") or [],
            "catalog_context": sample.get("catalog_context") or {},
        }
    )
    metadata.status = "ai_extracted"
    metadata.source = "ai"
    metadata.manual_override = False
    metadata.extraction_model = normalize_text(result.get("_model"))
    metadata.extraction_error = None
    metadata.extracted_at = datetime.utcnow()


def get_or_create_metadata(db: Session, user_id: str, material: Material) -> MaterialMetadata:
    metadata = (
        db.query(MaterialMetadata)
        .filter(MaterialMetadata.user_id == user_id, MaterialMetadata.material_pk == material.id)
        .first()
    )
    if metadata:
        return metadata
    metadata = MaterialMetadata(user_id=user_id, material_pk=material.id, status="missing", source="manual")
    db.add(metadata)
    db.flush()
    return metadata


def metadata_to_dict(metadata: MaterialMetadata | None) -> dict[str, Any] | None:
    return metadata.to_dict() if metadata else None


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()[:512]


def normalize_year(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int) and 1000 <= value <= 2200:
        return value
    match = re.search(r"(1[5-9]\d{2}|20\d{2}|21\d{2})", str(value))
    return int(match.group(1)) if match else None


def normalize_space(text: str) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", str(text or "")).strip()


def parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    elif "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MetadataExtractionError(f"invalid_model_json:{exc}") from exc
    if not isinstance(parsed, dict):
        raise MetadataExtractionError("invalid_model_json:not_object")
    return parsed


def model_error_summary(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return response.text[:300]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("code") or error)[:300]
        if error:
            return str(error)[:300]
    return str(payload)[:300]


def _distinct_values(db: Session, user_id: str, column: Any) -> list[str]:
    rows = (
        db.query(distinct(column))
        .filter(MaterialMetadata.user_id == user_id, column.isnot(None), column != "")
        .order_by(column.asc())
        .limit(100)
        .all()
    )
    return [str(row[0]) for row in rows if row and row[0]]
