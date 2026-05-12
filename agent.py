"""
Chandu Prompt Studio — Autonomous Blender Agent
The core agent loop:
  1. Read scene state from Blender
  2. Plan actions with AI
  3. Generate code with AI
  4. Execute in Blender
  5. If error  fix and retry (max 3x)
  6. Report final result
"""

import socket
import json
import time

BLENDER_HOST = "localhost"
BLENDER_PORT = 6789
MAX_RETRIES = 3

#  Blender Socket Communication 

def _send_to_blender(payload, timeout=30):
    """Send a command to Blender and return the response."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((BLENDER_HOST, BLENDER_PORT))
        data = json.dumps(payload).encode("utf-8") + b"##END##"
        s.sendall(data)

        response = b""
        s.settimeout(timeout)
        while True:
            chunk = s.recv(8192)
            if not chunk:
                break
            response += chunk
        s.close()
        return json.loads(response.decode("utf-8"))

    except ConnectionRefusedError:
        return {
            "status": "error",
            "message": "Cannot connect to Blender. Is blender_listener.py running inside Blender?"
        }
    except socket.timeout:
        return {"status": "error", "message": "Blender connection timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ping_blender():
    """Check if Blender listener is active."""
    result = _send_to_blender({"cmd": "ping"}, timeout=3)
    return result.get("status") == "ok"


def get_scene_state():
    """Get the full scene graph from Blender."""
    result = _send_to_blender({"cmd": "get_scene"}, timeout=10)
    if result.get("status") == "ok":
        return result.get("scene", {})
    return {}


def execute_in_blender(code):
    """Execute Python code in Blender and return result."""
    return _send_to_blender({"cmd": "execute", "code": code}, timeout=60)


#  Autonomous Agent Loop 

def run_agent(user_prompt, model, callbacks=None):
    """
    Full autonomous agent loop.

    callbacks dict (all optional):
      on_status(msg)        	6 status updates (connecting, planning, etc.)
      on_plan_token(tok)    	6 streaming plan tokens
      on_code_token(tok)    	6 streaming code tokens
      on_fix_token(tok)     	6 streaming fix tokens
      on_scene(state)       	6 called with scene dict
      on_code(code)         	6 called with final code string
      on_success(msg)       	6 called on success
      on_error(msg)         	6 called with unrecoverable error
      on_retry(n, error)    	6 called before each retry attempt
    """
    from ollama_engine import plan_actions, generate_code, fix_code

    cb = callbacks or {}
    status   = cb.get("on_status",     lambda m: None)
    on_scene = cb.get("on_scene",      lambda s: None)
    on_code  = cb.get("on_code",       lambda c: None)
    success  = cb.get("on_success",    lambda m: None)
    error    = cb.get("on_error",      lambda m: None)
    on_retry = cb.get("on_retry",      lambda n, e: None)

    # ── STEP 1: Check Blender connection ──
    status("🔌 Connecting to Blender...")
    if not ping_blender():
        error("Cannot reach Blender. Run blender_listener.py inside Blender first.")
        return False

    status("✅ Blender connected")

    # ── STEP 2: Read scene state ──
    status("👁  Reading Blender scene...")
    scene = get_scene_state()
    on_scene(scene)
    obj_count = len(scene.get("objects", []))
    status(f"📋 Scene: {obj_count} objects, {len(scene.get('lights',[]))} lights, {len(scene.get('cameras',[]))} cameras")

    # ── STEP 3: Plan actions ──
    status("🧠 Planning actions...")
    plan = plan_actions(
        user_prompt, scene, model,
        on_token=cb.get("on_plan_token")
    )
    status("📝 Plan ready")

    # ── STEP 4: Generate code ──
    status("⚡ Generating Blender code...")
    code = generate_code(
        user_prompt, scene, plan, model,
        on_token=cb.get("on_code_token")
    )
    on_code(code)

    # ── STEP 5: Execute + retry loop ──
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            status(f"🔧 Auto-fixing error (attempt {attempt}/{MAX_RETRIES})...")
            on_retry(attempt, last_error)
            code = fix_code(
                code, last_error, scene, model,
                on_token=cb.get("on_fix_token")
            )
            on_code(code)

        status(f"🚀 Executing in Blender (attempt {attempt})...")
        result = execute_in_blender(code)

        if result.get("status") == "success":
            scene_after = result.get("scene_after", {})
            on_scene(scene_after)
            new_count = len(scene_after.get("objects", []))
            status(f"✅ Done! Scene now has {new_count} objects")
            success(f"Completed in {attempt} attempt(s). Scene updated.")
            return True
        else:
            last_error = result.get("message", "Unknown error")
            status(f"❌ Error on attempt {attempt}: {last_error[:80]}...")
            if attempt < MAX_RETRIES:
                time.sleep(0.5)

    error(f"Agent failed after {MAX_RETRIES} attempts.\nLast error:\n{last_error}")
    return False
