#!/bin/bash
echo "Starting MD Simulation Dashboard..."
# Navigate to the script's directory dynamically
cd "$(dirname "$0")"
python3 server.py
