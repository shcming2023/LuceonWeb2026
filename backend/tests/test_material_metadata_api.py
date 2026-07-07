from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models.base import Base
from app.models.material import Material
from app.models.material_metadata import MaterialMetadata
from app.services import material_metadata as metadata_service
from main import app


def make_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, testing_session


def test_manual_metadata_update_is_searchable(monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    client, testing_session = make_client()
    try:
        client.post("/api/auth/register", json={"email": "meta@example.com", "password": "secret123"})
        db = testing_session()
        material = Material(
            user_id="1",
            title="Cambridge Secondary Mathematics Learners Book 7.pdf",
            filename="Cambridge Secondary Mathematics Learners Book 7.pdf",
            source_type="imported",
            stage_status="input",
            pipeline_status="idle",
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        db.close()

        response = client.patch(
            f"/api/materials/{material.id}/metadata",
            json={
                "original_title": "Cambridge Secondary Mathematics Learner's Book 7",
                "publication_year": 2021,
                "edition": "2nd Edition",
                "subject": "Mathematics",
                "publication_country": "United Kingdom",
                "series_name": "Cambridge Secondary Mathematics",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "manual"
        assert body["manual_override"] is True

        list_response = client.get("/api/materials", params={"search": "Learner's Book 7", "subject": "Mathematics"})
        assert list_response.status_code == 200
        rows = list_response.json()["materials"]
        assert rows[0]["book_metadata"]["original_title"] == "Cambridge Secondary Mathematics Learner's Book 7"

        series_response = client.get("/api/materials", params={"series": "Secondary Math"})
        assert series_response.status_code == 200
        series_rows = series_response.json()["materials"]
        assert len(series_rows) == 1
        assert series_rows[0]["book_metadata"]["series_name"] == "Cambridge Secondary Mathematics"
    finally:
        app.dependency_overrides.clear()


def test_metadata_sample_uses_budgeted_front_and_keyword_windows(monkeypatch):
    material = Material(
        user_id="1",
        title="Huge textbook.pdf",
        filename="Huge textbook.pdf",
        source_type="imported",
        stage_status="input",
        pipeline_status="idle",
    )
    long_text = (
        "front matter " * 400
        + "Copyright 2024 Cambridge University Press. ISBN 978-1-2345-6789-0. Second Edition. "
        + "body text " * 5000
        + "UNSAMPLED_TAIL_MARKER"
    )

    monkeypatch.setattr(
        metadata_service,
        "collect_text_sources",
        lambda _material: [{"label": "fake markdown", "text": long_text}],
    )

    sample = metadata_service.build_metadata_sample(material)

    assert sample["sampled_chars"] <= metadata_service.SAMPLE_TARGET_CHARS
    assert "Copyright 2024" in sample["text"]
    assert "UNSAMPLED_TAIL_MARKER" not in sample["text"]


def test_parse_json_content_accepts_text_wrapped_json():
    parsed = metadata_service.parse_json_content('结果如下：{"subject": "Mathematics"}')

    assert parsed == {"subject": "Mathematics"}


def test_catalog_context_prioritizes_manual_confirmed_metadata():
    _client, testing_session = make_client()
    try:
        db = testing_session()
        confirmed = Material(
            user_id="1",
            title="Grammar Friends 2 (Students Book).pdf",
            filename="Grammar Friends 2 (Students Book).pdf",
            source_type="imported",
            stage_status="input",
            pipeline_status="idle",
        )
        target = Material(
            user_id="1",
            title="Grammar Friends 3 (Students book).pdf",
            filename="Grammar Friends 3 (Students book).pdf",
            source_type="imported",
            stage_status="input",
            pipeline_status="idle",
        )
        db.add_all([confirmed, target])
        db.flush()
        db.add(
            MaterialMetadata(
                user_id="1",
                material_pk=confirmed.id,
                original_title="Grammar Friends 2",
                subject="English",
                series_name="Grammar Friends",
                language="English",
                status="manual",
                source="manual",
                confidence=1,
                manual_override=True,
            )
        )
        db.commit()

        context = metadata_service.build_catalog_context(db, "1", target)

        assert context["authority_order"][0].startswith("manual_confirmed")
        assert context["manual_confirmed_examples"][0]["authority"] == "manual_confirmed"
        assert context["manual_confirmed_examples"][0]["series_name"] == "Grammar Friends"
        assert context["catalog_values"]["subject"][0]["value"] == "English"
        assert context["catalog_values"]["subject"][0]["authority"] == "manual_confirmed"
    finally:
        app.dependency_overrides.clear()


def test_catalog_title_patterns_normalize_same_series_role_suffix():
    _client, testing_session = make_client()
    try:
        db = testing_session()
        observed_titles = [
            "Grammar Friends 2 (Students Book)",
            "Grammar Friends 3 (Students book)",
            "Grammar Friends 4 (Students Book)",
        ]
        observed_materials = []
        for title in observed_titles:
            material = Material(
                user_id="1",
                title=f"{title}.pdf",
                filename=f"{title}.pdf",
                source_type="imported",
                stage_status="input",
                pipeline_status="idle",
            )
            observed_materials.append(material)
        target = Material(
            user_id="1",
            title="Grammar Friends 1 (Tim Ward) (Z-Library).pdf",
            filename="Grammar Friends 1 (Tim Ward) (Z-Library).pdf",
            source_type="imported",
            stage_status="input",
            pipeline_status="idle",
        )
        db.add_all(observed_materials + [target])
        db.flush()
        for material, title in zip(observed_materials, observed_titles):
            db.add(
                MaterialMetadata(
                    user_id="1",
                    material_pk=material.id,
                    original_title=title,
                    subject="English Grammar",
                    series_name="Grammar Friends",
                    language="English",
                    status="ai_extracted",
                    source="ai",
                    confidence=0.55,
                    manual_override=False,
                )
            )
        db.commit()

        context = metadata_service.build_catalog_context(db, "1", target)
        result = {
            "original_title": "Grammar Friends 1",
            "series_name": "Grammar Friends",
            "evidence": [],
        }

        metadata_service.apply_context_title_patterns(result, context, target)

        assert context["similar_title_patterns"][0]["pattern"] == "Grammar Friends {level} (Students Book)"
        assert context["similar_title_patterns"][0]["count"] == 3
        assert result["original_title"] == "Grammar Friends 1 (Students Book)"
        assert result["evidence"][0]["source"] == "catalog_context"
    finally:
        app.dependency_overrides.clear()


def test_manual_confirmed_chinese_series_context_supplies_stable_fields_and_grade_title():
    _client, testing_session = make_client()
    try:
        db = testing_session()
        confirmed = Material(
            user_id="1",
            title="2026新版 三上 教材全解.pdf",
            filename="2026新版 三上 教材全解.pdf",
            source_type="imported",
            stage_status="input",
            pipeline_status="idle",
        )
        target = Material(
            user_id="1",
            title="2026新版 四上 教材全解.pdf",
            filename="2026新版 四上 教材全解.pdf",
            source_type="imported",
            stage_status="input",
            pipeline_status="idle",
        )
        unrelated = Material(
            user_id="1",
            title="AMC8_2026_Solutions.pdf",
            filename="AMC8_2026_Solutions.pdf",
            source_type="imported",
            stage_status="input",
            pipeline_status="idle",
        )
        db.add_all([confirmed, target, unrelated])
        db.flush()
        db.add(
            MaterialMetadata(
                user_id="1",
                material_pk=confirmed.id,
                original_title="新教材全解三年级数学（上）上海专用",
                publication_year=2022,
                subject="数学",
                series_name="新教材全解",
                publisher="天津人民出版社",
                grade_level="三年级上册",
                edition="第一版",
                language="中文",
                status="manual",
                source="manual",
                confidence=1,
                manual_override=True,
            )
        )
        db.add(
            MaterialMetadata(
                user_id="1",
                material_pk=unrelated.id,
                original_title="AMC8 2026 Solutions",
                subject="Mathematics",
                series_name="AMC8",
                language="English",
                status="ai_extracted",
                source="ai",
                confidence=0.5,
                manual_override=False,
            )
        )
        db.commit()

        context = metadata_service.build_catalog_context(db, "1", target)
        result = {
            "original_title": "新教材全解四年级数学（上）",
            "series_name": "新教材全解",
            "subject": "数学",
            "grade_level": "四年级上册",
            "publication_year": None,
            "publisher": "",
            "edition": "",
            "language": "中文",
            "evidence": [],
        }

        metadata_service.apply_manual_confirmed_context(result, context, target)

        assert context["manual_confirmed_examples"][0]["publisher"] == "天津人民出版社"
        assert context["manual_confirmed_examples"][0]["publication_year"] == 2022
        assert context["manual_confirmed_examples"][0]["similarity"] >= 0.25
        assert context["similar_ai_examples"] == []
        assert result["original_title"] == "新教材全解四年级数学（上）上海专用"
        assert result["publisher"] == "天津人民出版社"
        assert result["publication_year"] == 2022
        assert result["edition"] == "第一版"
        assert result["evidence"][0]["source"] == "catalog_context manual"
    finally:
        app.dependency_overrides.clear()
