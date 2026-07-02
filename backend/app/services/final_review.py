import io
import json
from collections import Counter
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.final_review import (
    FinalReviewAnnotation,
    FinalReviewDecision,
    FinalReviewSession,
    FinalReviewVerification,
)
from app.models.material import Material
from app.models.review_asset import ReviewAsset
from app.services.luceon_review import ObjectRef, clean_path, is_missing_object_error, object_exists, read_object
from app.utils.minio_client import minio_client


FINAL_REVIEW_BUCKET = "eduassets-review"

ISSUE_TYPES = {
    "missing_content",
    "extra_noise",
    "wrong_order",
    "heading_hierarchy",
    "question_grouping",
    "option_answer_blank",
    "image_missing",
    "image_wrong_parent",
    "image_should_keep",
    "image_should_drop",
    "table_broken",
    "formula_broken",
    "ocr_text_error",
    "print_layout",
    "needs_ai_check",
}
SEVERITIES = {"minor", "major", "blocker"}
SESSION_STATUSES = {"open", "submitted", "verifying", "project_review", "resolved", "archived"}
ANNOTATION_STATUSES = {
    "draft",
    "submitted",
    "verified",
    "rejected",
    "root_caused",
    "fix_proposed",
    "project_accepted",
    "project_rejected",
    "resolved",
}
DECISIONS = {"accept", "reject", "needs_more_evidence", "rerun_raw", "rerun_clean", "rerun_standard", "upstream_limited"}


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def material_for_asset(asset: ReviewAsset, db: Session) -> Material | None:
    query = db.query(Material).filter(Material.user_id == asset.user_id)
    if asset.material_id:
        material = query.filter(Material.material_id == asset.material_id).order_by(Material.id.desc()).first()
        if material:
            return material
    if asset.input_pdf_bucket and asset.input_pdf_object:
        return (
            query.filter(
                Material.input_bucket == asset.input_pdf_bucket,
                Material.input_object == asset.input_pdf_object,
            )
            .order_by(Material.id.desc())
            .first()
        )
    return None


def require_standard_material(asset: ReviewAsset, db: Session) -> Material:
    material = material_for_asset(asset, db)
    if not material or not material.standard_manifest_bucket or not material.standard_manifest_object:
        raise HTTPException(status_code=400, detail="该材料尚未生成 Standard，不能进入终极审查")
    return material


def session_or_404(session_id: int, user_id: str, db: Session) -> FinalReviewSession:
    session = db.query(FinalReviewSession).filter(FinalReviewSession.id == session_id, FinalReviewSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="终审会话不存在")
    return session


def annotation_or_404(annotation_id: int, user_id: str, db: Session) -> FinalReviewAnnotation:
    annotation = (
        db.query(FinalReviewAnnotation)
        .filter(FinalReviewAnnotation.id == annotation_id, FinalReviewAnnotation.user_id == user_id)
        .first()
    )
    if not annotation:
        raise HTTPException(status_code=404, detail="终审批注不存在")
    return annotation


def annotations_for_session(session_id: int, db: Session) -> list[FinalReviewAnnotation]:
    return (
        db.query(FinalReviewAnnotation)
        .filter(FinalReviewAnnotation.session_id == session_id)
        .order_by(FinalReviewAnnotation.created_at.asc(), FinalReviewAnnotation.id.asc())
        .all()
    )


def latest_verifications(annotation_ids: list[int], db: Session) -> dict[int, FinalReviewVerification]:
    if not annotation_ids:
        return {}
    rows = (
        db.query(FinalReviewVerification)
        .filter(FinalReviewVerification.annotation_id.in_(annotation_ids))
        .order_by(FinalReviewVerification.created_at.asc(), FinalReviewVerification.id.asc())
        .all()
    )
    result: dict[int, FinalReviewVerification] = {}
    for row in rows:
        result[row.annotation_id] = row
    return result


