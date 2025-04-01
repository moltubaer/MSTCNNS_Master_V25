#!/bin/bash

# === CONFIGURATION ===
CORE1_HOST="ubuntu@core1"           # Change to your core1 VM SSH address
UERANSIM_HOST="ubuntu@ueransim"     # Change to your UERANSIM VM SSH address
REMOTE_DIR="/home/ubuntu/pcap_captures"
LOCAL_DEST="$HOME/Downloads/pcap_captures"  # Change this if you want

mkdir -p "$LOCAL_DEST"

echo "📥 Fetching latest capture from core1..."
latest_dir=$(ssh "$CORE1_HOST" "ls -td $REMOTE_DIR/*/ | head -n 1")
scp -r "$CORE1_HOST:${latest_dir}" "$LOCAL_DEST/core1_latest/"

echo "📥 Fetching latest capture from ueransim..."
latest_file=$(ssh "$UERANSIM_HOST" "ls -t $REMOTE_DIR/*.pcap | head -n 1")
scp "$UERANSIM_HOST:$latest_file" "$LOCAL_DEST/ueransim_latest.pcap"

echo "✅ All latest PCAPs fetched to: $LOCAL_DEST"
