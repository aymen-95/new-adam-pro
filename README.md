# Smart Core Adam Pro

An advanced cognitive orchestration engine combining multi-model reasoning, dialectical analysis, internal monologue, bias detection, and conflict synthesis.

## Highlights
- Orchestrator dispatches prompts to configurable adapters (GPT, DeepSeek, Gemini, Copilot) with async execution.
- Dialectic engine builds agreement/contradiction maps.
- Internal monologue generates self-challenging reflections.
- Bias detector and conflict analyzer provide transparency.
- Response synthesizer merges supporting/opposing viewpoints into a structured packet.

## Project Layout
```
smart_core_adam_pro/
├── app/
│   ├── adapters/
│   │   ├── base.py
│   │   ├── gpt.py
│   │   ├── deepseek.py
│   │   ├── gemini.py
│   │   └── copilot.py
│   ├── pipelines/
│   │   ├── dialectic_engine.py
│   │   ├── internal_monologue.py
│   │   ├── bias_detector.py
│   │   ├── conflict_analyzer.py
│   │   └── response_synthesizer.py
│   ├── config.py
│   ├── core.py
│   ├── memory.py
│   ├── orchestrator.py
│   └── main.py
├── models/
│   └── types.py
├── data/
│   └── memory.json
├── tests/
│   ├── test_orchestrator.py
│   └── test_end_to_end.py
├── run_server.py
├── requirements.txt
├── README.md
└── .env.example
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment
Copy `.env.example` to `.env` and adjust values. Key variables:
- `ACTIVE_MODELS`: comma-separated model identifiers
- `ENABLE_THINK_LOOP`: enable internal self-query loop
- `MEMORY_PATH`: persistent memory storage path

## Run API
```
python run_server.py
```
The API listens on `http://127.0.0.1:8001`.

### Sample Request
```bash
curl -X POST http://127.0.0.1:8001/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"type":"text","value":"Should AI make ethical decisions?","source":"user"}'
```

## Tests
```
pytest -q
```

## Security & Expansion Notes
- Adapters isolate external API keys; integrate real APIs by extending adapter logic.
- Memory is file-based; migrate to resilient storage (Redis/PG) for production.
- Add additional adapters or pipelines via dependency injection.
