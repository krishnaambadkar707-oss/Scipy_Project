from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_dashboard_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "PulseView" in response.text


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_swagger_docs_are_available():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text


def test_analysis_returns_browser_data():
    response = client.post("/analyze", json={"heart_rate": 72, "noise_level": 0.2, "seed": 42})
    body = response.json()
    assert response.status_code == 200
    assert body["analysis"]["bpm"] > 0
    assert len(body["analysis"]["signal_preview"]) > 0
    assert abs(body["analysis"]["bpm"] - 72) < 3


def test_invalid_analysis_is_rejected():
    response = client.post("/analyze", json={"heart_rate": 500})
    assert response.status_code == 422


def test_cors_allows_the_configured_local_origin():
    response = client.options(
        "/analyze",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8000"


def test_short_duration_analysis():
    response = client.post("/analyze", json={"sampling_rate": 50, "duration": 0.3, "heart_rate": 72})
    assert response.status_code == 200
    assert "bpm" in response.json()["analysis"]


def test_get_analysis_with_query_params():
    response = client.get("/analyze?heart_rate=90&noise_level=0.1&seed=42")
    assert response.status_code == 200
    body = response.json()
    assert body["parameters"]["heart_rate"] == 90




