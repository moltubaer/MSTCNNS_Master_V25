#!/bin/bash

SOURCE_REPO="~/MSTCNNS_MASTER_V25/Open5gs/config" 
DESTINATION_DIR="~/docker_open5gs/config"

CONFIG_FILES=(
  "amf.yaml"
  "smf.yaml"
  "upf.yaml"
  "nrf.yaml"
  "ausf.yaml"
  "udm.yaml"
  "udr.yaml"
  "pcf.yaml"
  "bsf.yaml"
  "nssf.yaml"
)

# Stop running Open5GS containers before updating config
echo "Stopping Open5GS Docker containers..."
docker compose -f /path/to/docker_open5gs/sa-deploy.yaml down

# Copy configuration files
echo "Copying Open5GS configuration files..."
for FILE in "${CONFIG_FILES[@]}"; do
    if [ -f "$SOURCE_REPO/$FILE" ]; then
        cp "$SOURCE_REPO/$FILE" "$DESTINATION_DIR/"
        echo "Copied: $FILE"
    else
        echo "Warning: $FILE not found in source repo!"
    fi
done

# Restart Open5GS containers
# echo "Restarting Open5GS Docker containers..."
# docker compose -f /path/to/docker_open5gs/sa-deploy.yaml up -d

echo "Migration complete!"
