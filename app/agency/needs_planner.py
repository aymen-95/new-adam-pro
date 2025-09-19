from __future__ import annotations
from typing import Dict, Any


class NeedsPlanner:
    """Utility-based prioritization of actions from drives.

    Returns action suggestions with priority scores.
    """

    def score(self, drives: Dict[str, float], affordances: Dict[str, Any]) -> Dict[str, float]:
        hunger = drives.get("hunger", 0.0)
        fatigue = drives.get("fatigue", 0.0)
        curiosity = drives.get("curiosity", 0.0)
        threat = drives.get("threat", 0.0)

        scores: Dict[str, float] = {}
        # Safety dominates
        scores["seek_safety"] = max(threat * 0.9, 0.0)
        # Eating only if food exists; suppressed by high threat
        base_eat = hunger * (1.0 if affordances.get("food_available") else 0.2)
        suppression = max(0.0, 1.0 - 0.8 * threat)
        scores["eat"] = base_eat * suppression
        # Rest depends on fatigue and safety
        scores["rest"] = max(fatigue * (0.6 if threat < 0.3 else 0.2), 0.0)
        # Explore if curious and safe
        scores["explore"] = max(curiosity * (0.7 if threat < 0.2 else 0.1), 0.0)
        # Work/think is default
        scores["think"] = max(0.2 * (1.0 - threat), 0.05)
        return scores

    def decide(self, drives: Dict[str, float], affordances: Dict[str, Any]) -> tuple[str, float, str, Dict[str, Any]]:
        scores = self.score(drives, affordances)
        action = max(scores, key=scores.get)
        reason = self._reason_for(action, drives, affordances)
        return action, scores[action], reason, {}

    @staticmethod
    def _reason_for(action: str, drives: Dict[str, float], affordances: Dict[str, Any]) -> str:
        if action == "seek_safety":
            return "Threat high; prioritizing safety."
        if action == "eat":
            return "Hunger elevated with food available."
        if action == "rest":
            return "Fatigue high; recovering energy."
        if action == "explore":
            return "Curiosity driving information-seeking."
        return "Maintaining cognitive activity while monitoring environment."
