from flask import Flask, request, jsonify
import requests
import os
import logging
from label_parser import try_parse_label
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Environment variables (optional, not used since API key check is disabled)
API_KEY = os.getenv("RELAY_API_KEY")
PI_ENDPOINT = os.getenv("PI_ENDPOINT")  # e.g., https://fly-io-arspzg.fly.dev/ruuvi

# --- Allowed MAC address sets (edit here later to add more) ---
ALLOWLIST_RUUVI = {
    "D1:CA:96:06:7D:D8",
    "D7:D7:47:17:D6:A9",
    "F4:F5:53:B6:BE:59",
    "FA:3F:E8:D2:DD:32",
    "DF:50:AB:DC:0E:09",
    "E7:F9:34:2B:AF:CC",
    "FE:31:94:F4:EA:23",
    "D1:AF:84:BD:6F:1E",
    "E1:5C:E7:9B:9B:58",
    # TODO: add two more later (…:97:A1 and …:A1:F5)
}

ALLOWLIST_VOC = {
    "E9:72:13:8D:ED:8C",
    "FA:EF:CB:87:37:C9",
    "DF:21:9D:E1:67:2A",
    "F3:39:CD:D0:C7:80",
    "F4:80:94:52:FA:FC",
    "E7:3E:3B:B7:31:20",
    "DF:48:CD:D3:EE:06",
    "E5:33:82:E1:A0:56",
    "D2:BB:25:60:91:9F",
    "FA:CB:FC:2D:14:D4",
    "F6:2F:4E:A6:AE:36",
    "C4:5F:55:35:D6:99",
}

# --- Pi endpoints ---
# Keep using your existing PI_ENDPOINT (typically ends with '/ruuvi')
# Derive the VOC endpoint automatically unless explicitly provided
PI_ENDPOINT_VOC = os.getenv("PI_ENDPOINT_VOC")
if not PI_ENDPOINT_VOC:
    if PI_ENDPOINT and PI_ENDPOINT.rstrip("/").endswith("/ruuvi"):
        PI_ENDPOINT_VOC = PI_ENDPOINT.rstrip("/")[:-len("/ruuvi")] + "/ingest/voc"
    else:
        # Fallback: append VOC path if PI_ENDPOINT didn't end in /ruuvi
        base = (PI_ENDPOINT or "").rstrip("/")
        PI_ENDPOINT_VOC = base + "/ingest/voc"

# --- Small helper used in Step 3 (route logic) ---
def _as_int_or_none(v):
    try:
        return None if v is None else int(v)
    except (TypeError, ValueError):
        return None




@app.route("/ruuvi", methods=["POST"])
def relay_data():
    # --- keep your header logging exactly as-is ---
    app.logger.info("Received headers: %s", dict(request.headers))

    # --- keep your existing Authorization check exactly as-is ---
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Token ") or auth_header.split(" ")[1] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or "data" not in payload:
            app.logger.warning("Invalid payload: %s", payload)
            return jsonify({"status": "ok", "ruuvi_forwarded": 0, "voc_forwarded": 0, "message": "invalid payload"}), 200

        data = payload.get("data", {})
        gw_mac = data.get("gw_mac")
        gw_ts = _as_int_or_none(data.get("timestamp"))
        tags = data.get("tags", {}) or {}

        ruuvi_allowed = {}   # MAC -> tag (original shape)
        voc_forwarded = 0

        # --- Iterate all tags from the Gateway ---
        for mac, tag in tags.items():
            # RuuviTag path: recognized by presence of 'dataFormat'
            if isinstance(tag, dict) and "dataFormat" in tag:
                if mac in ALLOWLIST_RUUVI:
                    ruuvi_allowed[mac] = tag
                else:
                    app.logger.info("RUUVI relay: disallowed MAC %s (quiet-skip)", mac)
                continue

            # VOC path: tags without dataFormat but with raw 'data' hex
            raw_hex = (tag or {}).get("data")
            if not raw_hex:
                continue

            parsed = try_parse_label(raw_hex)
            if not parsed:
                continue

            if mac not in ALLOWLIST_VOC:
                app.logger.info("VOC relay: disallowed MAC %s (quiet-skip)", mac)
                continue

            # Build compact JSON for Pi /ingest/voc (exclude rssi/phy/channel; include raw_hex)
            voc_json = {
                "gw_mac": gw_mac,
                "sensor_mac": mac,
                "timestamp": _as_int_or_none((tag or {}).get("timestamp")) or gw_ts,
                "raw_hex": raw_hex,
                # Fields that match your VocLabel table
                "temperature": parsed.get("temperature"),
                "humidity": parsed.get("humidity"),
                "pressure": parsed.get("pressure"),
                "gas_resistance": parsed.get("gas_resistance"),
                "iaq": parsed.get("iaq"),
                "co2": parsed.get("co2"),
                "voc": parsed.get("voc"),
                "sgp40_voc_index": parsed.get("sgp40_voc_index"),
                "sgp40_raw": parsed.get("sgp40_raw"),
            }

            # Post one VOC reading per device to the Pi's /ingest/voc
            if not PI_ENDPOINT_VOC:
                app.logger.warning("VOC relay: PI_ENDPOINT_VOC is not set; skipping post for %s", mac)
            else:
                try:
                    resp_v = requests.post(PI_ENDPOINT_VOC, json=voc_json, timeout=6)
                    if resp_v.status_code != 200:
                        app.logger.warning("VOC relay: Pi returned %s: %s", resp_v.status_code, resp_v.text[:200])
                    else:
                        voc_forwarded += 1
                except Exception as e:
                    app.logger.error("VOC relay: post error for %s: %s", mac, e)

        # Forward the allowed Ruuvi subset to your existing PI_ENDPOINT (/ruuvi on the Pi)
        ruuvi_forwarded = 0
        if ruuvi_allowed:
            if not PI_ENDPOINT:
                app.logger.warning("Ruuvi relay: PI_ENDPOINT is not set; skipping Ruuvi forward")
            else:
                fwd_payload = {
                    "data": {
                        "coordinates": data.get("coordinates", ""),
                        "timestamp": gw_ts,
                        "nonce": data.get("nonce"),
                        "gw_mac": gw_mac,
                        "tags": ruuvi_allowed,
                    }
                }
                try:
                    resp_r = requests.post(PI_ENDPOINT, json=fwd_payload, timeout=6)
                    if resp_r.status_code != 200:
                        app.logger.warning("Ruuvi relay: Pi returned %s: %s", resp_r.status_code, resp_r.text[:200])
                    else:
                        ruuvi_forwarded = len(ruuvi_allowed)
                except Exception as e:
                    app.logger.error("Ruuvi relay: post error: %s", e)

        return jsonify({
            "status": "forwarded",
            "ruuvi_forwarded": ruuvi_forwarded,
            "voc_forwarded": voc_forwarded
        }), 200

    except Exception as e:
        app.logger.error("Error: %s", str(e))
        return jsonify({"error": str(e)}), 500

#if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=8080)

# to try to avoid multiple fly-relay apps in Tailscale
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)

