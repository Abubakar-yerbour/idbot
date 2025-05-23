from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)
devices = {}  # device_id -> {'name': ..., 'last_command': '', 'response': ''}
lock = Lock()

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    device_id = data.get("device_id")
    name = data.get("device_name")

    if not device_id or not name:
        return "Missing data", 400

    with lock:
        devices[device_id] = {
            'name': name,
            'last_command': '',
            'response': ''
        }

    return "Registered", 200

@app.route("/devices", methods=["GET"])
def list_devices():
    with lock:
        return jsonify({k: v['name'] for k, v in devices.items()})

@app.route("/send_command", methods=["POST"])
def send_command():
    data = request.json
    device_id = data.get("device_id")
    command = data.get("command")

    with lock:
        if device_id in devices:
            devices[device_id]['last_command'] = command
            return "Command sent", 200
    return "Device not found", 404

@app.route("/get_command/<device_id>", methods=["GET"])
def get_command(device_id):
    with lock:
        if device_id in devices:
            cmd = devices[device_id]['last_command']
            devices[device_id]['last_command'] = ''
            return jsonify({'command': cmd})
    return "Not found", 404

@app.route("/send_response/<device_id>", methods=["POST"])
def receive_response(device_id):
    data = request.json
    response = data.get("response")

    with lock:
        if device_id in devices:
            devices[device_id]['response'] = response
            return "Response saved", 200
    return "Device not found", 404

@app.route("/get_response/<device_id>", methods=["GET"])
def get_response(device_id):
    with lock:
        if device_id in devices:
            return jsonify({'response': devices[device_id]['response']})
    return "Not found", 404

app.run(host='0.0.0.0', port=8080)
