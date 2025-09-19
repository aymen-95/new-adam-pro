from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


SensoryType = Literal["audio", "visual", "text", "system", "environment", "touch"]
ActionType = Literal["speak", "move", "signal", "think", "analyze", "idle"]
ModelName = Literal["gpt", "deepseek", "gemini", "copilot"]


class InputEvent(BaseModel):
    type: SensoryType
    value: str
    source: str
    timestamp: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    metadata: Dict[str, Any] | None = None


class ModelResponse(BaseModel):
    model: str
    text: str
    reasoning: Optional[str] = None
    confidence: float = 0.5
    bias_flags: List[str] = Field(default_factory=list)


class DialecticSummary(BaseModel):
    agreements: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    argument_map: Dict[str, Any] = Field(default_factory=dict)
    narrative: str = ""


class ConflictReport(BaseModel):
    categories: Dict[str, List[str]] = Field(default_factory=dict)
    severity: float = 0.0
    description: str = ""


class BiasReport(BaseModel):
    model_biases: Dict[str, List[str]] = Field(default_factory=dict)
    overall_notes: str = ""

    model_config = {"protected_namespaces": ()}


class ResponsePacket(BaseModel):
    action: ActionType
    text: str
    intent: str
    supporting_points: List[str] = Field(default_factory=list)
    opposing_points: List[str] = Field(default_factory=list)
    bias_report: BiasReport | None = None
    dialectic_summary: DialecticSummary | None = None
    conflict_report: ConflictReport | None = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    id: str
    timestamp: datetime
    tags: List[str]
    payload: Dict[str, Any]


# ---- Agency / Drives ----

class Drives(BaseModel):
    hunger: float = 0.2
    fatigue: float = 0.2
    curiosity: float = 0.5
    threat: float = 0.0

    def clipped(self) -> "Drives":
        return Drives(
            hunger=max(0.0, min(self.hunger, 1.0)),
            fatigue=max(0.0, min(self.fatigue, 1.0)),
            curiosity=max(0.0, min(self.curiosity, 1.0)),
            threat=max(0.0, min(self.threat, 1.0)),
        )


class AgencyState(BaseModel):
    energy: float = 0.7
    satiety: float = 0.6
    drives: Drives = Field(default_factory=Drives)
    context: Dict[str, Any] = Field(default_factory=dict)
    # Derived affective/cognitive summaries
    class MoodState(BaseModel):
        label: str = "neutral"
        valence: float = 0.0  # [-1,1]
        arousal: float = 0.0  # [0,1]

    mood: MoodState = Field(default_factory=MoodState)
    appetite: float = 0.0
    weights: Dict[str, float] = Field(default_factory=dict)
    last_thoughts: List[str] = Field(default_factory=list)


class ActionPlan(BaseModel):
    action: str
    reason: str
    priority: float
    parameters: Dict[str, Any] = Field(default_factory=dict)
