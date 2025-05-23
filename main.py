from flask import Flask, request, jsonify
import json
import os
import requests

app = Flask(__name__)

BOT_TOKEN = "7814616506:AAHixHaptUH9hPcLq3awDS3mqHGScs3y9Yc"
OWNER_CHAT_ID = "7554840326"
CLIENTS_FILE = "clients.json"

def load_clients():
    if os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_clients(clients):
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f)

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    device_id = data.get("device_id")
    name = data.get("device_name")
    chat_id = data.get("chat_id")

    if not device_id or not name or not chat_id:
        return jsonify({"error": "Missing required fields"}), 400

    clients = load_clients()
    clients[device_id] = {
        "device_name": name,
        "chat_id": chat_id
    }
    save_clients(clients)

    msg = f"✅ New device:\n• Name: {name}\n• ID: {device_id}"
    send_message(OWNER_CHAT_ID, msg)

    return jsonify({"message": "Device registered successfully"}), 200

@app.route("/devices", methods=["GET"])
def list_devices():
    clients = load_clients()
    return jsonify(clients), 200

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=data)
    except Exception as e:
        print(f"Failed to send message: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
