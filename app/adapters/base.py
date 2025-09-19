from __future__ import annotations
import asyncio
from typing import Any, Dict
from abc import ABC, abstractmethod


class AdapterError(RuntimeError):
    """Raised when an adapter fails to communicate with its underlying model."""


class BaseAdapter(ABC):
    name: str

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    async def ask(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await asyncio.wait_for(self._call_model(prompt, context), timeout=self.timeout)
        except asyncio.TimeoutError as exc:  # pragma: no cover - network edge case
            raise AdapterError(f"Adapter {self.name} timed out") from exc

    @abstractmethod
    async def _call_model(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        ...
