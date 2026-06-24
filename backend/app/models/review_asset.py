from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


class ReviewAsset(Base):
    __tablename__ = "review_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False, index=True)
    input_filename = Column(String(512), nullable=True, index=True)
    review_stage = Column(String(32), nullable=False, default="parse", index=True)
    material_id = Column(String(128), nullable=True, index=True)
    run_id = Column(String(128), nullable=True, index=True)
    manifest_bucket = Column(String(128), nullable=False)
    manifest_object = Column(String(1024), nullable=False)
    input_pdf_bucket = Column(String(128), nullable=True)
    input_pdf_object = Column(String(1024), nullable=True)
    source_pdf_bucket = Column(String(128), nullable=True)
    source_pdf_object = Column(String(1024), nullable=True)
    markdown_bucket = Column(String(128), nullable=True)
    markdown_object = Column(String(1024), nullable=True)
    page_markdown_bucket = Column(String(128), nullable=True)
    page_markdown_object = Column(String(1024), nullable=True)
    popo_markdown_bucket = Column(String(128), nullable=True)
    popo_markdown_object = Column(String(1024), nullable=True)
    middle_json_bucket = Column(String(128), nullable=True)
    middle_json_object = Column(String(1024), nullable=True)
    manifest_json = Column(Text, nullable=True)
    review_status = Column(String(32), nullable=False, default="pending", index=True)
    review_tags = Column(Text, nullable=True)
    review_note = Column(Text, nullable=True)
    report_text = Column(Text, nullable=True)
    report_generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_review_user_manifest", "user_id", "manifest_bucket", "manifest_object", unique=True),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "filename": self.display_filename(),
            "size": 0,
            "status": "parsed" if self.manifest_json else "pending",
            "upload_time": self.created_at.isoformat() if self.created_at else None,
            "has_manifest": bool(self.manifest_json),
            "input_filename": self.input_filename or "",
            "review_stage": self.review_stage or "parse",
            "material_id": self.material_id,
            "run_id": self.run_id,
            "manifest_bucket": self.manifest_bucket,
            "manifest_object": self.manifest_object,
            "input_pdf": {
                "bucket": self.input_pdf_bucket,
                "object": self.input_pdf_object,
            },
            "source_pdf": {
                "bucket": self.source_pdf_bucket,
                "object": self.source_pdf_object,
            },
            "markdown": {
                "bucket": self.markdown_bucket,
                "object": self.markdown_object,
            },
            "page_markdown": {
                "bucket": self.page_markdown_bucket,
                "object": self.page_markdown_object,
            },
            "popo_markdown": {
                "bucket": self.popo_markdown_bucket,
                "object": self.popo_markdown_object,
            },
            "middle_json": {
                "bucket": self.middle_json_bucket,
                "object": self.middle_json_object,
            },
            "review_status": self.review_status or "pending",
            "review_tags": self._review_tags(),
            "review_note": self.review_note or "",
            "report_generated_at": self.report_generated_at.isoformat() if self.report_generated_at else None,
            "has_report": bool(self.report_text),
        }

    def _review_tags(self) -> list[str]:
        if not self.review_tags:
            return []
        import json

        try:
            value = json.loads(self.review_tags)
        except json.JSONDecodeError:
            return []
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]

    def display_filename(self) -> str:
        value = self.input_filename or self.title
        if value.lower().endswith(".pdf"):
            return value
        return f"{value}.pdf"
