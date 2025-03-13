#!/bin/bash

echo "=== Nitterlocal Backend Service Troubleshooting ==="
echo ""

# Check if the service file exists
echo "Checking service file..."
if [ -f "/etc/systemd/system/nitterlocal-backend.service" ]; then
  echo "✅ Service file exists"
  echo "Service file contents:"
  cat /etc/systemd/system/nitterlocal-backend.service
else
  echo "❌ Service file not found"
fi
echo ""

# Check if the working directory exists
echo "Checking working directory..."
WORKING_DIR=$(grep "WorkingDirectory" /etc/systemd/system/nitterlocal-backend.service | cut -d= -f2)
if [ -d "$WORKING_DIR" ]; then
  echo "✅ Working directory exists: $WORKING_DIR"
else
  echo "❌ Working directory not found: $WORKING_DIR"
fi
echo ""

# Check if the Python module exists
echo "Checking Python module..."
if [ -d "$WORKING_DIR/app" ] && [ -f "$WORKING_DIR/app/main.py" ]; then
  echo "✅ Python module exists"
else
  echo "❌ Python module not found"
fi
echo ""

# Check Python dependencies
echo "Checking Python dependencies..."
if [ -f "$WORKING_DIR/app/requirements.txt" ]; then
  echo "Requirements file exists. Checking dependencies..."
  pip3 list | grep -f "$WORKING_DIR/app/requirements.txt" || echo "Some dependencies may be missing"
else
  echo "❌ Requirements file not found"
fi
echo ""

# Check if the port is already in use
echo "Checking if port is in use..."
PORT=$(grep -oP "port \K[0-9]+" "$WORKING_DIR/app/main.py" | head -1)
if netstat -tuln | grep ":$PORT " > /dev/null; then
  echo "❌ Port $PORT is already in use"
else
  echo "✅ Port $PORT is available"
fi
echo ""

# Check service logs
echo "Checking service logs..."
journalctl -u nitterlocal-backend -n 20
echo ""

# Try to run the service manually
echo "Trying to run the service manually..."
cd "$WORKING_DIR"
python3 -m app.main --host 0.0.0.0 --port 8000 --test-mode
echo ""

echo "Troubleshooting completed."
