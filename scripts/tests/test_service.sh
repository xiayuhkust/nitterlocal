#!/bin/bash

echo "Testing nitterlocal backend systemd service..."

# Function to check if the service is running
check_service() {
  echo "Checking service status..."
  sudo systemctl status nitterlocal-backend.service
  return $?
}

# Function to test the API endpoint
test_endpoint() {
  echo "Testing API endpoint..."
  curl -s http://43.132.129.242:8000/ | grep -q "Twitter URL ID Service"
  if [ $? -eq 0 ]; then
    echo "✅ API endpoint test passed"
    return 0
  else
    echo "❌ API endpoint test failed"
    return 1
  fi
}

# Function to test service restart
test_restart() {
  echo "Testing service restart..."
  echo "Stopping service..."
  sudo systemctl stop nitterlocal-backend.service
  sleep 2
  echo "Checking if service is stopped..."
  sudo systemctl status nitterlocal-backend.service || true
  
  echo "Starting service..."
  sudo systemctl start nitterlocal-backend.service
  sleep 5
  echo "Checking if service restarted..."
  check_service
  test_endpoint
}

# Main test sequence
echo "1. Installing service..."
sudo ./install_service.sh

echo "2. Testing service status..."
check_service

echo "3. Testing API endpoint..."
test_endpoint

echo "4. Testing service restart..."
test_restart

echo "5. Testing service logs..."
sudo journalctl -u nitterlocal-backend.service -n 20

echo "All tests completed."
