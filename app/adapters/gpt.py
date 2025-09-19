from __future__ import annotations
import asyncio
from typing import Any, Dict

from .base import BaseAdapter


class GPTAdapter(BaseAdapter):
    name = "gpt"

    async def _call_model(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "text": f"GPT reflection on: {prompt[:80]}",
            "reasoning": "Emphasizes probabilistic reasoning and human-aligned values.",
            "confidence": 0.7,
        }
