from __future__ import annotations
import math, random
from collections import defaultdict
from typing import Dict, Iterable, Tuple


class Policy:
    """Emergent navigation policy via learned tag values and drive-affordances.

    - tag_weights[tag]: learned value (attraction>0 / repulsion<0)
    - nav_vector(objects, drives): continuous potential-field sum with curiosity noise
    - update(objects, reward): simple online update for all visible tags
    """

    def __init__(self) -> None:
        self.tag_weights: Dict[str, float] = defaultdict(float)
        self.lr: float = 0.05
        self.decay: float = 0.999
        self.sigma: float = 120.0  # spatial falloff (pixels)

    def nav_vector(self, objects: Iterable[dict], drives: Dict[str, float]) -> Tuple[float, float]:
        hunger = float(drives.get("hunger", 0.0) or 0.0)
        threat = float(drives.get("threat", 0.0) or 0.0)
        curiosity = float(drives.get("curiosity", 0.0) or 0.0)

        # base affordance by tag modulated by drives (no discrete triggers)
        def base_affordance(tag: str) -> float:
            t = (tag or "").lower()
            val = 0.0
            if "food" in t:
                val += 1.2 * hunger
            if "hazard" in t or "danger" in t:
                val -= 1.3 * threat
            # unknown objects feed curiosity
            if not t or t.startswith("obj"):
                val += 0.8 * curiosity
            return val

        vx, vy = 0.0, 0.0
        for o in objects:
            tag = str(o.get("tag", ""))
            w = self.tag_weights[tag] + base_affordance(tag)
            x, y = float(o.get("x", 0.0)), float(o.get("y", 0.0))
            # caller provides agent position; we'll add later as relative vector
            # here we assume caller subtracts agent position beforehand
            # For convenience, allow absolute coordinates by passing agent (0,0)
            # We treat (x,y) here as relative coordinates.
            dist = math.hypot(x, y) + 1e-6
            fall = math.exp(-dist / self.sigma)
            ux, uy = x / dist, y / dist
            vx += w * fall * ux
            vy += w * fall * uy

        # curiosity-driven exploration noise (zero-mean)
        if curiosity > 0.05:
            amp = 0.4 * curiosity
            vx += (random.random() - 0.5) * amp
            vy += (random.random() - 0.5) * amp

        return vx, vy

    def update(self, objects: Iterable[dict], reward: float) -> None:
        # decay weights slightly
        for k in list(self.tag_weights.keys()):
            self.tag_weights[k] *= self.decay
        # distribute reward to visible tags
        tags = {str(o.get("tag", "")) for o in objects}
        for tag in tags:
            self.tag_weights[tag] += self.lr * reward
            # clamp softly
            self.tag_weights[tag] = max(-2.5, min(2.5, self.tag_weights[tag]))

