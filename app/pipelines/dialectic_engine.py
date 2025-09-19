from __future__ import annotations
from typing import Iterable, List
from models.types import DialecticSummary, ModelResponse


class DialecticEngine:
    """Analyze agreements and contradictions across model responses."""

    def analyze(self, responses: Iterable[ModelResponse]) -> DialecticSummary:
        agreements: List[str] = []
        contradictions: List[str] = []
        argument_map = {}

        texts = list(responses)
        for i, base in enumerate(texts):
            argument_map.setdefault(base.model, {"claims": [], "contradicts": []})
            argument_map[base.model]["claims"].append(base.text)
            for other in texts[i + 1 :]:
                if base.text[:40] == other.text[:40]:
                    agreements.append(f"{base.model} aligns with {other.model} on opening perspective.")
                elif base.model != other.model:
                    contradictions.append(
                        f"{base.model} diverges from {other.model}: '{base.text[:30]}...' vs '{other.text[:30]}...'"
                    )
                    argument_map[base.model]["contradicts"].append(other.model)
        narrative = self._build_narrative(agreements, contradictions)
        return DialecticSummary(agreements=agreements, contradictions=contradictions, argument_map=argument_map, narrative=narrative)

    @staticmethod
    def _build_narrative(agreements: List[str], contradictions: List[str]) -> str:
        parts = []
        if agreements:
            parts.append(f"Convergence detected on {len(agreements)} key points.")
        if contradictions:
            parts.append(f"Identified {len(contradictions)} active contradictions requiring synthesis.")
        return " ".join(parts) if parts else "Minimal dialectic tension observed."
