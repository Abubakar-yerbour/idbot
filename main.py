from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

# In-memory storage for commands and outputs
commands = {}
outputs = {}
lock = Lock()

@app.route("/get_command/<device_id>", methods=["GET"])
def get_command(device_id):
    with lock:
        command = commands.pop(device_id, None)
    if command:
        return jsonify(command)
    else:
        return jsonify({})

@app.route("/post_output", methods=["POST"])
def post_output():
    data = request.get_json()
    device_id = data.get("device_id")
    output = data.get("output")
    if device_id and output:
        with lock:
            outputs[device_id] = output
        return jsonify({"status": "success"})
    return jsonify({"status": "failure"}), 400

@app.route("/send_command", methods=["POST"])
def send_command():
    data = request.get_json()
    device_id = data.get("device_id")
    command = data.get("command")
    args = data.get("args", "")
    if device_id and command:
        with lock:
            commands[device_id] = {"command": command, "args": args}
        return jsonify({"status": "command sent"})
    return jsonify({"status": "failure"}), 400

@app.route("/get_output/<device_id>", methods=["GET"])
def get_output(device_id):
    with lock:
        output = outputs.pop(device_id, "")
    return jsonify({"output": output})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
