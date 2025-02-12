#!/bin/bash

SOURCE_REPO="/home/ubuntu/MSTCNNS_Master_V25/UERANSIM/config"
DESTINATION_DIR="/home/ubuntu/UERANSIM/config"

# List of configuration files to migrate
CONFIG_FILES=(
  "open5gs-gnb.yaml"
  "open5gs-ue.yaml"
)

echo "🔍 Verifying Source Directory: $SOURCE_REPO"
if [ ! -d "$SOURCE_REPO" ]; then
    echo "❌ ERROR: Source directory does not exist! Check SOURCE_REPO path."
    exit 1
fi

# Stop any running UERANSIM instances before updating config
echo "🛑 Stopping UERANSIM processes..."
pkill -f nr-gnb
pkill -f nr-ue

# Copy configuration files to their respective locations
echo "📂 Copying UERANSIM configuration files..."
for FILE in "${CONFIG_FILES[@]}"; do
    SRC_FILE="$SOURCE_REPO/$FILE"
    DEST_FILE="$DESTINATION_DIR/$FILE"
    
    echo "🔎 Checking: $SRC_FILE"
    
    if [ -f "$SRC_FILE" ]; then
        cp "$SRC_FILE" "$DEST_FILE"
        echo "✅ Copied: $FILE -> $DEST_FILE"
    else
        echo "❌ ERROR: $FILE not found in $SOURCE_REPO"
    fi
done

# Restart UERANSIM components
echo "🔄 Restarting UERANSIM gNB and UE..."
cd "$DESTINATION_DIR"

# Start gNB
echo "🚀 Starting gNB..."
nohup ./build/nr-gnb -c config/gnb.yaml > gnb.log 2>&1 &

# Start UE
echo "🚀 Starting UE..."
nohup ./build/nr-ue -c config/ue.yaml > ue.log 2>&1 &

echo "✅ UERANSIM Configuration Migration Complete!"
