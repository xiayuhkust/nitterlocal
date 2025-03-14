# Backend Service Accessibility Guide

## Overview
This document explains how to access the backend service for the Twitter URL ID Service and troubleshoot common connectivity issues.

## Current Configuration
The backend service is configured to run as a systemd service on the server with the following details:
- Service name: `nitterlocal-backend`
- Binding address: `0.0.0.0:8000` (all interfaces)
- Working directory: `/home/ubuntu/nitterlocal`

## Accessing the Service
The service should be accessible at:
- Local access: `http://localhost:8000/`
- Remote access: Use the server's actual IP address or hostname

### Important Note About IP Address
The IP address `43.132.129.242` mentioned in the documentation may not be accessible from all networks. This could be due to:
1. Network connectivity issues between your environment and the server
2. Firewall rules blocking access to port 8000
3. The server having a different public IP address than expected

## Troubleshooting Steps
If you cannot access the backend service, try the following:

1. **Verify the service is running**:
   ```bash
   sudo systemctl status nitterlocal-backend
   ```

2. **Check if the service is binding to the correct port**:
   ```bash
   ss -tulpn | grep 8000
   ```

3. **Test local connectivity**:
   ```bash
   curl -v http://localhost:8000/
   ```

4. **Check firewall settings**:
   ```bash
   sudo iptables -L -n | grep 8000
   ```

5. **Verify the server's actual IP address**:
   ```bash
   hostname -I
   ```

6. **Restart the service if needed**:
   ```bash
   sudo systemctl restart nitterlocal-backend
   ```

## Using the Direct Sync Feature
The backend service now supports direct synchronization without requiring file upload:

1. Access the web interface at `http://[server-ip]:8000/`
2. Click the "同步到MySQL" button without uploading a file first
3. This will directly synchronize the local SQLite database with MySQL

## Service Logs
To view the service logs for debugging:
```bash
sudo journalctl -u nitterlocal-backend -n 100
```
