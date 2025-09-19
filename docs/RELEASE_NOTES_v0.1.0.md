# SmartCore Emergent Prototype v0.1.0

Highlights:
- Drives (hunger, fatigue, curiosity, threat) + physiology (Heart BPM/HRV)
- Emergent navigation policy (potential fields + curiosity + learned tag values)
- No hand-crafted if/else reflexes for movement
- Multi-model dialectic orchestrator with bias/conflict summaries
- Live WebSocket dashboard + 2D world
- Offline video renderer (`tools/render_demo.py`) for MP4/GIF demos

How to run:
- `python smart_core_adam_pro/run_server.py` then open `http://127.0.0.1:8001/`
- Optional: `python smart_core_adam_pro/tools/render_demo.py --out demo.mp4 --seconds 60`

Security & housekeeping:
- Keep `.env` & data files out of git; `.env.example` only
- Attach videos to Releases or use LFS, not repo source

Roadmap:
- Persist learned tag weights and add richer RL
- Unity/Unreal 3D sensors, physics, and multi-agent scenes
- Vision/audio adapters + episodic/semantic memory graphs
