FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    iproute2 iptables curl gnupg2 && \
    curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.gpg | gpg --dearmor -o /usr/share/keyrings/tailscale-archive-keyring.gpg && \
    curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.list | tee /etc/apt/sources.list.d/tailscale.list && \
    apt-get update && apt-get install -y tailscale && \
    apt-get clean

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Start Tailscale and your Flask app
CMD tailscaled & \
    sleep 5 && \
    tailscale up --authkey=${TS_AUTHKEY} --hostname=fly-relay && \
    python app.py

