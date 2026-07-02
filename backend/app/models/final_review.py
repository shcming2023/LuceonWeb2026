import json
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


def _loads_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


class FinalReviewSession(Base):
    __tablename__ = "final_review_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    review_asset_id = Column(Integer, nullable=False, index=True)
    material_id = Column(String(128), nullable=False, index=True)
    standard_run_id = Column(String(128), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="open", index=True)
    summary_json = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_final_review_session_asset", "user_id", "review_asset_id", "standard_run_id"),
    )

    def summary(self) -> dict[str, Any]:
        value = _loads_json(self.summary_json, {})
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "review_asset_id": str(self.review_asset_id),
            "material_id": self.material_id,
            "standard_run_id": self.standard_run_id or "",
            "status": self.status,
            "summary": self.summary(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FinalReviewAnnotation(Base):
    __tablename__ = "final_review_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    issue_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False, default="major", index=True)
    status = Column(String(32), nullable=False, default="draft", index=True)
    human_note = Column(Text, nullable=True)
    anchors_json = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_final_review_annotation_session", "session_id", "status"),
    )

    def anchors(self) -> dict[str, Any]:
        value = _loads_json(self.anchors_json, {})
        return value if isinstance(value, dict) else {}

    def evidence(self) -> dict[str, Any]:
        value = _loads_json(self.evidence_json, {})
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "issue_type": self.issue_type,
            "severity": self.severity,
            "status": self.status,
            "human_note": self.human_note or "",
            "anchors": self.anchors(),
            "evidence": self.evidence(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FinalReviewVerification(Base):
    __tablename__ = "final_review_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    annotation_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="verified", index=True)
    root_cause_stage = Column(String(64), nullable=False, default="unknown_needs_review", index=True)
    root_cause_label = Column(String(64), nullable=False, default="qa_gate_gap", index=True)
    confidence = Column(Float, nullable=False, default=0.4)
    evidence_json = Column(Text, nullable=True)
    proposed_action_json = Column(Text, nullable=True)
    model_info_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def evidence(self) -> dict[str, Any]:
        value = _loads_json(self.evidence_json, {})
        return value if isinstance(value, dict) else {}

    def proposed_action(self) -> dict[str, Any]:
        value = _loads_json(self.proposed_action_json, {})
        return value if isinstance(value, dict) else {}

    def model_info(self) -> dict[str, Any]:
        value = _loads_json(self.model_info_json, {})
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "annotation_id": str(self.annotation_id),
            "status": self.status,
            "root_cause_stage": self.root_cause_stage,
            "root_cause_label": self.root_cause_label,
            "confidence": self.confidence,
            "evidence": self.evidence(),
            "proposed_action": self.proposed_action(),
            "model_info": self.model_info(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FinalReviewDecision(Base):
    __tablename__ = "final_review_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    annotation_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    decision = Column(String(64), nullable=False, index=True)
    reviewer_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "annotation_id": str(self.annotation_id),
            "decision": self.decision,
            "reviewer_note": self.reviewer_note or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