def decisions_for_annotations(annotation_ids: list[int], db: Session) -> dict[int, list[FinalReviewDecision]]:
    if not annotation_ids:
        return {}
    rows = (
        db.query(FinalReviewDecision)
        .filter(FinalReviewDecision.annotation_id.in_(annotation_ids))
        .order_by(FinalReviewDecision.created_at.asc(), FinalReviewDecision.id.asc())
        .all()
    )
    result: dict[int, list[FinalReviewDecision]] = {}
    for row in rows:
        result.setdefault(row.annotation_id, []).append(row)
    return result


def session_to_dict(session: FinalReviewSession, db: Session) -> dict[str, Any]:
    annotations = annotations_for_session(session.id, db)
    annotation_ids = [row.id for row in annotations]
    verifications = latest_verifications(annotation_ids, db)
    decisions = decisions_for_annotations(annotation_ids, db)
    counts = Counter(row.status for row in annotations)
    payload = session.to_dict()
    payload["counts"] = {
        "annotations": len(annotations),
        "draft": counts.get("draft", 0),
        "submitted": counts.get("submitted", 0),
        "root_caused": counts.get("root_caused", 0),
        "fix_proposed": counts.get("fix_proposed", 0),
        "project_accepted": counts.get("project_accepted", 0),
        "project_rejected": counts.get("project_rejected", 0),
    }
    payload["annotations"] = [
        {
            **row.to_dict(),
            "verification": verifications[row.id].to_dict() if row.id in verifications else None,
            "decisions": [decision.to_dict() for decision in decisions.get(row.id, [])],
        }
        for row in annotations
    ]
    return payload


def _ref(bucket: str | None, object_name: str | None) -> ObjectRef | None:
    if bucket and object_name:
        return ObjectRef(bucket=bucket, object=object_name)
    return None


def _manifest_ref_from_material(material: Material | None, stage: str) -> ObjectRef | None:
    if not material:
        return None
    if stage == "mineru":
        return _ref(material.mineru_manifest_bucket, material.mineru_manifest_object)
    if stage in {"popo", "minerupopo"}:
        return _ref(material.popo_manifest_bucket, material.popo_manifest_object)
    if stage == "raw":
        return _ref(material.raw_manifest_bucket, material.raw_manifest_object)
    if stage == "clean":
        return _ref(material.clean_manifest_bucket, material.clean_manifest_object)
    if stage == "standard":
        return _ref(material.standard_manifest_bucket, material.standard_manifest_object)
    return None


def _same_prefix_ref(manifest_ref: ObjectRef | None, filename: str) -> ObjectRef | None:
    if not manifest_ref:
        return None
    prefix = manifest_ref.object.rsplit("/", 1)[0] + "/" if "/" in manifest_ref.object else ""
    return ObjectRef(manifest_ref.bucket, clean_path(f"{prefix}{filename}"))


def _ref_from_manifest_value(value: Any, manifest_ref: ObjectRef | None) -> ObjectRef | None:
    if not manifest_ref:
        return None
    bucket = manifest_ref.bucket
    object_name = ""
    if isinstance(value, dict):
        bucket = str(value.get("bucket") or bucket)
        object_name = clean_path(value.get("object") or value.get("key") or value.get("path"))
    elif isinstance(value, str):
        object_name = clean_path(value)
    if not object_name:
        return None
    if "/" not in object_name:
        prefix = manifest_ref.object.rsplit("/", 1)[0] + "/" if "/" in manifest_ref.object else ""
        object_name = clean_path(f"{prefix}{object_name}")
    return ObjectRef(bucket, object_name)


