"""
CHANDU PROMPT STUDIO — Blender Agent Listener
==============================================
Paste this into Blender's Scripting tab and click RUN.
This gives your app eyes into Blender — it can read the scene,
execute code, and report errors back to the agent automatically.
"""

import bpy
import socket
import threading
import traceback
import json
import mathutils

HOST = "localhost"
PORT = 6789

# ── Scene Reader ────────────────────────────────────────────────

def get_scene_state():
    """Read everything in the current Blender scene and return as dict."""
    scene = bpy.context.scene
    state = {
        "frame_current": scene.frame_current,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "objects": [],
        "lights": [],
        "cameras": [],
        "materials": [],
        "collections": [c.name for c in bpy.data.collections],
    }

    for obj in scene.objects:
        entry = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "visible": obj.visible_get(),
        }

        if obj.type == "MESH":
            entry["vertices"] = len(obj.data.vertices)
            entry["faces"] = len(obj.data.polygons)
            entry["materials"] = [m.name for m in obj.data.materials if m]
            state["objects"].append(entry)

        elif obj.type == "LIGHT":
            entry["light_type"] = obj.data.type
            entry["energy"] = obj.data.energy
            entry["color"] = list(obj.data.color)
            state["lights"].append(entry)

        elif obj.type == "CAMERA":
            entry["lens"] = obj.data.lens
            state["cameras"].append(entry)

    for mat in bpy.data.materials:
        state["materials"].append({
            "name": mat.name,
            "use_nodes": mat.use_nodes,
        })

    return state

# ── Code Executor ───────────────────────────────────────────────

def execute_code(code):
    """Execute Blender Python code and return result dict."""
    try:
        namespace = {"bpy": bpy, "mathutils": mathutils}
        exec(compile(code, "<chandu_agent>", "exec"), namespace)
        scene_after = get_scene_state()
        return {
            "status": "success",
            "message": "Code executed successfully",
            "scene_after": scene_after,
        }
    except Exception:
        return {
            "status": "error",
            "message": traceback.format_exc(),
            "scene_after": None,
        }

# ── Request Handler ─────────────────────────────────────────────

def handle_request(payload):
    """Route incoming request to correct handler."""
    cmd = payload.get("cmd", "")

    if cmd == "ping":
        return {"status": "ok", "message": "Blender agent listener active"}

    elif cmd == "get_scene":
        return {"status": "ok", "scene": get_scene_state()}

    elif cmd == "execute":
        code = payload.get("code", "")
        return execute_code(code)

    else:
        return {"status": "error", "message": f"Unknown command: {cmd}"}

def handle_client(conn):
    try:
        data = b""
        while True:
            chunk = conn.recv(8192)
            if not chunk:
                break
            data += chunk
            if b"##END##" in data:
                break

        raw = data.replace(b"##END##", b"").decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"cmd": "execute", "code": raw}
        result = handle_request(payload)
        response = json.dumps(result).encode("utf-8")
        conn.sendall(response)

    except Exception as e:
        err = json.dumps({"status": "error", "message": str(e)})
        try:
            conn.sendall(err.encode("utf-8"))
        except:
            pass
    finally:
        conn.close()

# ── Server ──────────────────────────────────────────────────────

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"\n{'='*55}")
    print(f"  CHANDU PROMPT STUDIO — Blender Agent ACTIVE")
    print(f"  Listening on {HOST}:{PORT}")
    print(f"  Agent can now SEE and CONTROL this Blender session")
    print(f"{'='*55}\n")
    while True:
        try:
            conn, _ = server.accept()
            t = threading.Thread(target=handle_client, args=(conn,), daemon=True)
            t.start()
        except Exception as e:
            print(f"[Agent Listener] Error: {e}")
            break

thread = threading.Thread(target=start_server, daemon=True)
thread.start()
print("[Chandu] Agent listener running in background. Open your app now!")