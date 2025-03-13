#!/bin/bash

# Start the Twitter URL ID Service backend on the server IP
cd /home/ubuntu/repos/nitterlocal
python3 -m app.main --host 43.132.129.242 --port 8000
