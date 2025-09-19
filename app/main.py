from __future__ import annotations
import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import asyncio, json, time, math
from pathlib import Path
from collections import deque

from models.types import InputEvent, ResponsePacket
from .agency.agency import Agency
from .body.body import Body
from .agency.policy import Policy

from .config import get_settings
from .core import SmartCore

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("smartcore.api")

settings = get_settings()
core = SmartCore()
core.start()
agency = Agency()
body = Body()
policy = Policy()

app = FastAPI(title=settings.app_name)


@app.post("/orchestrate", response_model=ResponsePacket)
async def orchestrate(event: InputEvent):
    try:
        ctx = {
            "weights": agency.state.weights,
            "mood": agency.state.mood.model_dump(),
            "heart": agency.heart.to_dict(),
        }
        response = await core.process_event(event, context=ctx)
        return response
    except Exception as exc:  # pragma: no cover
        logger.exception("processing_failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/memory")
async def memory(tag: str | None = None, limit: int = 5):
    entries = core.memory.query_by_tag(tag, limit) if tag else core.memory.load()[-limit:]
    return [entry.model_dump(mode="json") for entry in entries]


@app.get("/health")
async def health():
    return {"status": "ok", "models": settings.active_models}


@app.get("/agency/state")
async def agency_state():
    return agency.state.model_dump(mode="json")


class StepInput(InputEvent):
    minutes: float | None = 1.0
    food_available: bool | None = False
    threat: float | None = None
    stimulation: bool | None = False


@app.post("/agency/step")
async def agency_step(evt: StepInput):
    # Perceive environment
    signals = {"threat": evt.threat, "stimulation": evt.stimulation}
    agency.sense(signals)
    agency.step(max(0.0, float(evt.minutes or 0.0)), signals)
    plan = agency.decide({"food_available": bool(evt.food_available)})
    agency.enact(plan)
    return {
        "state": agency.state.model_dump(mode="json"),
        "plan": plan.model_dump(),
        "mood": agency.state.mood.model_dump(),
        "appetite": agency.state.appetite,
        "weights": agency.state.weights,
        "thoughts": agency.state.last_thoughts,
    }


# ---- WebSocket live feed ----

class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active.discard(websocket)

    async def broadcast(self, message: dict):
        data = json.dumps(message, ensure_ascii=False)
        for ws in list(self.active):
            try:
                await ws.send_text(data)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()
LAST_OBJECTS: list[dict] = []
PREV_DRIVES = {"hunger": 0.0, "threat": 0.0, "fatigue": 0.0}
TS = {
    "bpm": deque(maxlen=180),
    "threat": deque(maxlen=180),
    "hunger": deque(maxlen=180),
}


def _nearest(tag: str) -> tuple[dict | None, float]:
    if not LAST_OBJECTS:
        return (None, float("inf"))
    bx, by = body.state.x, body.state.y
    best, bd = None, float("inf")
    for o in LAST_OBJECTS:
        if str(o.get("tag")) != tag:
            continue
        dx, dy = float(o.get("x", 0)) - bx, float(o.get("y", 0)) - by
        d = math.hypot(dx, dy)
        if d < bd:
            best, bd = o, d
    return best, bd


def _emergent_move():
    # build relative object coordinates
    rel = []
    bx, by = body.state.x, body.state.y
    for o in LAST_OBJECTS:
        rel.append({"tag": o.get("tag"), "x": float(o.get("x", 0.0)) - bx, "y": float(o.get("y", 0.0)) - by})
    drives = {
        "hunger": agency.state.drives.hunger,
        "threat": agency.state.drives.threat,
        "curiosity": agency.state.drives.curiosity,
    }
    vx, vy = policy.nav_vector(rel, drives)
    if vx == 0 and vy == 0:
        return
    target = math.atan2(vy, vx)
    _turn_towards(target)
    # speed scales with energy and nav magnitude
    mag = min(1.0, math.hypot(vx, vy))
    speed_scale = 0.5 + 0.5 * agency.state.energy
    body.move(forward=mag * speed_scale, dt=0.25)


def _turn_towards(target_angle: float):
    # rotate body yaw toward target
    yaw = body.state.yaw
    diff = math.atan2(math.sin(target_angle - yaw), math.cos(target_angle - yaw))
    step = max(-0.3, min(0.3, diff))
    body.turn(step)


