from __future__ import annotations
from typing import Iterable, List

from models.types import BiasReport, DialecticSummary, ModelResponse, ResponsePacket, ConflictReport


class ResponseSynthesizer:
    """Produces the final response blending supportive/opposing insights."""

    def synthesize(
        self,
        prompt: str,
        intent: str,
        responses: Iterable[ModelResponse],
        dialectic: DialecticSummary,
        bias: BiasReport,
        conflict: ConflictReport,
        context: dict | None = None,
    ) -> ResponsePacket:
        supporting_points: List[str] = []
        opposing_points: List[str] = []
        for resp in responses:
            if "not" in resp.text.lower() or "however" in resp.text.lower():
                opposing_points.append(f"{resp.model}: {resp.text}")
            else:
                supporting_points.append(f"{resp.model}: {resp.text}")
        # adjust intent based on context (drives/mood/heart/weights)
        if context:
            weights = context.get("weights") or {}
            mood = context.get("mood") or {}
            heart = context.get("heart") or {}
            top = max(weights, key=weights.get) if weights else None
            if top == "seek_safety":
                intent = "safety_first"
            elif top == "eat" and (weights.get("eat", 0) > 0.5) and (weights.get("seek_safety", 0) < 0.4):
                intent = "prioritize_nutrition"
            elif top == "explore" and weights.get("explore", 0) > 0.5:
                intent = "explore_environment"

        text = self._compose_text(prompt, dialectic, conflict, context)
        action = "speak"
        return ResponsePacket(
            action=action,
            text=text,
            intent=intent,
            supporting_points=supporting_points,
            opposing_points=opposing_points,
            bias_report=bias,
            dialectic_summary=dialectic,
            conflict_report=conflict,
            meta={
                "prompt": prompt,
                "models": [resp.model for resp in responses],
                "context": context or {},
            },
        )

    @staticmethod
    def _compose_text(prompt: str, dialectic: DialecticSummary, conflict: ConflictReport, context: dict | None = None) -> str:
        parts = [f"Prompt: {prompt}"]
        if dialectic.narrative:
            parts.append(dialectic.narrative)
        if conflict.description:
            parts.append(conflict.description)
        if context:
            weights = context.get("weights") or {}
            mood = context.get("mood") or {}
            heart = context.get("heart") or {}
            if weights:
                top = sorted(weights.items(), key=lambda kv: -kv[1])[:2]
                parts.append("Top weights: " + ", ".join(f"{k}={v:.2f}" for k, v in top))
            if mood:
                parts.append(f"Mood: {mood.get('label','-')} v={mood.get('valence',0):.2f} a={mood.get('arousal',0):.2f}")
            if heart:
                parts.append(f"Physio: {heart.get('bpm','?')} bpm, hrv={heart.get('hrv','?')}")
        return " " .join(parts)
