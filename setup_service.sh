#!/bin/bash

# Define variables
USER="pi"
PROJECT_DIR="/home/$USER/CSR_PROJECT"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python3"
SERVICE_FILE="/etc/systemd/system/photoframe.service"

echo "🔧 Setting up photoframe.service..."

# Create service file content
cat <<EOF | sudo tee $SERVICE_FILE
[Unit]
Description=Digital Photo Frame Web Server
After=network.target

[Service]
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PYTHON app.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "📄 Service file created at $SERVICE_FILE"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service
echo "✅ Enabling photoframe.service..."
sudo systemctl enable photoframe.service

# Start service
echo "🚀 Starting photoframe.service..."
sudo systemctl restart photoframe.service

# Check status
echo "📊 Checking status..."
sleep 2
sudo systemctl status photoframe.service --no-pager

echo "🎉 Setup Complete! Access at http://raspberrypi.local:8080"
