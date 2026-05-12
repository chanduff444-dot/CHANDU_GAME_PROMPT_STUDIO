import socket
import json

HOST = 'localhost'
PORT = 6789


def send(payload, timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((HOST, PORT))
    data = json.dumps(payload).encode('utf-8') + b'##END##'
    s.sendall(data)
    resp = b''
    while True:
        chunk = s.recv(8192)
        if not chunk:
            break
        resp += chunk
    s.close()
    try:
        return json.loads(resp.decode('utf-8'))
    except Exception:
        return resp.decode('utf-8')


if __name__ == '__main__':
    print('Pinging Blender listener...')
    print(send({'cmd': 'ping'}))

    print('\nRequesting scene...')
    scene = send({'cmd': 'get_scene'})
    print('Scene keys:', list(scene.keys()) if isinstance(scene, dict) else scene)

    # Example execute (optional): create a cube — run only if you expect Blender to allow it
    # print('\nExecuting sample create-cube code...')
    # code = "import bpy\nbpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))"
    # print(send({'cmd': 'execute', 'code': code}))
