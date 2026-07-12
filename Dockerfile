FROM node:20-bookworm-slim

USER root

# Install Python3, pip, and build tools using apt-get
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them globally
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt --break-system-packages

# Install n8n globally
RUN npm install -g n8n --omit=dev

# Switch back to node user
USER node

# Expose n8n default port
EXPOSE 5678

# Set execution command
CMD ["n8n", "start"]
