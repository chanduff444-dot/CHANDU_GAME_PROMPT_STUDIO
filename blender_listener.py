"""
CHANDU AI LAB - Blender Socket Listener
========================================
STEP 1: Open Blender
STEP 2: Go to Scripting tab
STEP 3: Paste this entire file and click RUN
STEP 4: Blender is now listening for your app!
"""

import bpy
import socket
import threading
import traceback

HOST = "localhost"
PORT = 6789

def execute_code(code):
    """Run AI-generated code inside Blender safely."""
    try:
        exec(compile(code, "<chandu_ai>", "exec"), {"bpy": bpy})
        return "OK: Code executed successfully"
    except Exception as e:
        return f"ERROR: {traceback.format_exc()}"

def handle_client(conn):
    """Handle one connection from the app."""
    try:
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"##END##" in data:
                break
        code = data.replace(b"##END##", b"").decode("utf-8")
        print(f"\n[Chandu AI] Received code ({len(code)} chars)")
        result = execute_code(code)
        conn.sendall(result.encode("utf-8"))
        print(f"[Chandu AI] {result[:80]}")
    except Exception as e:
        print(f"[Chandu AI] Connection error: {e}")
    finally:
        conn.close()

def start_server():
    """Start the socket server in a background thread."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"\n{'='*50}")
    print(f"  CHANDU AI LAB - Blender Listener ACTIVE")
    print(f"  Listening on {HOST}:{PORT}")
    print(f"  Ready to receive AI-generated code!")
    print(f"{'='*50}\n")
    while True:
        try:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn,), daemon=True)
            t.start()
        except Exception as e:
            print(f"[Chandu AI] Server error: {e}")
            break

# Start server in background so Blender doesn't freeze
thread = threading.Thread(target=start_server, daemon=True)
thread.start()
print("[Chandu AI] Socket listener started in background!")