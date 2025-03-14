#!/bin/bash

echo "=== MOCK SYSTEMD INSTALLATION ==="
echo "This is a mock test of the systemd service installation"
echo "In a real environment with sudo access, the service would be installed with:"
echo "sudo ./install_service.sh"
echo ""

echo "=== SERVICE FILE CONTENTS ==="
cat nitterlocal-backend.service
echo ""

echo "=== TESTING SERVICE FUNCTIONALITY ==="
# Start the backend service in the background
python3 -m app.main --host 0.0.0.0 --port 8000 &
PID=$!
echo "Started backend service with PID: $PID"

# Wait for service to start
sleep 5
echo "Testing health endpoint..."
curl -s http://localhost:8000/health
echo ""

# Test service restart
echo "Simulating service crash..."
kill $PID
echo "Service stopped"

# Restart service (simulating systemd restart)
echo "Simulating systemd automatic restart..."
python3 -m app.main --host 0.0.0.0 --port 8000 &
PID=$!
echo "Restarted backend service with PID: $PID"

# Wait for service to restart
sleep 5
echo "Testing health endpoint after restart..."
curl -s http://localhost:8000/health
echo ""

# Cleanup
echo "Cleaning up test processes..."
kill $PID
echo "Test completed successfully"
