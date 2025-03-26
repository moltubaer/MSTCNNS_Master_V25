#!/bin/bash

# Remote host configuration
UERANSIM="ubuntu@10.100.51.82"
CORE="ubuntu@10.100.51.80"

CORE_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/open5gs_capture.sh"
UERANSIM_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/ueransim_capture.sh"
REMOTE_OUTPUT_DIR="/home/ubuntu/pcap_captures"
LOCAL_OUTPUT_DIR="/home/ubuntu/downloaded_pcaps"

# Duration and interface (optional remote args)
DURATION=60
UERANSIM_INTERFACE="any"
CORE_INTERFACE=""   # Open5GS has randomized bridge interface name

# Run the script on core
echo "[*] Running tcpdump script on $CORE..."
ssh "$CORE" "bash $CORE_SCRIPT $DURATION $INTERFACE"

# Run the script on ueransim
echo "[*] Running tcpdump script on $UERANSIM..."
ssh "$UERANSIM" "bash $CORE_SCRIPT $DURATION $UERANSIM_INTERFACE"

# Create local dir
mkdir -p "$"

# Download the .pLOCAL_OUTPUT_DIRcap files
echo "[*] Downloading .pcap files..."
scp "$CORE:$REMOTE_OUTPUT_DIR/*.pcap" "$LOCAL_OUTPUT_DIR"
scp "$UERANSIM:$REMOTE_OUTPUT_DIR/*.pcap" "$LOCAL_OUTPUT_DIR"

echo "[✓] PCAPs downloaded to $LOCAL_OUTPUT_DIR"
