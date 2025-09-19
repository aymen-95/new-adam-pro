from __future__ import annotations
from app.agency.agency import Agency
from models.types import ActionPlan


def test_agency_decides_to_eat_when_hungry():
    a = Agency()
    # make very hungry, safe
    a.drives.hunger = 0.9
    a.drives.threat = 0.0
    plan: ActionPlan = a.decide({"food_available": True})
    assert plan.action in {"eat", "seek_safety"}
    assert plan.priority >= 0.5


def test_agency_prioritizes_safety_over_food():
    a = Agency()
    a.drives.hunger = 0.9
    a.drives.threat = 0.9
    plan: ActionPlan = a.decide({"food_available": True})
    assert plan.action == "seek_safety"
