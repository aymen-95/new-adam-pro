from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DriveGains:
    hunger_gain_per_min: float = 0.02
    fatigue_gain_per_min: float = 0.015
    curiosity_decay_per_min: float = 0.01
    threat_decay_per_min: float = 0.03


class DrivesModel:
    """Homeostatic drives with simple differential update.

    Values are in [0,1]. update() advances time and applies external signals.
    """

    def __init__(self) -> None:
        self.hunger = 0.2
        self.fatigue = 0.2
        self.curiosity = 0.5
        self.threat = 0.0
        self.gains = DriveGains()

    def as_dict(self) -> Dict[str, float]:
        return {
            "hunger": self.hunger,
            "fatigue": self.fatigue,
            "curiosity": self.curiosity,
            "threat": self.threat,
        }

    def clamp(self) -> None:
        for k in ["hunger", "fatigue", "curiosity", "threat"]:
            v = getattr(self, k)
            setattr(self, k, max(0.0, min(1.0, v)))

    def update(self, minutes: float, signals: Dict[str, Any] | None = None) -> None:
        signals = signals or {}
        self.hunger += self.gains.hunger_gain_per_min * minutes
        self.fatigue += self.gains.fatigue_gain_per_min * minutes
        self.curiosity -= self.gains.curiosity_decay_per_min * minutes
        self.threat -= self.gains.threat_decay_per_min * minutes

        # External signals influence
        if signals.get("stimulation"):
            self.curiosity = min(1.0, self.curiosity + 0.1)
        if (th := signals.get("threat")) is not None:
            self.threat = max(self.threat, float(th))
        if signals.get("rest"):
            self.fatigue = max(0.0, self.fatigue - 0.2)

        self.clamp()

    # Action effects
    def apply_eat(self) -> None:
        self.hunger = max(0.0, self.hunger - 0.5)
        self.curiosity = min(1.0, self.curiosity + 0.05)

    def apply_rest(self) -> None:
        self.fatigue = max(0.0, self.fatigue - 0.5)
        self.threat = max(0.0, self.threat - 0.1)

    def apply_explore(self) -> None:
        self.curiosity = min(1.0, self.curiosity + 0.2)
        self.fatigue = min(1.0, self.fatigue + 0.05)

    def apply_seek_safety(self) -> None:
        self.threat = max(0.0, self.threat - 0.5)
