from __future__ import annotations
import asyncio
import logging
from typing import Optional

from models.types import InputEvent, ResponsePacket

from .config import get_settings
from .memory import MemoryStore
from .orchestrator import Orchestrator

logger = logging.getLogger("smartcore.core")


class SmartCore:
    """High-level interface for processing events via orchestrator."""

    def __init__(self, memory_path: Optional[str] = None):
        settings = get_settings()
        path = memory_path or settings.memory_path
        self.memory = MemoryStore(path)
        self.orchestrator = Orchestrator(memory=self.memory)
        self._think_task: Optional[asyncio.Task] = None
        self.settings = settings

    async def process_event(self, event: InputEvent, context: Optional[dict] = None) -> ResponsePacket:
        logger.info("processing", extra={"event": event.model_dump()})
        packet = await self.orchestrator.handle(event, context=context)
        return packet

    def start(self) -> None:
        if self.settings.enable_think_loop:
            loop = asyncio.get_event_loop()
            if not self._think_task:
                self._think_task = loop.create_task(self._think_loop())

    async def _think_loop(self) -> None:
        interval = max(self.settings.think_interval_seconds, 2.0)
        while True:
            await asyncio.sleep(interval)
            synthetic = InputEvent(type="system", value="self-query", source="core")
            await self.process_event(synthetic)

    def shutdown(self) -> None:
        if self._think_task and not self._think_task.done():
            self._think_task.cancel()
