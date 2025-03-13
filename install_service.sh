#!/bin/bash

# Install the systemd service for nitterlocal backend
# This script must be run with sudo privileges

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo"
  exit 1
fi

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Install dependencies if not already installed
if [ ! -f "/tmp/backend_deps_installed" ]; then
  echo "Installing backend dependencies..."
  ./install_backend_deps.sh
  touch /tmp/backend_deps_installed
fi

# Copy the service file to systemd directory
echo "Installing systemd service..."
cp nitterlocal-backend.service /etc/systemd/system/

# Reload systemd to recognize the new service
systemctl daemon-reload

# Enable and start the service
systemctl enable nitterlocal-backend
systemctl start nitterlocal-backend

# Check service status
echo "Service status:"
systemctl status nitterlocal-backend

echo ""
echo "Installation complete!"
echo "You can manage the service with these commands:"
echo "  sudo systemctl start nitterlocal-backend    # Start the service"
echo "  sudo systemctl stop nitterlocal-backend     # Stop the service"
echo "  sudo systemctl restart nitterlocal-backend  # Restart the service"
echo "  sudo systemctl status nitterlocal-backend   # Check service status"
echo "  sudo journalctl -u nitterlocal-backend      # View service logs"
