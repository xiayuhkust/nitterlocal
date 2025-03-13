#!/bin/bash

echo "=== Nitterlocal Backend Service Fix Script ==="
echo ""

# Update the service file to use the correct path
echo "Updating service file with correct paths..."
CURRENT_DIR=$(pwd)
sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$CURRENT_DIR|g" /etc/systemd/system/nitterlocal-backend.service
echo "✅ Updated working directory to: $CURRENT_DIR"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r app/requirements.txt
echo "✅ Dependencies installed"

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload
echo "✅ Systemd reloaded"

# Restart service
echo "Restarting service..."
sudo systemctl restart nitterlocal-backend
echo "✅ Service restarted"

# Check service status
echo "Checking service status..."
sudo systemctl status nitterlocal-backend
echo ""

echo "Fix completed. If the service is still not working, please check the logs with:"
echo "sudo journalctl -u nitterlocal-backend -n 50"
