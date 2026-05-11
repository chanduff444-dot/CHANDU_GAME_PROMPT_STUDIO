# Chandu Game Prompt Studio

Offline prompt-to-Blender app using Ollama.
Built to feel like a compact studio dashboard for prompt-driven 3D and game asset creation.
Future plan: connect the same asset pipeline to Unreal Engine as well.

## Flow

1. You type a prompt in the desktop app.
2. App sends prompt to local Ollama model.
3. App receives Blender Python code.
4. App sends code to Blender listener over socket.
5. Blender executes code and returns status.

## Files

- blender_listener.py: Run inside Blender once per session.
- blender_ai_app.py: Desktop UI app.
- blender_bridge.py: Socket client from app to Blender.
- ollama_engine.py: Ollama integration and streaming.
- code_cleaner.py: Code cleanup and syntax validation.
- requirements.txt: Python dependencies.

## Setup

1. Install dependencies:

   pip install -r requirements.txt

2. Start Ollama server:

   ollama serve

3. Pull at least one model (example):

   ollama pull llama3.1

4. Start Blender and run listener:

   - Open Blender -> Scripting tab.
   - Open blender_listener.py.
   - Click Run Script.

5. Start app:

   python blender_ai_app.py

   or double-click run_app.bat

## Notes

- Blender listener runs on localhost:6789.
- If app shows Blender waiting, listener is not running yet.
- The bpy import warning in VS Code is normal outside Blender.
- Unreal Engine integration will be added later through export/import or automation scripts.

## Studio-style feature direction

- cleaner project dashboard layout
- asset generation presets for games and scenes
- export pipeline for Blender, Unity, and Unreal
- preview panels for prompts, logs, and generated code
- branded studio UI with a more professional look and feel
