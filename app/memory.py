from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from models.types import InputEvent, MemoryEntry, ModelResponse


class MemoryStore:
    """Persistent memory implemented as JSON document."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def load(self) -> List[MemoryEntry]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [MemoryEntry(**entry) for entry in raw]

    def save(self, entries: Iterable[MemoryEntry]) -> None:
        serializable = [entry.model_dump(mode="json") for entry in entries]
        self.path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")

    def append_observation(self, event: InputEvent, responses: List[ModelResponse]) -> MemoryEntry:
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            tags=[event.type, event.source],
            payload={
                "event": event.model_dump(),
                "responses": [resp.model_dump() for resp in responses],
            },
        )
        entries = self.load()
        entries.append(entry)
        self.save(entries)
        return entry

    def query_by_tag(self, tag: str, limit: int = 5) -> List[MemoryEntry]:
        return [entry for entry in self.load() if tag in entry.tags][-limit:]
