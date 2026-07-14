from fastapi.testclient import TestClient

from main import app


def test_system_health_does_not_require_gpu():
    client = TestClient(app)

    response = client.get("/api/system/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "ok", "gpu_required": False}


def test_mineru_health_endpoint(monkeypatch):
    class FakeClient:
        def health(self):
            return {
                "available": True,
                "base_url": "http://mineru-router:8002",
                "status": "healthy",
            }

    monkeypatch.setattr("app.api.health.MineruApiClient", lambda: FakeClient())

    client = TestClient(app)
    response = client.get("/api/system/mineru-health")

    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["base_url"] == "http://mineru-router:8002"