def _read_json_optional(ref: ObjectRef | None) -> dict[str, Any] | None:
    if not ref or not object_exists(ref.bucket, ref.object):
        return None
    try:
        parsed = json.loads(read_object(ref.bucket, ref.object).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _read_text_excerpt(ref: ObjectRef | None, limit: int = 4000) -> dict[str, Any]:
    if not ref or not object_exists(ref.bucket, ref.object):
        return {"available": False, "ref": _ref_dict(ref)}
    text = read_object(ref.bucket, ref.object).decode("utf-8", errors="replace")
    return {
        "available": True,
        "ref": _ref_dict(ref),
        "char_count": len(text),
        "excerpt": text[:limit],
        "truncated": len(text) > limit,
    }


def _ref_dict(ref: ObjectRef | None) -> dict[str, str]:
    return ref.as_dict() if ref else {"bucket": "", "object": ""}


def _pick_stage_object(manifest: dict[str, Any] | None, manifest_ref: ObjectRef | None, keys: tuple[str, ...], fallback: str) -> ObjectRef | None:
    candidates: list[ObjectRef | None] = []
    objects = manifest.get("objects") if isinstance(manifest, dict) and isinstance(manifest.get("objects"), dict) else {}
    for key in keys:
        candidates.append(_ref_from_manifest_value(objects.get(key), manifest_ref))
        candidates.append(_ref_from_manifest_value(manifest.get(key), manifest_ref) if isinstance(manifest, dict) else None)
    candidates.append(_same_prefix_ref(manifest_ref, fallback))
    for ref in candidates:
        if ref and object_exists(ref.bucket, ref.object):
            return ref
    return None


def collect_annotation_evidence(
    session: FinalReviewSession,
    annotation: FinalReviewAnnotation,
    asset: ReviewAsset,
    material: Material,
) -> dict[str, Any]:
    standard_manifest_ref = _manifest_ref_from_material(material, "standard")
    clean_manifest_ref = _manifest_ref_from_material(material, "clean")
    raw_manifest_ref = _manifest_ref_from_material(material, "raw")
    popo_manifest_ref = _manifest_ref_from_material(material, "popo")
    mineru_manifest_ref = _manifest_ref_from_material(material, "mineru")

    standard_manifest = _read_json_optional(standard_manifest_ref)
    clean_manifest = _read_json_optional(clean_manifest_ref)
    raw_manifest = _read_json_optional(raw_manifest_ref)
    standard_document_ref = _pick_stage_object(
        standard_manifest,
        standard_manifest_ref,
        ("standard_document_json", "standard_document"),
        "standard_document.json",
    )
    standard_html_ref = _pick_stage_object(standard_manifest, standard_manifest_ref, ("standard_html", "html"), "standard.html")
    standard_md_ref = _pick_stage_object(standard_manifest, standard_manifest_ref, ("standard_md", "standard_markdown", "markdown"), "standard.md")
    clean_md_ref = _pick_stage_object(clean_manifest, clean_manifest_ref, ("clean_md", "clean_markdown", "markdown"), "clean.md")
    raw_md_ref = _pick_stage_object(raw_manifest, raw_manifest_ref, ("raw_markdown", "markdown", "clean_md"), "clean.md")

    return {
        "schema": "luceon-final-review-evidence/v1",
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "asset": {
            "review_asset_id": str(asset.id),
            "title": asset.title,
            "material_id": asset.material_id or "",
            "input_pdf": _ref_dict(_ref(asset.input_pdf_bucket, asset.input_pdf_object)),
            "source_pdf": _ref_dict(_ref(asset.source_pdf_bucket, asset.source_pdf_object)),
        },
        "session": {
            "id": str(session.id),
            "material_id": session.material_id,
            "standard_run_id": session.standard_run_id or "",
        },
        "annotation": annotation.to_dict(),
        "stage_refs": {
            "standard_manifest": _ref_dict(standard_manifest_ref),
            "standard_document": _ref_dict(standard_document_ref),
            "standard_html": _ref_dict(standard_html_ref),
            "standard_markdown": _ref_dict(standard_md_ref),
            "clean_manifest": _ref_dict(clean_manifest_ref),
            "clean_markdown": _ref_dict(clean_md_ref),
            "raw_manifest": _ref_dict(raw_manifest_ref),
            "raw_markdown": _ref_dict(raw_md_ref),
            "popo_manifest": _ref_dict(popo_manifest_ref),
            "mineru_manifest": _ref_dict(mineru_manifest_ref),
        },
        "stage_status": {
            "standard_quality_score": material.standard_quality_score,
            "material_stage_status": material.stage_status,
            "pipeline_status": material.pipeline_status,
            "raw_run_id": material.raw_run_id or "",
            "clean_run_id": material.clean_run_id or "",
            "standard_run_id": material.standard_run_id or "",
        },
        "standard": {
            "manifest_available": bool(standard_manifest),
            "document_available": bool(standard_document_ref),
            "html_available": bool(standard_html_ref),
            "markdown": _read_text_excerpt(standard_md_ref),
        },
        "clean": {
            "manifest_available": bool(clean_manifest),
            "markdown": _read_text_excerpt(clean_md_ref),
        },
        "raw": {
            "manifest_available": bool(raw_manifest),
            "markdown": _read_text_excerpt(raw_md_ref),
        },
    }


def classify_root_cause(annotation: FinalReviewAnnotation, evidence: dict[str, Any]) -> tuple[str, str, float, dict[str, Any]]:
    issue_type = annotation.issue_type
    anchors = annotation.anchors()
    stage_refs = evidence.get("stage_refs", {}) if isinstance(evidence, dict) else {}
    raw_available = bool(stage_refs.get("raw_manifest", {}).get("object"))
    note = annotation.human_note or ""

    if issue_type == "formula_broken":
        stage, label, target, confidence = "standard_rendering", "math_rendering", "standard", 0.72
    elif issue_type == "option_answer_blank":
        stage, label, target, confidence = "standard_rendering", "answer_blank_rendering", "standard", 0.7
    elif issue_type == "print_layout":
        stage, label, target, confidence = "standard_layout", "html_layout", "standard", 0.7
    elif issue_type in {"question_grouping", "image_wrong_parent"}:
        stage, label, target, confidence = "standard_grouping", "block_assignment", "standard", 0.62
    elif issue_type in {"wrong_order", "heading_hierarchy"}:
        stage = "raw_outline" if raw_available else "unknown_needs_review"
        label = "anchor_application" if raw_available else "qa_gate_gap"
        target, confidence = "raw", 0.58
    elif issue_type in {"missing_content", "ocr_text_error"}:
        stage = "clean_underrepair" if raw_available else "mineru_ocr_layout"
        label = "upstream_noise_absorption"
        target, confidence = "clean", 0.52
    elif issue_type == "extra_noise":
        stage, label, target, confidence = "clean_overclean", "upstream_noise_absorption", "clean", 0.52
    elif issue_type in {"image_missing", "image_should_keep", "image_should_drop"}:
        stage, label, target, confidence = "clean_underrepair", "candidate_extraction", "clean", 0.5
    elif issue_type == "table_broken":
        stage, label, target, confidence = "standard_layout", "html_layout", "standard", 0.56
    elif issue_type == "needs_ai_check":
        stage, label, target, confidence = _classify_open_feedback(note, raw_available)
    else:
        stage, label, target, confidence = "unknown_needs_review", "qa_gate_gap", "review", 0.35

    proposed_action = {
        "target_stage": target,
        "root_cause_stage": stage,
        "root_cause_label": label,
        "evidence_refs": stage_refs,
        "recommended_action": _recommended_action(target, issue_type),
        "generalizable_rule_candidate": _rule_candidate(issue_type, anchors),
        "rerun_required": target in {"raw", "clean", "standard"},
        "risk_note": "仅生成修订建议，不直接修改 Clean 或 Standard 输出物。",
    }
    return stage, label, confidence, proposed_action


def _classify_open_feedback(note: str, raw_available: bool) -> tuple[str, str, str, float]:
    normalized = note.lower()
    if _has_any(normalized, ("公式", "latex", "katex", "math", "sqrt", "frac")):
        return "standard_rendering", "math_rendering", "standard", 0.66
    if _has_any(normalized, ("填空", "空格", "____", "blank", "t/f", "true or false", "对错判断", "判断题", "选项")):
        return "standard_rendering", "answer_blank_rendering", "standard", 0.62
    if _has_any(normalized, ("不是正文", "非正文", "目录页", "extra", "noise", "噪音")):
        return "clean_overclean", "upstream_noise_absorption", "clean", 0.54
    if _has_any(normalized, ("main idea", "detail", "reference", "vocabulary", "题目的分类", "题组", "关联关系", "题干")):
        return "standard_grouping", "block_assignment", "standard", 0.62
    if _has_any(normalized, ("分栏", "布局", "排版", "过大", "不协调", "左对齐", "右对齐", "打印")):
        return "standard_layout", "html_layout", "standard", 0.6
    if _has_any(normalized, ("不需要", "目录")):
        return "clean_overclean", "upstream_noise_absorption", "clean", 0.48
    if _has_any(normalized, ("顺序", "目录层级", "标题层级", "章节")):
        if raw_available:
            return "raw_outline", "anchor_application", "raw", 0.56
        return "unknown_needs_review", "qa_gate_gap", "review", 0.35
    return "unknown_needs_review", "qa_gate_gap", "review", 0.35


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _recommended_action(target: str, issue_type: str) -> str:
    if target == "standard":
        return f"优化 Standard 分组/渲染规则后重跑 Standard；问题类型：{issue_type}"
    if target == "clean":
        return f"检查 Clean 保守清洗与证据补足规则后重跑 Clean/Standard；问题类型：{issue_type}"
    if target == "raw":
        return f"检查 Raw 目录锚点、block assignment 或 QA 门禁后重跑 Raw/Clean/Standard；问题类型：{issue_type}"
    if target == "review":
        return "需要项目核查补充证据，暂不进入自动修订。"
    return "记录上游限制，避免用材料特例硬编码绕过。"


def _rule_candidate(issue_type: str, anchors: dict[str, Any]) -> str:
    heading_path = anchors.get("heading_path") if isinstance(anchors.get("heading_path"), list) else []
    context = " > ".join(str(item) for item in heading_path if item)
    if issue_type in {"question_grouping", "option_answer_blank"}:
        return f"在同一题组上下文内保持题干、选项、空格、答案区域连续；上下文：{context}"
    if issue_type in {"formula_broken", "table_broken"}:
        return f"将公式/表格作为不可拆结构校验渲染完整性；上下文：{context}"
    if issue_type.startswith("image_"):
        return f"基于 caption、相邻题干和页面位置校验图片归属；上下文：{context}"
    return f"基于章节路径和相邻块证据生成可复用修正规则；上下文：{context}"


def verify_annotation(annotation: FinalReviewAnnotation, asset: ReviewAsset, material: Material, db: Session) -> FinalReviewVerification:
    session = db.query(FinalReviewSession).filter(FinalReviewSession.id == annotation.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="终审会话不存在")
    evidence = collect_annotation_evidence(session, annotation, asset, material)
    stage, label, confidence, proposed_action = classify_root_cause(annotation, evidence)
    verification = FinalReviewVerification(
        annotation_id=annotation.id,
        user_id=annotation.user_id,
        status="verified",
        root_cause_stage=stage,
        root_cause_label=label,
        confidence=confidence,
        evidence_json=json_dumps(evidence),
        proposed_action_json=json_dumps(proposed_action),
        model_info_json=json_dumps({"mode": "deterministic_v1", "llm_used": False}),
    )
    db.add(verification)
    annotation.status = "root_caused"
    session.status = "project_review"
    return verification


def add_decision(annotation: FinalReviewAnnotation, decision: str, reviewer_note: str, user_id: str, db: Session) -> FinalReviewDecision:
    if decision not in DECISIONS:
        raise HTTPException(status_code=400, detail="不支持的项目决策")
    row = FinalReviewDecision(
        annotation_id=annotation.id,
        user_id=user_id,
        decision=decision,
        reviewer_note=reviewer_note.strip(),
    )
    db.add(row)
    if decision == "accept":
        annotation.status = "project_accepted"
    elif decision in {"rerun_raw", "rerun_clean", "rerun_standard", "upstream_limited"}:
        annotation.status = "fix_proposed"
    elif decision == "reject":
        annotation.status = "project_rejected"
    else:
        annotation.status = "rejected"
    return row


def export_payloads(session: FinalReviewSession, db: Session) -> dict[str, bytes]:
    annotations = annotations_for_session(session.id, db)
    annotation_ids = [row.id for row in annotations]
    verifications = latest_verifications(annotation_ids, db)
    decisions = decisions_for_annotations(annotation_ids, db)
    exported_at = datetime.utcnow().isoformat() + "Z"

    ledger_rows = []
    for annotation in annotations:
        row = annotation.to_dict()
        row["verification"] = verifications[annotation.id].to_dict() if annotation.id in verifications else None
        row["decisions"] = [decision.to_dict() for decision in decisions.get(annotation.id, [])]
        ledger_rows.append(row)

    root_counter = Counter(
        verification.root_cause_stage
        for verification in verifications.values()
        if verification.root_cause_stage
    )
    decision_rows = [decision.to_dict() for rows in decisions.values() for decision in rows]
    summary = {
        "schema": "luceon-final-review-summary/v1",
        "exported_at": exported_at,
        "session": session.to_dict(),
        "counts": {
            "annotations": len(annotations),
            "verifications": len(verifications),
            "decisions": len(decision_rows),
        },
        "status_counts": dict(Counter(annotation.status for annotation in annotations)),
        "severity_counts": dict(Counter(annotation.severity for annotation in annotations)),
    }
    root_report = {
        "schema": "luceon-final-review-root-cause/v1",
        "exported_at": exported_at,
        "session": session.to_dict(),
        "root_cause_stage_counts": dict(root_counter),
        "verifications": [verification.to_dict() for verification in verifications.values()],
    }
    return {
        "final_review_ledger.jsonl": ("\n".join(json_dumps(row) for row in ledger_rows) + ("\n" if ledger_rows else "")).encode("utf-8"),
        "root_cause_report.json": json_dumps(root_report).encode("utf-8"),
        "project_decisions.jsonl": ("\n".join(json_dumps(row) for row in decision_rows) + ("\n" if decision_rows else "")).encode("utf-8"),
        "review_summary.json": json_dumps(summary).encode("utf-8"),
    }


def export_session_artifacts(session: FinalReviewSession, db: Session) -> dict[str, Any]:
    prefix = clean_path(f"final_review/{session.material_id}/{session.standard_run_id or 'standard-run-unknown'}/{session.id}")
    payloads = export_payloads(session, db)
    try:
        if not minio_client.bucket_exists(FINAL_REVIEW_BUCKET):
            minio_client.make_bucket(FINAL_REVIEW_BUCKET)
        refs = {}
        for name, content in payloads.items():
            object_name = clean_path(f"{prefix}/{name}")
            minio_client.put_object(
                FINAL_REVIEW_BUCKET,
                object_name,
                io.BytesIO(content),
                len(content),
                content_type="application/json" if name.endswith(".json") else "application/x-ndjson",
            )
            refs[name] = {"bucket": FINAL_REVIEW_BUCKET, "object": object_name}
    except Exception as exc:
        if is_missing_object_error(exc):
            raise HTTPException(status_code=500, detail=f"终审归档桶不可用：{exc}") from exc
        raise
    return {
        "bucket": FINAL_REVIEW_BUCKET,
        "prefix": prefix,
        "objects": refs,
    }
