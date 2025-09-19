from __future__ import annotations
from typing import Dict, Iterable, List
from models.types import BiasReport, ModelResponse


class BiasDetector:
    """Performs heuristic bias analysis over model responses."""

    def evaluate(self, responses: Iterable[ModelResponse]) -> BiasReport:
        model_biases: Dict[str, List[str]] = {}
        for resp in responses:
            flags: List[str] = []
            text_lower = resp.text.lower()
            if any(keyword in text_lower for keyword in ["always", "never", "must"]):
                flags.append("overgeneralization")
            if "should" in text_lower and "perhaps" not in text_lower:
                flags.append("normative_bias")
            if len(resp.text) < 40:
                flags.append("insufficient_deliberation")
            if flags:
                model_biases.setdefault(resp.model, []).extend(flags)
        notes = "Balanced perspectives detected." if not model_biases else "Bias indicators flagged; review recommended."
        return BiasReport(model_biases=model_biases, overall_notes=notes)
