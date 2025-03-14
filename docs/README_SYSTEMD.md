# Nitterlocal Backend Systemd Service

This document explains how to install and manage the systemd service for the Nitterlocal Backend.

## Installation

To install the service, run:

```bash
sudo ./install_service.sh
```

This will:
1. Install required dependencies
2. Copy the service file to systemd
3. Enable and start the service
4. Show the initial service status

## Service Management

### Check Status

```bash
sudo systemctl status nitterlocal-backend
```

### Start Service

```bash
sudo systemctl start nitterlocal-backend
```

### Stop Service

```bash
sudo systemctl stop nitterlocal-backend
```

### Restart Service

```bash
sudo systemctl restart nitterlocal-backend
```

### View Logs

```bash
sudo journalctl -u nitterlocal-backend
```

To follow logs in real-time:

```bash
sudo journalctl -u nitterlocal-backend -f
```

### Uninstall Service

If you need to remove the service:

```bash
sudo ./uninstall_service.sh
```

## Service Configuration

The service is configured to:
- Run as the ubuntu user
- Start automatically at boot
- Restart automatically if it crashes
- Wait 10 seconds between restart attempts
- Log output to the system journal

## Service File Location

The service file is located at:
```
/etc/systemd/system/nitterlocal-backend.service
```

You can edit this file if needed, but remember to run `sudo systemctl daemon-reload` after any changes.
