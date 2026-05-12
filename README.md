# Chandu Prompt Studio — Autonomous Blender Agent (Level 3)

This project provides an autonomous Blender agent that:

- Reads Blender scene state
- Uses a local Ollama model to plan, generate, and fix Blender Python code
- Executes code inside Blender via a socket listener
- Retries automatically (configurable retries) and reports results

## Key Scripts

- `blender_listener.py`: Run inside Blender (Scripting tab). Exposes a socket API for scene read/execute.
- `agent.py`: Core autonomous loop (plan → code → execute → fix → retry).
- `ollama_engine.py`: Planner / coder / fixer helpers and streaming support.
- `app.py`: Desktop UI (CustomTkinter) for prompts, logs, models, and running the agent.
- `requirements.txt`: Python dependencies.

## Quick Start

1. Install Python deps:

```bash
pip install -r requirements.txt
```

2. Start Ollama server locally:

```bash
ollama serve
```

3. Pull a model (example):

```bash
ollama pull deepseek-coder:6.7b
```

4. Start Blender and run the listener:

Open Blender → Scripting tab → open `blender_listener.py` → Run Script

5. Launch the desktop app:

```bash
python app.py
```

6. In the app: select a model, enter a prompt, and click `RUN AGENT`.

## Notes & Troubleshooting

- Blender listener default: `localhost:6789` (update if needed in `agent.py`).
- If the app cannot reach Ollama, ensure `ollama serve` is running and the model is pulled.
- Run `blender_listener.py` inside Blender — `bpy` only works in Blender's Python.
- The agent will attempt up to the configured retries to auto-fix errors returned from Blender.

## Next Steps

- Add authentication or TLS for remote Blender sessions.
- Add more robust validation of generated code before execution.
- Improve model prompts for fidelity and safety checks.

Enjoy building with Chandu Prompt Studio! If you want, I can run a quick code validation or wire up a ZIP packaging step next.
