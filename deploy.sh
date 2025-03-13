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
cp "${SRC_DIR}/scripts/database/fixed_update_mysql_kol_info_v3.py" "${DEST_DIR}/scripts/database/"
cp "${SRC_DIR}/scripts/database/fixed_update_mysql_kol_tweet.py" "${DEST_DIR}/scripts/database/"

# Copy sync scripts
cp "${SRC_DIR}/scripts/sync/sync_kol_character.py" "${DEST_DIR}/scripts/sync/"
cp "${SRC_DIR}/scripts/sync/sync_to_mysql_combined.py" "${DEST_DIR}/scripts/sync/"

# Copy app files
cp -r "${SRC_DIR}/app/"* "${DEST_DIR}/app/"

# Copy test scripts
cp "${SRC_DIR}/test_mysql_connection.py" "${DEST_DIR}/"
cp "${SRC_DIR}/test_mysql_sync.py" "${DEST_DIR}/"
cp "${SRC_DIR}/update_crontab.sh" "${DEST_DIR}/"

# Set executable permissions
chmod +x "${DEST_DIR}/scripts/database/process_excel.py"
chmod +x "${DEST_DIR}/scripts/database/create_tables.py"
chmod +x "${DEST_DIR}/scripts/database/fixed_update_mysql_kol_info_v3.py"
chmod +x "${DEST_DIR}/scripts/database/fixed_update_mysql_kol_tweet.py"
chmod +x "${DEST_DIR}/scripts/sync/sync_kol_character.py"
chmod +x "${DEST_DIR}/scripts/sync/sync_to_mysql_combined.py"
chmod +x "${DEST_DIR}/test_mysql_connection.py"
chmod +x "${DEST_DIR}/test_mysql_sync.py"
chmod +x "${DEST_DIR}/update_crontab.sh"

echo "Deployment completed successfully!"
