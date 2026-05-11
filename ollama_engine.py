"""
Chandu AI Lab - Ollama Engine
Handles all communication with local Ollama AI.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434"

SYSTEM_PROMPT = """You are a Blender Python (bpy) expert for Chandu AI Lab.
The user will describe what they want to create or do in Blender.
You MUST respond with ONLY executable Blender Python code.
No explanations. No markdown. No code blocks. No comments unless inside the code.

MANDATORY RULES:
- Always start with: import bpy
- Always clear scene: bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
- ONLY use valid bpy API calls. Check every function name.
- NEVER use nonexistent attributes like: .metrics, .size (on primitives), .horizon_color
- For primitives use: bpy.ops.mesh.primitive_cube_add(size=2)
- For world settings use: bpy.context.scene.world.use_nodes = True
- NEVER access None objects. Check object existence first.

CORRECT EXAMPLES:
- Add cube: bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
- Add sphere: bpy.ops.mesh.primitive_uv_sphere_add(radius=1)
- Get object: obj = bpy.context.active_object
- Set material: obj.data.materials.append(mat)
- Rotate object: obj.rotation_euler = (0, 0, 1.57)
- Keyframe: obj.keyframe_insert(data_path='location', frame=1)

ERRORS TO AVOID:
- Do NOT use 'size' parameter on object rotation/scale
- Do NOT access properties on None objects
- Do NOT use undefined attributes
- Do NOT try to access context if no object is active
- Always use proper operator parameter names from Blender docs

For gears specifically:
- Use bmesh for tooth geometry or model simple circular discs
- Use proper rotation matrices for gear meshing
- Test tooth count ratios before setting rotation speeds
"""

def get_models():
    """Fetch list of available Ollama models."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return [m["name"] for m in data.get("models", [])]
    except:
        pass
    return []

def check_ollama():
    """Check if Ollama is running."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except:
        return False

def generate_blender_code(prompt, model, on_token=None):
    """
    Stream AI response from Ollama.
    on_token: callback(text) called for each chunk — use to update UI live.
    Returns final complete code string.
    """
    full_prompt = f"""Create Blender Python code for this request:

{prompt}

Return ONLY the Python code. Nothing else."""

    payload = {
        "model": model,
        "prompt": full_prompt,
        "system": SYSTEM_PROMPT,
        "stream": True,
    }

    full_response = ""
    try:
        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=120
        ) as r:
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        full_response += token
                        if on_token:
                            on_token(token)
                        if data.get("done"):
                            break
                    except:
                        pass
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to Ollama. Is it running? Run: ollama serve")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")

    return full_response

def clean_code(raw):
    """Strip markdown and non-code lines from AI output."""
    import re
    text = re.sub(r"```python", "", raw)
    text = re.sub(r"```", "", text)
    lines = text.splitlines()
    code_lines = []
    in_code = False
    skip_starts = ("here", "this", "below", "note:", "sure", "certainly",
                   "i will", "let me", "the following", "of course")
    for line in lines:
        s = line.strip().lower()
        if not in_code and s == "":
            continue
        if any(s.startswith(p) for p in skip_starts):
            continue
        if s.startswith(("import ", "from ", "bpy", "#", "def ", "class ")):
            in_code = True
        if in_code:
            code_lines.append(line)
    result = "\n".join(code_lines).strip()
    return result if result else text.strip()