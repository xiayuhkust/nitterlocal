#!/bin/bash

# Script to check server connectivity and backend service status

echo "Checking server connectivity and backend service status..."
echo "========================================================="

# Check if the service is running
echo "Checking if the service is running..."
sudo systemctl status nitterlocal-backend | grep Active

# Check if the service is binding to the correct port
echo -e "\nChecking if the service is binding to port 8000..."
ss -tulpn | grep 8000 || echo "Port 8000 not in use"

# Check local connectivity
echo -e "\nTesting local connectivity..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "Cannot connect to localhost:8000"

# Get the server's IP address
echo -e "\nServer IP addresses:"
hostname -I

# Check firewall settings
echo -e "\nChecking firewall settings for port 8000..."
sudo iptables -L -n | grep 8000 || echo "No iptables rules found for port 8000"

echo -e "\nConnectivity check completed."
echo "If you cannot access the service remotely, please ensure you are using the correct IP address."
echo "The service is configured to bind to 0.0.0.0:8000, which means it should be accessible from all network interfaces."
