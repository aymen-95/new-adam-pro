from __future__ import annotations
import asyncio
from typing import Any, Dict

from .base import BaseAdapter


class CopilotAdapter(BaseAdapter):
    name = "copilot"

    async def _call_model(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.04)
        return {
            "text": f"Copilot pragmatic answer: {prompt[:80]}",
            "reasoning": "Targets actionable steps and developer pragmatics.",
            "confidence": 0.55,
        }
