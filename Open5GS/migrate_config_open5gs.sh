#!/bin/bash

SOURCE_REPO="./config" 
DESTINATION_DIR="../docker_open5gs"

# Mapping of configuration files to correct subdirectories
declare -A CONFIG_MAP
CONFIG_MAP=(
  ["amf.yaml"]="amf/amf.yaml"
  ["smf.yaml"]="smf/smf.yaml"
  ["upf.yaml"]="upf/upf.yaml"
  ["nrf.yaml"]="nrf/nrf.yaml"
  ["ausf.yaml"]="ausf/ausf.yaml"
  ["udm.yaml"]="udm/udm.yaml"
  ["udr.yaml"]="udr/udr.yaml"
  ["pcf.yaml"]="pcf/pcf.yaml"
  ["bsf.yaml"]="bsf/bsf.yaml"
  ["nssf.yaml"]="nssf/nssf.yaml"
)

# Stop running Open5GS containers before updating config
echo "Stopping Open5GS Docker containers..."
# docker compose -f "$DESTINATION_DIR/sa-deploy.yaml" down

# Copy configuration files to their respective locations
echo "Copying Open5GS configuration files..."
for FILE in "${!CONFIG_MAP[@]}"; do
    SRC_FILE="$SOURCE_REPO/$FILE"
    DEST_FILE="$DESTINATION_DIR/${CONFIG_MAP[$FILE]}"
    
    if [ -f "$SRC_FILE" ]; then
        cp "$SRC_FILE" "$DEST_FILE"
        echo "Copied: $FILE -> $DEST_FILE"
    else
        echo "Warning: $FILE not found in source repo!"
    fi
done

# Restart Open5GS containers
echo "Restarting Open5GS Docker containers..."
# docker compose -f "$DESTINATION_DIR/sa-deploy.yaml" up -d

echo "Migration complete!"