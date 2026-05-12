"""
Chandu Prompt Studio — Ollama AI Engine
Handles: planning, code generation, error fixing
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434"

# ── Prompts ──────────────────────────────────────────────────────

PLANNER_SYSTEM = """You are the planning brain of Chandu Prompt Studio, an autonomous Blender AI agent.
Given the user's request and the current Blender scene state, create a clear step-by-step action plan.
Be concise. List only the key steps needed. Max 6 steps.
Format: numbered list only. No extra explanation."""

CODER_SYSTEM = """You are an expert Blender Python (bpy) coder for Chandu Prompt Studio.
You receive a user request, the current scene state, and an action plan.
You MUST output ONLY valid executable Blender Python code.
Rules:
- Start with: import bpy
- Never use markdown, no backticks, no explanations
- Clear existing objects when starting fresh: bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
- Use only valid bpy API — bpy.ops, bpy.data, bpy.context
- For materials always use nodes: mat.use_nodes = True
- For animations use keyframes (frame 1-120)
- Handle all potential errors inside the code with try/except where needed"""

FIXER_SYSTEM = """You are an autonomous Blender Python error-fixer for Chandu Prompt Studio.
You will be given: the original code, the error message, and the current scene state.
Your job is to output a FIXED version of the code that resolves the error.
Output ONLY the corrected Python code. No explanations. No markdown."""

# ── Helpers ──────────────────────────────────────────────────────

def _stream(model, system, prompt, on_token=None):
    """Stream from Ollama and return full response."""
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": True,
    }
    full = ""
    try:
        with requests.post(f"{OLLAMA_URL}/api/generate", json=payload,
                           stream=True, timeout=180) as r:
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        full += token
                        if on_token:
                            on_token(token)
                        if data.get("done"):
                            break
                    except:
                        pass
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Ollama not running. Start with: ollama serve")
    return full


def clean_code(raw):
    """Strip markdown fences and non-code preamble."""
    import re
    text = re.sub(r"```python\s*", "", raw)
    text = re.sub(r"```\s*", "", text)
    lines = text.splitlines()
    code_lines = []
    in_code = False
    skip = ("here", "this", "below", "note:", "sure", "certainly",
            "i will", "let me", "the following", "of course", "to ")
    for line in lines:
        s = line.strip().lower()
        if not in_code and s == "":
            continue
        if any(s.startswith(p) for p in skip) and not in_code:
            continue
        if s.startswith(("import ", "from ", "bpy", "#", "def ", "class ", "mat", "obj")):
            in_code = True
        if in_code:
            code_lines.append(line)
    result = "\n".join(code_lines).strip()
    return result if result else text.strip()

# ── Public API ────────────────────────────────────────────────────

def check_ollama():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except:
        return False


def get_models():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except:
        pass
    return []


def plan_actions(user_prompt, scene_state, model, on_token=None):
    """Step 1: AI plans what actions to take."""
    scene_summary = f"""
Current scene has:
- {len(scene_state.get('objects', []))} mesh objects: {[o['name'] for o in scene_state.get('objects', [])]}
- {len(scene_state.get('lights', []))} lights
- {len(scene_state.get('cameras', []))} cameras
- Materials: {[m['name'] for m in scene_state.get('materials', [])]}
- Frame range: {scene_state.get('frame_start')} - {scene_state.get('frame_end')}
"""
    prompt = f"User request: {user_prompt}\n\nCurrent Blender scene:\n{scene_summary}\n\nCreate an action plan:"
    return _stream(model, PLANNER_SYSTEM, prompt, on_token=on_token)


def generate_code(user_prompt, scene_state, plan, model, on_token=None):
    """Step 2: AI generates Blender Python code."""
    scene_json = json.dumps(scene_state, indent=2)
    prompt = f"""User request: {user_prompt}

Action plan:
{plan}

Current scene state:
{scene_json}

Write the complete Blender Python code:"""
    raw = _stream(model, CODER_SYSTEM, prompt, on_token=on_token)
    return clean_code(raw)


def fix_code(original_code, error_message, scene_state, model, on_token=None):
    """Step 3: AI fixes broken code automatically."""
    scene_json = json.dumps(scene_state, indent=2)
    prompt = f"""Original code that failed:
{original_code}

Error message:
{error_message}

Current scene state:
{scene_json}

Write the fixed code:"""
    raw = _stream(model, FIXER_SYSTEM, prompt, on_token=on_token)
    return clean_code(raw)


def generate_blender_code(prompt, model, on_token=None):
    """Compatibility wrapper: generate Blender code given only a prompt and model.

    This keeps older callers working (blender_ai_app, ai_engine) by creating
    a minimal empty scene state and asking the planner for a short plan,
    then requesting code generation. The `on_token` callback streams code tokens.
    """
    # Minimal scene state for backward compatibility
    scene_state = {}
    # Create a short plan (no streaming for plan here)
    try:
        plan = plan_actions(prompt, scene_state, model, on_token=None)
    except Exception:
        plan = ""
    # Generate code (stream tokens via on_token)
    return generate_code(prompt, scene_state, plan, model, on_token=on_token)