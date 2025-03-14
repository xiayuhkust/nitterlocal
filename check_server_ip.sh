#!/bin/bash

# Script to check server IP and connectivity

echo "Checking server IP and connectivity..."
echo "======================================"

# Get server IP addresses
echo "Server IP addresses:"
hostname -I

# Check if the service is running
echo -e "\nChecking if the backend service is running..."
sudo systemctl status nitterlocal-backend | grep Active

# Check if the service is binding to port 8000
echo -e "\nChecking if the service is binding to port 8000..."
ss -tulpn | grep 8000 || echo "Port 8000 not in use"

# Check local connectivity
echo -e "\nTesting local connectivity..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/ || echo "Cannot connect to localhost:8000"

# Check firewall settings
echo -e "\nChecking firewall settings for port 8000..."
sudo iptables -L -n | grep 8000 || echo "No iptables rules found for port 8000"

# Get public IP address
echo -e "\nAttempting to get public IP address..."
curl -s https://api.ipify.org || echo "Could not determine public IP"

echo -e "\nConnectivity check completed."
echo "If you cannot access the service remotely, please ensure you are using the correct IP address."
echo "The service is configured to bind to 0.0.0.0:8000, which means it should be accessible from all network interfaces."
