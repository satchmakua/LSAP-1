from fastapi.testclient import TestClient

from lsap.api.app import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["axes_loaded"] == 30


def test_axes_endpoint_serves_all_six_fields():
    r = client.get("/api/axes")
    assert r.status_code == 200
    axes = r.json()
    assert len(axes) == 30
    assert {a["field"] for a in axes} == {"L", "N", "C", "P", "A", "S"}
