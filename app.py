from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("RELAY_API_KEY")
PI_ENDPOINT = os.getenv("PI_ENDPOINT")  # e.g., http://raspberrypi.tail37fbde.ts.net:5000/ruuvi


@app.route("/ruuvi", methods=["POST"])
def relay_data():
    received_key = request.headers.get("X-API-Key")
    
    # Debugging output
    print("Expected API key:", API_KEY)
    print("Received API key:", received_key)

    if received_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        response = requests.post(PI_ENDPOINT, json=request.get_json())
        return jsonify({"status": "forwarded", "pi_response": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500



#@app.route("/ruuvi", methods=["POST"])
#def relay_data():
#    if request.headers.get("X-API-Key") != API_KEY:
#        return jsonify({"error": "Unauthorized"}), 401
#
#    try:
#        response = requests.post(PI_ENDPOINT, json=request.get_json())
#        return jsonify({"status": "forwarded", "pi_response": response.text}), response.status_code
#    except Exception as e:
#        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
