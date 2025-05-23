from flask import Flask, request, jsonify, abort
import os
import json
import requests

app = Flask(__name__)
DEVICE_FILE = "devices.json"
BOT_TOKEN = "7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc"
CHAT_ID = "7554840326"  # Your personal Telegram Chat ID

# Load registered devices
def load_devices():
    if os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, "r") as f:
            return json.load(f)
    return {}

# Save devices
def save_devices(devices):
    with open(DEVICE_FILE, "w") as f:
        json.dump(devices, f)

devices = load_devices()

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    device_id = data.get("device_id")
    device_name = data.get("device_name")
    chat_id = data.get("chat_id")

    if device_id and device_name:
        devices[device_id] = {
            "device_name": device_name,
            "chat_id": chat_id
        }
        save_devices(devices)

        # Notify bot owner
        msg = f"✅ Device connected:\nName: {device_name}\nID: {device_id}"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": msg
        })

        return jsonify({"status": "registered"}), 200

    return jsonify({"error": "Missing fields"}), 400

@app.route("/devices", methods=["GET"])
def get_devices():
    device_list = [
        {"device_id": k, "device_name": v["device_name"]}
        for k, v in devices.items()
    ]
    return jsonify({"devices": device_list}), 200

@app.route("/ping/<device_id>", methods=["GET"])
def ping_device(device_id):
    if device_id not in devices:
        return abort(404)
    # For now, we treat registered = alive
    return jsonify({"status": "alive"}), 200

@app.route("/command", methods=["POST"])
def send_command():
    data = request.json
    device_id = data.get("device_id")
    command = data.get("command")
    args = data.get("args")

    print(f"[COMMAND] To: {device_id} | CMD: {command} | Args: {args}")
    return jsonify({"status": "sent"}), 200

if __name__ == "__main__":
    print("Flask server running on port 10000...")
    app.run(host="0.0.0.0", port=10000)
