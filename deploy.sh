#!/bin/bash

# Script to deploy updated files to the correct location

# Source and destination directories
SRC_DIR="/home/ubuntu/repos/nitterlocal"
DEST_DIR="/home/ubuntu/nitterlocal"

# Create necessary directories
mkdir -p "${DEST_DIR}/scripts/database"
mkdir -p "${DEST_DIR}/scripts/sync"
mkdir -p "${DEST_DIR}/app"
mkdir -p "${DEST_DIR}/app/static"

# Copy database processing scripts
cp "${SRC_DIR}/scripts/database/process_excel.py" "${DEST_DIR}/scripts/database/"
cp "${SRC_DIR}/scripts/database/create_tables.py" "${DEST_DIR}/scripts/database/"

# Copy sync scripts
cp "${SRC_DIR}/scripts/sync/sync_kol_character.py" "${DEST_DIR}/scripts/sync/"

# Copy app files
cp -r "${SRC_DIR}/app/"* "${DEST_DIR}/app/"

# Set executable permissions
chmod +x "${DEST_DIR}/scripts/database/process_excel.py"
chmod +x "${DEST_DIR}/scripts/database/create_tables.py"
chmod +x "${DEST_DIR}/scripts/sync/sync_kol_character.py"

echo "Deployment completed successfully!"
