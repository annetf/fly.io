FROM debian:bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    iproute2 iptables curl gnupg2 ca-certificates lsb-release dirmngr

# Add Tailscale GPG key and repository
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 458CA832957F5868 && \
    curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.list | tee /etc/apt/sources.list.d/tailscale.list

# Install Tailscale
RUN apt-get update && apt-get install -y tailscale && apt-get clean

WORKDIR /app
COPY . .

# Create and activate virtual environment, then install Python packages
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Start Tailscale and the Flask app using the virtual environment
#CMD bash -c "tailscaled & sleep 5 && tailscale up --authkey=${TS_AUTHKEY} --hostname=fly-relay && /app/venv/bin/python app.py"

# to avoid repeated instances of the fly-relay on Tailscale, replaced the last line above with a short retry loop:
# Start tailscaled, try 'tailscale up' for ~2 minutes, then start Flask
CMD bash -lc 'tailscaled & \
  for i in {1..60}; do \
    tailscale up --authkey="$TS_AUTHKEY" --hostname=fly-relay --advertise-tags=tag:fly-relay && break; \
    echo "tailscale up failed, retrying in 2s..."; sleep 2; \
  done; \
  exec /app/venv/bin/python app.py'
