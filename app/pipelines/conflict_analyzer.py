from __future__ import annotations
from typing import Iterable, List

from models.types import ConflictReport, ModelResponse


class ConflictAnalyzer:
    """Classifies cognitive conflicts emerging from multi-model responses."""

    def analyze(self, responses: Iterable[ModelResponse]) -> ConflictReport:
        categories = {"methodological": [], "ethical": [], "semantic": []}
        texts = list(responses)
        for resp in texts:
            lower = resp.text.lower()
            if any(token in lower for token in ["method", "approach", "process"]):
                categories["methodological"].append(resp.model)
            if any(token in lower for token in ["ethic", "moral", "duty"]):
                categories["ethical"].append(resp.model)
            if any(token in lower for token in ["definition", "term", "meaning"]):
                categories["semantic"].append(resp.model)
        non_empty = {k: v for k, v in categories.items() if v}
        severity = min(len(non_empty) * 0.35, 1.0)
        description = "Conflicts span multiple dimensions." if non_empty else "Minor divergence detected."
        return ConflictReport(categories=non_empty, severity=severity, description=description)
