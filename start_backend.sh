#!/bin/bash

# Start the Twitter URL ID Service backend on the server IP
cd /home/ubuntu/repos/nitterlocal
python3 -m app.main --host 127.0.0.1 --port 8000
