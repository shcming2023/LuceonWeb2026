from __future__ import annotations

from sqlalchemy.orm import Session

from app.workflow_v2.models import GoldenRegressionCase


GOLDEN_COHORT_VERSION = "worker-v2-golden-2026-07-11"

GOLDEN_CASES = (
    ("theme-reading", 1327, "pdf-c01773ffbba92a91", "2026SSP上海暑假初中进阶版-主题精读.pdf", ["bilingual", "reading", "workbook", "qr", "mixed-layout"], "Primary acceptance sample; exposes numbering, choice grouping, answer-space, QR and page-expansion defects."),
    ("new-question-types", 1326, "pdf-1b34e6163ff04195", "2026SSP上海暑假初中进阶版-新题型探索.pdf", ["chinese", "english", "new-question-types", "image-rich"], "Sibling SSP volume with different exercise structures and an existing legacy output."),
    ("amc10-large", 1332, "pdf-cfe425e404b99f6f", "V1 AMC10.pdf", ["mathematics", "formula-heavy", "large-file", "long-document"], "Large formula-heavy stress case from the newest GPU batch."),
    ("pemberton-igcse-math", 1330, "pdf-c2e244a2a30b08fa", "Pemberton Mathematics for Cambridge IGCSE Extended Student Book.pdf", ["mathematics", "textbook", "diagram", "long-document"], "Long textbook case with diagrams, formulas, worked examples and legacy versions."),
    ("igcse-english", 949, "pdf-10609bb8e1159052", "0500 Cambridge IGCSE English Students Book, 3rd Edition.pdf", ["english", "reading", "writing", "textbook"], "English reading and extended-writing case with long answer surfaces."),
    ("grammar-friends-3", 1012, "pdf-0b7b610b19e63537", "Grammar Friends 3 (Students Book).pdf", ["english", "grammar", "image-rich", "young-learner"], "Image-rich young-learner workbook with short prompts and dense visual exercises."),
    ("amc8-small", 954, "pdf-037fdccc525f7536", "AMC8_2026_Solutions.pdf", ["mathematics", "small-file", "solutions", "formula"], "Small mathematical solution booklet that catches fixed-overhead and short-document regressions."),
    ("great-writing-3", 1025, "pdf-0b220957896bae1e", "Great Writing 3, Fifth Edition.pdf", ["english", "writing", "long-answer", "large-file"], "Writing-focused workbook for printable answer-space and paragraph-layout gates."),
    ("chinese-primary-math", 953, "pdf-4ff6a5f9abc595a1", "2026新版 四上 教材全解.pdf", ["chinese", "primary-math", "mixed-layout", "image-rich"], "Chinese primary mathematics case with mixed OCR, diagrams and compact exercises."),
    ("additional-math-workbook", 982, "pdf-95f334cd6d91c504", "Cambridge IGCSE Additional Mathematics Workbook 2018.pdf", ["mathematics", "workbook", "formula-heavy", "answer-space"], "Compact formula-heavy workbook for question grouping and printable working-space gates."),
)


def ensure_golden_set(db: Session) -> None:
    for case_key, material_pk, material_id, title, dimensions, reason in GOLDEN_CASES:
        row = db.query(GoldenRegressionCase).filter(GoldenRegressionCase.case_key == case_key).first()
        if row:
            continue
        db.add(
            GoldenRegressionCase(
                cohort_version=GOLDEN_COHORT_VERSION,
                case_key=case_key,
                material_pk=material_pk,
                material_id=material_id,
                title=title,
                dimensions_json=GoldenRegressionCase.dump(dimensions),
                selection_reason=reason,
                baseline_json=GoldenRegressionCase.dump({"legacy_preserved": True, "execution_authorized": False}),
                status="selected",
            )
        )
    db.flush()


def list_golden_set(db: Session) -> list[dict]:
    rows = db.query(GoldenRegressionCase).order_by(GoldenRegressionCase.id).all()
    return [
        {
            "case_key": row.case_key,
            "cohort_version": row.cohort_version,
            "material_pk": str(row.material_pk),
            "material_id": row.material_id,
            "title": row.title,
            "dimensions": row.load(row.dimensions_json, []),
            "selection_reason": row.selection_reason,
            "baseline": row.load(row.baseline_json, {}),
            "status": row.status,
        }
        for row in rows
    ]
