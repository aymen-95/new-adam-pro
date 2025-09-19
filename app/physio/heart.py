from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class HeartState:
    bpm: float = 70.0
    hrv: float = 0.5  # 0..1 (higher is calmer/more variability)
    baseline: float = 70.0
    min_bpm: float = 50.0
    max_bpm: float = 160.0
    _phase_s: float = 0.0  # time accumulator for beat timing
    beat: bool = False


class Heart:
    """Simple physiological heart model.

    - bpm increases with arousal and activity; decreases with rest/calm.
    - hrv decreases under stress; increases at rest.
    - update(dt) advances time and toggles `beat` when crossing the next cycle.
    """

    def __init__(self) -> None:
        self.state = HeartState()

    def update(self, dt_seconds: float, *, arousal: float = 0.0, activity: float = 0.0, rest: bool = False) -> None:
        s = self.state
        arousal = max(0.0, min(1.0, float(arousal)))
        activity = max(0.0, min(1.0, float(activity)))
        # Target bpm responds to arousal/activity
        target = s.baseline + arousal * 40.0 + activity * 60.0 - (20.0 if rest else 0.0)
        target = max(s.min_bpm, min(s.max_bpm, target))
        # Smooth approach (first-order lag)
        k = 2.0  # responsiveness
        alpha = 1.0 - math.exp(-k * max(0.0, dt_seconds))
        s.bpm = s.bpm + (target - s.bpm) * alpha
        # HRV: lower under stress, higher at rest
        stress = max(arousal, activity)
        s.hrv = max(0.05, min(1.0, 0.8 - 0.6 * stress + (0.2 if rest else 0.0)))

        # Beat timing
        period = 60.0 / max(1.0, s.bpm)
        s._phase_s += dt_seconds
        s.beat = False
        while s._phase_s >= period:
            s._phase_s -= period
            s.beat = True  # at least one beat occurred in this update window

    def to_dict(self) -> Dict[str, Any]:
        s = self.state
        return {"bpm": round(s.bpm, 1), "hrv": round(s.hrv, 3), "beat": s.beat}

