from flask import Flask, request, jsonify
import requests
import os
import logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Environment variables (optional, not used since API key check is disabled)
API_KEY = os.getenv("RELAY_API_KEY")
PI_ENDPOINT = os.getenv("PI_ENDPOINT")  # e.g., https://fly-io-arspzg.fly.dev/ruuvi

@app.route("/ruuvi", methods=["POST"])
def relay_data():
    app.logger.info("Received headers: %s", dict(request.headers))  # for debugging Print all incoming headers

    # API key check using 'Authorization: Token ...'
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Token ") or auth_header.split(" ")[1] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        app.logger.info("Forwarding data to Raspberry Pi: %s", data)  # Debug payload

        response = requests.post(PI_ENDPOINT, json=data)
        return jsonify({"status": "forwarded", "pi_response": response.text}), response.status_code

    except Exception as e:
        app.logger.error("Error: %s", str(e))  # Optional: log error
        return jsonify({"error": str(e)}), 500

#if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=8080)

# to try to avoid multiple fly-relay apps in Tailscale
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
