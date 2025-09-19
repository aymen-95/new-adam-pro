from __future__ import annotations
import math, random, argparse
from pathlib import Path
from typing import List, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont
import imageio

# Import internal modules (no server needed)
import sys
from pathlib import Path as _Path
sys.path.append(str(_Path(__file__).resolve().parents[1]))
from app.agency.agency import Agency
from app.agency.policy import Policy
from app.body.body import Body


def world_to_screen(x: float, y: float, origin: Tuple[int, int], scale: float) -> Tuple[int, int]:
    ox, oy = origin
    return int(ox + x * scale), int(oy + y * scale)


def draw_frame(img: Image.Image, body: Body, objects: List[dict], agency: Agency, ts: Dict[str, list]):
    d = ImageDraw.Draw(img)
    W, H = img.size

    # Panels
    pad = 20
    room_w, room_h = body.room_w, body.room_h
    scale = min((W*0.55 - 2*pad) / room_w, (H - 2*pad) / room_h)
    origin = (pad, pad)

    # Background
    d.rectangle([0,0,W,H], fill=(11,16,32))

    # Room
    d.rectangle([origin[0], origin[1], origin[0] + room_w*scale, origin[1] + room_h*scale], outline=(31,41,71), width=2)

    # Objects
    for o in objects:
        cx, cy = world_to_screen(o['x'], o['y'], origin, scale)
        color = (108,192,255)
        tag = str(o.get('tag',''))
        if tag == 'food':
            color = (125,245,157)
        elif tag == 'hazard':
            color = (255,107,107)
        d.ellipse([cx-6, cy-6, cx+6, cy+6], fill=color)

    # Agent
    bx, by = world_to_screen(body.state.x, body.state.y, origin, scale)
    d.ellipse([bx-10, by-10, bx+10, by+10], fill=(125,245,157))
    # Facing
    d.line([bx, by, bx + 18*math.cos(body.state.yaw), by + 18*math.sin(body.state.yaw)], fill=(125,245,157), width=2)
    gaze = body.state.yaw + body.state.head_yaw
    d.line([bx, by, bx + 24*math.cos(gaze), by + 24*math.sin(gaze)], fill=(255,228,138), width=2)

    # Hands
    d.line([bx, by, bx-14, by-20*body.state.left_hand], fill=(122,208,122), width=2)
    d.line([bx, by, bx+14, by-20*body.state.right_hand], fill=(122,208,122), width=2)

    # Right panel text
    right_x = int(W*0.58)
    text_y = pad
    fg = (230,233,239)
    muted = (154,165,177)
    def tline(label, val):
        nonlocal text_y
        d.text((right_x, text_y), f"{label}: {val}", fill=fg)
        text_y += 22

    mood = agency.state.mood
    tline("Mood", f"{mood.label} | v={mood.valence:.2f}, a={mood.arousal:.2f}")
    tline("Appetite", f"{agency.state.appetite:.2f}")
    tline("Heart", f"{agency.heart.state.bpm:.0f} bpm | hrv={agency.heart.state.hrv:.2f}")
    tline("Drives", f"H={agency.state.drives.hunger:.2f} F={agency.state.drives.fatigue:.2f} C={agency.state.drives.curiosity:.2f} T={agency.state.drives.threat:.2f}")
    text_y += 10
    # Thoughts (last 3)
    d.text((right_x, text_y), "Thoughts:", fill=muted); text_y += 18
    for t in agency.state.last_thoughts[:3]:
        d.text((right_x, text_y), f"- {t[:70]}", fill=fg); text_y += 18

    # Sparklines
    def spark(x, y, w, h, arr, vmin, vmax, color):
        d.rectangle([x,y,x+w,y+h], outline=(31,41,71), width=1)
        if len(arr) < 2:
            return
        n = len(arr)
        sx = w / max(1, n-1)
        pts = []
        for i, v in enumerate(arr):
            t = (max(vmin, min(vmax, v)) - vmin) / (vmax - vmin + 1e-6)
            yy = y + h - t*h
            xx = x + i*sx
            pts.append((xx,yy))
        d.line(pts, fill=color, width=2)

    spark(right_x, H-120, 260, 40, ts['bpm'], 50, 160, (255,107,107))
    spark(right_x, H-70, 260, 40, ts['threat'], 0, 1, (247,209,95))


