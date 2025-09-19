from __future__ import annotations
import os
from importlib import reload

from fastapi.testclient import TestClient


def test_api_pipeline(monkeypatch, tmp_path):
    memory_path = tmp_path / "memory.json"
    memory_path.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("MEMORY_PATH", str(memory_path))
    monkeypatch.setenv("ENABLE_THINK_LOOP", "false")

    from app import config, main

    reload(config)
    reload(main)

    client = TestClient(main.app)
    payload = {"type": "text", "value": "Should AI replace human judges?", "source": "user"}
    resp = client.post("/orchestrate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in {"inform", "mediate_contradiction", "highlight_conflict"}
    assert "bias_report" in data

    memory_resp = client.get("/memory")
    assert memory_resp.status_code == 200
    assert isinstance(memory_resp.json(), list)
