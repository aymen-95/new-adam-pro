from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import math


@dataclass
class BodyState:
    # 2D world state (top-down)
    x: float = 250.0
    y: float = 180.0
    yaw: float = 0.0  # radians, 0 -> facing right
    head_yaw: float = 0.0  # relative to body yaw
    left_hand: float = 0.0  # 0 down .. 1 up
    right_hand: float = 0.0
    speed: float = 60.0  # px per second


class Body:
    """Minimal 2D kinematics for a virtual body."""

    def __init__(self, width: int = 500, height: int = 360) -> None:
        self.state = BodyState()
        self.room_w = width
        self.room_h = height
        self._activity: float = 0.0  # 0..1 estimate of recent movement

    def to_dict(self) -> Dict[str, Any]:
        s = self.state
        return {
            "x": s.x,
            "y": s.y,
            "yaw": s.yaw,
            "head_yaw": s.head_yaw,
            "left_hand": s.left_hand,
            "right_hand": s.right_hand,
            "room": {"w": self.room_w, "h": self.room_h},
        }

    def reset(self) -> None:
        self.state = BodyState()

    def turn(self, delta: float) -> None:
        self.state.yaw = (self.state.yaw + delta) % (2 * math.pi)

    def look(self, delta: float) -> None:
        self.state.head_yaw = max(-math.pi/2, min(math.pi/2, self.state.head_yaw + delta))

    def move(self, forward: float, sideways: float = 0.0, dt: float = 0.2) -> None:
        # forward/sideways in [-1,1]; dt seconds
        s = self.state
        speed = s.speed * dt
        dx = (math.cos(s.yaw) * forward - math.sin(s.yaw) * sideways) * speed
        dy = (math.sin(s.yaw) * forward + math.cos(s.yaw) * sideways) * speed
        new_x = max(10, min(self.room_w - 10, s.x + dx))
        new_y = max(10, min(self.room_h - 10, s.y + dy))
        dist = math.hypot(new_x - s.x, new_y - s.y)
        s.x, s.y = new_x, new_y
        # instant normalized speed relative to max speed
        inst = 0.0 if dt <= 0 else min(1.0, (dist / dt) / max(1e-3, s.speed))
        # EMA for activity
        self._activity = max(inst, self._activity * 0.7 + inst * 0.3)

    def pose(self, left: float | None = None, right: float | None = None) -> None:
        if left is not None:
            self.state.left_hand = max(0.0, min(1.0, float(left)))
        if right is not None:
            self.state.right_hand = max(0.0, min(1.0, float(right)))

    def tick(self, dt: float) -> None:
        # natural decay of activity in absence of movement
        decay = math.exp(-0.8 * max(0.0, dt))
        self._activity *= decay

    def activity(self) -> float:
        return max(0.0, min(1.0, self._activity))
