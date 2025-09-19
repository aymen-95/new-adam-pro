from __future__ import annotations
from typing import Dict, Any

from models.types import AgencyState, ActionPlan
from app.physio.heart import Heart
from .drives import DrivesModel
from .needs_planner import NeedsPlanner


class Agency:
    """High-level agent managing drives and decisions."""

    def __init__(self) -> None:
        self.state = AgencyState()
        self.drives = DrivesModel()
        self.planner = NeedsPlanner()
        self.heart = Heart()

    def sense(self, signals: Dict[str, Any]) -> None:
        # direct updates
        if (th := signals.get("threat")) is not None:
            self.drives.threat = max(self.drives.threat, float(th))
        if signals.get("stimulation"):
            self.drives.curiosity = min(1.0, self.drives.curiosity + 0.05)

    def step(self, minutes: float, signals: Dict[str, Any]) -> None:
        self.drives.update(minutes, signals)
        # sync into AgencyState
        self.state.drives.hunger = self.drives.hunger
        self.state.drives.fatigue = self.drives.fatigue
        self.state.drives.curiosity = self.drives.curiosity
        self.state.drives.threat = self.drives.threat
        # homeostasis
        self.state.satiety = max(0.0, min(1.0, 1.0 - self.drives.hunger))
        self.state.energy = max(0.0, min(1.0, 1.0 - self.drives.fatigue))
        # derive affective summary
        self._update_mood_and_appetite()
        # heart responds to arousal/activity
        activity = float(signals.get("activity", 0.0) or 0.0)
        self.heart.update(minutes * 60.0, arousal=self.state.mood.arousal, activity=activity, rest=bool(signals.get("rest", False)))

    def decide(self, affordances: Dict[str, Any]) -> ActionPlan:
        weights = self.planner.score(self.drives.as_dict(), affordances)
        self.state.weights = weights
        action, priority, reason, params = self.planner.decide(self.drives.as_dict(), affordances)
        # generate thoughts
        self.state.last_thoughts = self._generate_thoughts(action, priority, reason)
        return ActionPlan(action=action, priority=priority, reason=reason, parameters=params)

    def enact(self, plan: ActionPlan) -> None:
        if plan.action == "eat":
            self.drives.apply_eat()
        elif plan.action == "rest":
            self.drives.apply_rest()
        elif plan.action == "explore":
            self.drives.apply_explore()
        elif plan.action == "seek_safety":
            self.drives.apply_seek_safety()
        # sync derived values
        self.step(0.0, {})

    # Perception API
    def observe_vision(self, objects: list[dict]) -> None:
        """Lightweight vision hook: boosts curiosity and records thoughts."""
        if not isinstance(objects, list):
            return
        n = len(objects)
        # small curiosity boost per vision event
        self.drives.curiosity = min(1.0, self.drives.curiosity + 0.02 * n)
        self.state.context["vision_last_count"] = n
        # keep a short thought about what was seen
        labels = [str(o.get("tag", o.get("id", "?"))) for o in objects[:5]]
        self.state.last_thoughts = [f"Vision: {n} object(s) in view -> {', '.join(labels)}"] + self.state.last_thoughts[:4]

    # --- internals ---
    def _update_mood_and_appetite(self) -> None:
        # appetite tracks hunger but is suppressed by high threat
        appetite = max(0.0, self.drives.hunger * (1.0 - 0.5 * self.drives.threat))
        # simple valence/arousal model
        valence = (self.state.satiety - self.drives.threat) + 0.2 * (self.drives.curiosity - self.drives.fatigue)
        valence = max(-1.0, min(1.0, valence))
        arousal = max(0.0, min(1.0, 0.5 * self.drives.threat + 0.4 * self.drives.curiosity + 0.1))
        label = self._label_from(valence, arousal)
        self.state.appetite = appetite
        self.state.mood.label = label
        self.state.mood.valence = valence
        self.state.mood.arousal = arousal

    @staticmethod
    def _label_from(valence: float, arousal: float) -> str:
        if arousal > 0.7 and valence < -0.2:
            return "anxious"
        if arousal > 0.6 and valence > 0.3:
            return "excited"
        if valence < -0.3 and arousal < 0.5:
            return "sad"
        if valence > 0.4 and arousal < 0.5:
            return "calm"
        if arousal > 0.6 and abs(valence) < 0.2:
            return "alert"
        if self_like := valence > 0.1 and arousal > 0.4:
            return "curious"
        return "neutral"

    def _generate_thoughts(self, action: str, priority: float, reason: str) -> list[str]:
        d = self.drives.as_dict()
        thoughts = [
            f"Assessing drives: hunger={d['hunger']:.2f}, fatigue={d['fatigue']:.2f}, curiosity={d['curiosity']:.2f}, threat={d['threat']:.2f}",
            f"Mood: {self.state.mood.label} (valence={self.state.mood.valence:.2f}, arousal={self.state.mood.arousal:.2f})",
            f"Appetite score: {self.state.appetite:.2f}",
            f"Heart: {self.heart.state.bpm:.1f} bpm (hrv={self.heart.state.hrv:.2f})",
            f"Action weights: " + ", ".join(f"{k}={v:.2f}" for k, v in sorted(self.state.weights.items(), key=lambda kv: -kv[1])),
            f"Chosen: {action} (priority={priority:.2f}) because {reason}",
        ]
        return thoughts

    # Public helper for computing weights without committing a decision
    def eval_weights(self, affordances: Dict[str, Any]) -> Dict[str, float]:
        w = self.planner.score(self.drives.as_dict(), affordances)
        self.state.weights = w
        return w
