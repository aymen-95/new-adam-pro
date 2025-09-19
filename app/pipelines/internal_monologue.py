from __future__ import annotations
import itertools
from typing import List

from models.types import ModelResponse


class InternalMonologue:
    """Creates self-generated reflections to deepen reasoning."""

    def __init__(self, depth: int = 2):
        self.depth = depth

    def reflect(self, prompt: str, base_responses: List[ModelResponse]) -> List[ModelResponse]:
        reflections: List[ModelResponse] = []
        for level in range(self.depth):
            for resp in base_responses:
                counter_text = self._counter_argument(resp, level)
                reflections.append(
                    ModelResponse(
                        model=f"internal_{resp.model}_{level}",
                        text=counter_text,
                        reasoning="Self-generated monologic challenge",
                        confidence=max(resp.confidence - 0.05 * (level + 1), 0.3),
                    )
                )
        return reflections

    @staticmethod
    def _counter_argument(resp: ModelResponse, level: int) -> str:
        prefixes = ["What if", "Consider", "Suppose", "Is it possible"]
        prefix = prefixes[level % len(prefixes)]
        return f"{prefix} the opposite holds? Re-evaluate: {resp.text[:80]}"
