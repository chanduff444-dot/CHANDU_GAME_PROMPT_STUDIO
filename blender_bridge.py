import socket
import json

HOST = "localhost"
PORT = 6789
END_MARKER = b"##END##"


def check_blender_listener(host=HOST, port=PORT, timeout=0.75):
    """Return True if Blender socket listener is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def send_code_to_blender(code, host=HOST, port=PORT, timeout=20):
    """Send Python code to Blender listener and return execution result text."""
    payload = json.dumps({"cmd": "execute", "code": code}).encode("utf-8") + END_MARKER

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(payload)
        sock.shutdown(socket.SHUT_WR)

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

    return response.decode("utf-8", errors="replace").strip()
