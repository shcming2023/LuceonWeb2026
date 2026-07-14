from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models.base import Base
from main import app


@pytest.fixture()
def client():
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
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_register_sets_session_cookie_and_me_returns_user(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    response = client.post(
        "/api/auth/register",
        json={"email": "Ada@Example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert client.cookies.get("mineru_session")
    assert response.json()["user"]["email"] == "ada@example.com"

    me_response = client.get("/api/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ada@example.com"


def test_register_rejects_duplicate_email(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "secret123"},
    )

    response = client.post(
        "/api/auth/register",
        json={"email": "ADA@example.com", "password": "secret123"},
    )

    assert response.status_code == 409


def test_login_sets_session_for_existing_user(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "secret123"},
    )
    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert client.cookies.get("mineru_session")
    assert response.json()["user"]["email"] == "ada@example.com"


def test_admin_alias_maps_to_dev_admin_email(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    register_response = client.post(
        "/api/auth/register",
        json={"email": "admin", "password": "123456"},
    )
    assert register_response.status_code == 200
    assert register_response.json()["user"]["email"] == "admin@luceon.local"
    client.post("/api/auth/logout")

    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin", "password": "123456"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == "admin@luceon.local"


def test_login_rejects_wrong_password(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "secret123"},
    )
    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "wrongpass"},
    )

    assert response.status_code == 401


def test_authenticated_cookie_can_access_files(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "secret123"},
    )

    response = client.get("/api/files")

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_auth_required_for_current_user_and_files_when_legacy_auth_enabled(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")

    me_response = client.get("/api/auth/me")
    files_response = client.get("/api/files")

    assert me_response.status_code == 401
    assert files_response.status_code == 401


def test_public_workspace_available_without_session(client):
    me_response = client.get("/api/auth/me")
    files_response = client.get("/api/files")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "workspace@luceon.local"
    assert me_response.json()["capabilities"]["pipeline_admin"] is False
    assert files_response.status_code == 200
    assert files_response.json()["total"] == 0


def test_pipeline_admin_capability_uses_authenticated_email_allowlist(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")
    monkeypatch.setenv("LUCEON_PIPELINE_ADMIN_EMAILS", "ops@example.com")

    response = client.post(
        "/api/auth/register",
        json={"email": "ops@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["capabilities"]["pipeline_admin"] is True
    assert client.get("/api/auth/me").json()["capabilities"]["pipeline_admin"] is True


def test_popo_recovery_is_forbidden_for_normal_authenticated_user(client, monkeypatch):
    monkeypatch.setenv("LUCEON_AUTH_DISABLED", "false")
    monkeypatch.setenv("LUCEON_PIPELINE_ADMIN_EMAILS", "ops@example.com")
    client.post(
        "/api/auth/register",
        json={"email": "reader@example.com", "password": "secret123"},
    )

    preflight = client.post("/api/materials/1/pipeline/resume-popo/preflight")
    start = client.post("/api/materials/1/pipeline/resume-popo/start")

    assert preflight.status_code == 403
    assert start.status_code == 403
