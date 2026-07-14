from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.workflow_v2.golden_set import GOLDEN_CASES, ensure_golden_set, list_golden_set
from app.workflow_v2.models import GoldenRegressionCase, WorkflowBase


def test_golden_set_is_fixed_diverse_and_not_authorized_for_execution():
    engine = create_engine("sqlite://")
    WorkflowBase.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    ensure_golden_set(db)
    ensure_golden_set(db)
    db.commit()

    rows = list_golden_set(db)
    dimensions = {item for row in rows for item in row["dimensions"]}
    assert len(GOLDEN_CASES) == len(rows) == db.query(GoldenRegressionCase).count() == 10
    assert len({row["material_id"] for row in rows}) == 10
    assert {"mathematics", "english", "chinese", "image-rich", "formula-heavy", "writing"} <= dimensions
    assert all(row["baseline"]["execution_authorized"] is False for row in rows)
