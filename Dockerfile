FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl iptables iproute2 dnsutils gnupg bash \
    && rm -rf /var/lib/apt/lists/*

# Install Tailscale
RUN curl -fsSL https://pkgs.tailscale.com/stable/tailscale_1.66.4_amd64.tgz | tar -xz && \
    mv tailscale*/tailscale tailscale*/tailscaled /usr/sbin/

# Set working directory
WORKDIR /app

# Copy app files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Start the app via the script
CMD ["bash", "/start.sh"]