def _snapshot() -> dict:
    return {
        "ts": time.time(),
        "state": agency.state.model_dump(mode="json"),
        "mood": agency.state.mood.model_dump(),
        "appetite": agency.state.appetite,
        "weights": agency.state.weights,
        "thoughts": agency.state.last_thoughts,
        "body": body.to_dict(),
        "heart": agency.heart.to_dict(),
        "objects": LAST_OBJECTS,
        "timeseries": {
            "bpm": list(TS["bpm"]),
            "threat": list(TS["threat"]),
            "hunger": list(TS["hunger"]),
        },
    }


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    async def sender_loop():
        # periodic state broadcast to this client only
        while True:
            await asyncio.sleep(1.0)
            # advance body activity decay and heart rhythm
            body.tick(1.0)
            # emergent movement from policy & drives (no hard-coded conditions)
            _emergent_move()
            agency.heart.update(1.0, arousal=agency.state.mood.arousal, activity=body.activity())
            # timeseries sample
            TS["bpm"].append(agency.heart.state.bpm)
            TS["threat"].append(agency.state.drives.threat)
            TS["hunger"].append(agency.state.drives.hunger)
            try:
                await websocket.send_text(json.dumps({"type": "state", "data": _snapshot()}, ensure_ascii=False))
            except Exception:
                break

    async def receiver_loop():
        # handle inbound commands
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
            except Exception:
                await websocket.send_text(json.dumps({"type": "error", "error": "invalid_json"}))
                continue

            mtype = data.get("type")
            if mtype == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "ts": time.time()}))
            elif mtype == "get_state":
                await websocket.send_text(json.dumps({"type": "state", "data": _snapshot()}, ensure_ascii=False))
            elif mtype == "tick":
                minutes = float(data.get("minutes", 1.0))
                food = bool(data.get("food_available", False))
                threat = data.get("threat")
                stim = bool(data.get("stimulation", False))
                # capture prev drives for reward
                PREV_DRIVES.update({
                    "hunger": agency.state.drives.hunger,
                    "threat": agency.state.drives.threat,
                    "fatigue": agency.state.drives.fatigue,
                })
                step_evt = StepInput(type="system", value="tick", source="ws", minutes=minutes, food_available=food, threat=threat, stimulation=stim)
                # reuse REST logic
                res = await agency_step(step_evt)  # type: ignore[arg-type]
                # compute simple reward from drive deltas
                new = res["state"]["drives"]
                dh = PREV_DRIVES["hunger"] - float(new.get("hunger", 0.0))
                dt = PREV_DRIVES["threat"] - float(new.get("threat", 0.0))
                df = float(new.get("fatigue", 0.0)) - PREV_DRIVES["fatigue"]
                reward = 1.0 * dh + 0.8 * dt - 0.2 * df
                policy.update(LAST_OBJECTS, reward)
                await websocket.send_text(json.dumps({"type": "step_result", "data": res}, ensure_ascii=False))
            elif mtype == "sense":
                # update drives without time advance
                threat = data.get("threat")
                stim = bool(data.get("stimulation", False))
                agency.sense({"threat": threat, "stimulation": stim})
                await websocket.send_text(json.dumps({"type": "state", "data": _snapshot()}, ensure_ascii=False))
            elif mtype == "orchestrate":
                text = data.get("text") or ""
                evt = InputEvent(type="text", value=str(text), source="ws")
                try:
                    ctx = {
                        "weights": agency.state.weights,
                        "mood": agency.state.mood.model_dump(),
                        "heart": agency.heart.to_dict(),
                    }
                    resp = await core.process_event(evt, context=ctx)
                    await websocket.send_text(json.dumps({"type": "orchestrate_result", "data": resp.model_dump(mode="json")}, ensure_ascii=False))
                except Exception as exc:
                    await websocket.send_text(json.dumps({"type": "error", "error": str(exc)}))
            elif mtype == "body_cmd":
                cmd = data.get("cmd")
                if cmd == "turn":
                    body.turn(float(data.get("delta", 0.0)))
                elif cmd == "look":
                    body.look(float(data.get("delta", 0.0)))
                elif cmd == "move":
                    body.move(float(data.get("forward", 0.0)), float(data.get("sideways", 0.0)), float(data.get("dt", 0.2)))
                elif cmd == "pose":
                    body.pose(left=data.get("left"), right=data.get("right"))
                elif cmd == "reset":
                    body.reset()
                await websocket.send_text(json.dumps({"type": "body_state", "data": body.to_dict()}, ensure_ascii=False))
            elif mtype == "vision":
                # objects: [{id, x, y, tag}] from UI; use as visual input
                objects = data.get("objects") or []
                agency.observe_vision(objects)
                # keep server-side snapshot to enable auto navigation
                LAST_OBJECTS[:] = list(objects)
                await websocket.send_text(json.dumps({"type": "ack", "ok": True}))
            else:
                await websocket.send_text(json.dumps({"type": "error", "error": "unknown_type"}))

    sender = asyncio.create_task(sender_loop())
    receiver = asyncio.create_task(receiver_loop())
    try:
        await asyncio.gather(sender, receiver)
    except WebSocketDisconnect:
        pass
    finally:
        sender.cancel()
        receiver.cancel()
        manager.disconnect(websocket)


# ---- Simple UI (static) ----

_UI_DIR = Path(__file__).resolve().parents[1] / "ui"
if _UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")


@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/ui/")
