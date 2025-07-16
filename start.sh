#!/bin/bash

echo "Starting tailscaled..."
/usr/sbin/tailscaled &

# Wait for tailscaled to be ready
sleep 5

echo "Authenticating with Tailscale..."
tailscale up --authkey=${TS_AUTHKEY} --hostname=flyrelay --accept-routes --reset

# Optional: wait for network to be ready
sleep 5

echo "Starting Flask app..."
python app.py
