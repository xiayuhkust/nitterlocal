#!/bin/bash

# Uninstall the systemd service for nitterlocal backend
# This script must be run with sudo privileges

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo"
  exit 1
fi

# Stop and disable the service
echo "Stopping and disabling service..."
systemctl stop nitterlocal-backend
systemctl disable nitterlocal-backend

# Remove the service file
echo "Removing service file..."
rm -f /etc/systemd/system/nitterlocal-backend.service

# Reload systemd
systemctl daemon-reload

echo "Service uninstalled successfully"
