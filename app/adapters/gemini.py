from __future__ import annotations
import asyncio
from typing import Any, Dict

from .base import BaseAdapter


class GeminiAdapter(BaseAdapter):
    name = "gemini"

    async def _call_model(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "text": f"Gemini multimodal insight: {prompt[:80]}",
            "reasoning": "Balances creative exploration with factual grounding.",
            "confidence": 0.6,
        }
