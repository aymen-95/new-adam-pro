from __future__ import annotations
import asyncio

from models.types import InputEvent
from app.memory import MemoryStore
from app.orchestrator import Orchestrator


def test_orchestrator_basic(tmp_path):
    memory_path = tmp_path / "memory.json"
    memory_path.write_text("[]", encoding="utf-8")
    memory = MemoryStore(str(memory_path))
    orchestrator = Orchestrator(memory=memory)

    event = InputEvent(type="text", value="Can AI be conscious?", source="user")
    packet = asyncio.run(orchestrator.handle(event))

    assert packet.intent in {"inform", "mediate_contradiction", "highlight_conflict", "report_sound"}
    assert packet.dialectic_summary is not None
    assert packet.bias_report is not None
    assert packet.supporting_points or packet.opposing_points
