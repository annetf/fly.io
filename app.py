from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Environment variables (optional, not used since API key check is disabled)
API_KEY = os.getenv("RELAY_API_KEY")
PI_ENDPOINT = os.getenv("PI_ENDPOINT")  # e.g., https://fly-io-arspzg.fly.dev/ruuvi

@app.route("/ruuvi", methods=["POST"])
def relay_data():
    print("Received headers:", dict(request.headers))  # for debugging Print all incoming headers

    # API key check is disabled for testing
    #if request.headers.get("X-API-Key") != API_KEY:
    #    return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        print("Forwarding data to Raspberry Pi:", data)  # Debug payload

        response = requests.post(PI_ENDPOINT, json=data)
        return jsonify({"status": "forwarded", "pi_response": response.text}), response.status_code

    except Exception as e:
        print("Error:", str(e))  # Optional: log error
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
