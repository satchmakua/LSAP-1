from fastapi.testclient import TestClient

from lsap.api import app as app_module
from lsap.api.app import app
from lsap.engine.compiler import Dials, compile_constraints
from lsap.engine.runtime import EngineError, GenerationRun, Paragraph, WorldState

client = TestClient(app)

DIALS = {"c1": 0.9, "c2": 0.4, "c3": 0.6, "c4": 0.9, "c5": 0.4}


def _fake_run(**kwargs) -> GenerationRun:
    d = kwargs.get("dials") or Dials(**DIALS)
    return GenerationRun(
        dials=d,
        spec=compile_constraints(d),
        situation=kwargs.get("situation", "s"),
        world=WorldState(facts=["A door is closed."], objects=["the glass"]),
        paragraphs=[
            Paragraph(
                index=0, phase="establishment", language_register="elevated literary",
                emotional_energy=0.5, text="The room was cold.", objects_seen=["the glass"],
                memory_note=None,
            )
        ],
    )


def test_presets_endpoint_lists_dial_configs():
    body = client.get("/api/presets").json()
    assert len(body) >= 4
    ids = {p["id"] for p in body}
    assert {"minimal", "baroque", "trap"} <= ids
    assert set(body[0]["dials"]) >= {"c1", "c2", "c3", "c4", "c5"}


def test_generate_endpoint_returns_the_run(monkeypatch):
    monkeypatch.setattr(app_module.engine_runtime, "generate", _fake_run)
    r = client.post(
        "/api/generate", json={"dials": DIALS, "situation": "A man returns.", "paragraphs": 1}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["situation"] == "A man returns."
    assert len(body["paragraphs"]) == 1
    assert body["paragraphs"][0]["phase"] == "establishment"
    # the compiled spec travels with the run so the console can show what was enforced
    assert body["spec"]["bands"]["c1"] == "extreme"
    assert any("Metaphor" in r for r in body["spec"]["rules"]["c1"])


def test_generate_endpoint_rejects_bad_paragraph_counts():
    for n in (0, 9):
        r = client.post(
            "/api/generate", json={"dials": DIALS, "situation": "x", "paragraphs": n}
        )
        assert r.status_code == 400


def test_generate_endpoint_maps_engine_error_to_400(monkeypatch):
    def boom(**kwargs):
        raise EngineError("ANTHROPIC_API_KEY is not set. Add it to backend/.env.")

    monkeypatch.setattr(app_module.engine_runtime, "generate", boom)
    r = client.post("/api/generate", json={"dials": DIALS, "situation": "x", "paragraphs": 2})
    assert r.status_code == 400
    assert "ANTHROPIC_API_KEY" in r.json()["detail"]