def run_demo(out: Path, seconds: float = 15.0, fps: int = 10, seed: int = 7):
    random.seed(seed)

    # World and agent
    agency = Agency()
    body = Body()
    policy = Policy()

    # Objects
    objects = [
        {"id": "food1", "x": 120.0, "y": 90.0, "tag": "food"},
        {"id": "haz1", "x": 420.0, "y": 280.0, "tag": "hazard"},
        {"id": "o1", "x": 260.0, "y": 60.0, "tag": ""},
    ]

    # Time stepping
    dt = 1.0 / fps
    frames = int(seconds * fps)
    W, H = 900, 540
    timeseries = {"bpm": [], "threat": [], "hunger": []}

    images = []
    prev = {"hunger": agency.state.drives.hunger, "threat": agency.state.drives.threat, "fatigue": agency.state.drives.fatigue}

    for i in range(frames):
        # Vision → curiosity boost
        agency.observe_vision(objects)
        # Nav vector from policy & drives
        rel = [{"tag": o['tag'], "x": o['x']-body.state.x, "y": o['y']-body.state.y} for o in objects]
        vx, vy = policy.nav_vector(rel, {"hunger": agency.state.drives.hunger, "threat": agency.state.drives.threat, "curiosity": agency.state.drives.curiosity})
        if vx or vy:
            target = math.atan2(vy, vx)
            # turn and move scaled by energy
            yaw = body.state.yaw
            diff = math.atan2(math.sin(target - yaw), math.cos(target - yaw))
            step = max(-0.3, min(0.3, diff))
            body.turn(step)
            mag = min(1.0, math.hypot(vx, vy))
            speed_scale = 0.5 + 0.5 * agency.state.energy
            body.move(forward=mag * speed_scale, dt=dt)
        else:
            body.tick(dt)

        # Step drives + heart
        agency.step(dt/60.0, {})
        agency.heart.update(dt, arousal=agency.state.mood.arousal, activity=0.5*mag if (vx or vy) else 0.0)

        # Reward update every 1s
        if (i % fps) == 0 and i > 0:
            new = {"hunger": agency.state.drives.hunger, "threat": agency.state.drives.threat, "fatigue": agency.state.drives.fatigue}
            reward = (prev['hunger'] - new['hunger']) + 0.8*(prev['threat'] - new['threat']) - 0.2*(new['fatigue'] - prev['fatigue'])
            policy.update(objects, reward)
            prev = new

        # Timeseries
        timeseries['bpm'].append(agency.heart.state.bpm)
        timeseries['threat'].append(agency.state.drives.threat)
        timeseries['hunger'].append(agency.state.drives.hunger)

        # Render frame
        img = Image.new("RGB", (W, H))
        draw_frame(img, body, objects, agency, timeseries)
        images.append(img)

    # Try MP4, fallback to GIF
    if out.suffix.lower() == ".mp4":
        try:
            imageio.mimsave(out, images, fps=fps, codec="libx264", quality=8)
            return
        except Exception:
            # fallback
            pass
        out = out.with_suffix('.gif')
    imageio.mimsave(out, images, duration=1.0/fps)


def main():
    p = argparse.ArgumentParser(description="Render an offline demo video of the SmartCore agent")
    p.add_argument("--out", default="demo_new_adam.mp4", help="Output video path (.mp4 or .gif)")
    p.add_argument("--seconds", type=float, default=20.0, help="Duration in seconds")
    p.add_argument("--fps", type=int, default=10, help="Frames per second")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    run_demo(out, seconds=args.seconds, fps=args.fps, seed=args.seed)
    print(f"Saved demo to {out}")


if __name__ == "__main__":
    main()
