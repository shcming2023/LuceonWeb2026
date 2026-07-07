import json
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, UniqueConstraint

from .base import Base


class MaterialMetadata(Base):
    __tablename__ = "material_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    material_pk = Column(Integer, nullable=False, index=True)

    original_title = Column(String(512), nullable=True, index=True)
    publication_date = Column(String(64), nullable=True)
    publication_year = Column(Integer, nullable=True, index=True)
    edition = Column(String(256), nullable=True, index=True)
    subject = Column(String(128), nullable=True, index=True)
    publication_country = Column(String(128), nullable=True, index=True)
    series_name = Column(String(256), nullable=True, index=True)
    publisher = Column(String(256), nullable=True, index=True)
    isbn = Column(String(128), nullable=True, index=True)
    language = Column(String(128), nullable=True, index=True)
    grade_level = Column(String(128), nullable=True, index=True)

    status = Column(String(32), nullable=False, default="missing", index=True)
    source = Column(String(32), nullable=False, default="manual", index=True)
    confidence = Column(Float, nullable=True)
    manual_override = Column(Boolean, nullable=False, default=False, index=True)

    evidence_json = Column(Text, nullable=True)
    sample_json = Column(Text, nullable=True)
    extraction_model = Column(String(128), nullable=True)
    extraction_error = Column(Text, nullable=True)
    extracted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "material_pk", name="uq_material_metadata_user_material"),)

    def evidence(self) -> list[dict[str, Any]]:
        return _loads_list(self.evidence_json)

    def sample(self) -> dict[str, Any]:
        return _loads_dict(self.sample_json)

    def update_evidence(self, value: list[dict[str, Any]]) -> None:
        self.evidence_json = json.dumps(value[:12], ensure_ascii=False)

    def update_sample(self, value: dict[str, Any]) -> None:
        self.sample_json = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "material_pk": str(self.material_pk),
            "original_title": self.original_title or "",
            "publication_date": self.publication_date or "",
            "publication_year": self.publication_year,
            "edition": self.edition or "",
            "subject": self.subject or "",
            "publication_country": self.publication_country or "",
            "series_name": self.series_name or "",
            "publisher": self.publisher or "",
            "isbn": self.isbn or "",
            "language": self.language or "",
            "grade_level": self.grade_level or "",
            "status": self.status or "missing",
            "source": self.source or "manual",
            "confidence": self.confidence,
            "manual_override": bool(self.manual_override),
            "evidence": self.evidence(),
            "sample": self.sample(),
            "extraction_model": self.extraction_model or "",
            "extraction_error": self.extraction_error or "",
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def _loads_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _loads_list(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
