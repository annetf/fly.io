FROM debian:bookworm-slim

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    iproute2 iptables curl gnupg2 ca-certificates lsb-release

# Add Tailscale repository and GPG key
RUN curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.gpg | tee /usr/share/keyrings/tailscale-archive-keyring.gpg > /dev/null && \
    curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.list | tee /etc/apt/sources.list.d/tailscale.list > /dev/null

# Install Tailscale
RUN apt-get update && apt-get install -y tailscale && apt-get clean

WORKDIR /app
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

# Start Tailscale and the Flask app
CMD bash -c "tailscaled & sleep 5 && tailscale up --authkey=${TS_AUTHKEY} --hostname=fly-relay && python3 app.py"
