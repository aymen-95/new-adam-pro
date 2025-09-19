from __future__ import annotations
import asyncio
from typing import Any, Dict

from .base import BaseAdapter


class DeepSeekAdapter(BaseAdapter):
    name = "deepseek"

    async def _call_model(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.06)
        return {
            "text": f"DeepSeek analytical view: {prompt[:80]}",
            "reasoning": "Focuses on deep analysis and alternative trajectories.",
            "confidence": 0.65,
        }
