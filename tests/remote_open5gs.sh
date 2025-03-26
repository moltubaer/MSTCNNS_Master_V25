#!/bin/bash

# Remote host configuration
UERANSIM="ubuntu@10.100.51.82"
CORE="ubuntu@10.100.51.80"

CORE_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/tests/open5gs_capture.sh"
UERANSIM_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/tests/ueransim_capture.sh"
REMOTE_OUTPUT_DIR="/home/ubuntu/pcap_captures"
LOCAL_OUTPUT_DIR="/home/alexandermoltu/Documents/V25/Masterdownloaded_pcaps"

# Duration and interface (optional remote args)
DURATION=60
UERANSIM_INTERFACE="any"

# Run scripts in parallel
echo "[*] Running tcpdump script on CORE ($CORE)..."
ssh "$CORE" "bash $CORE_SCRIPT $DURATION $CORE_INTERFACE" &
PID_CORE=$!

echo "[*] Running tcpdump script on UERANSIM ($UERANSIM)..."
ssh "$UERANSIM" "bash $UERANSIM_SCRIPT $DURATION $UERANSIM_INTERFACE" &
PID_UERANSIM=$!

# Wait for both to finish
wait $PID_CORE
wait $PID_UERANSIM

# Create local dir
mkdir -p "$LOCAL_OUTPUT_DIR"

# Download the .pcap files
echo "[*] Downloading .pcap files..."
scp "$CORE:$REMOTE_OUTPUT_DIR/*.pcap" "$LOCAL_OUTPUT_DIR"
scp "$UERANSIM:$REMOTE_OUTPUT_DIR/*.pcap" "$LOCAL_OUTPUT_DIR"

echo "[✓] PCAPs downloaded to $LOCAL_OUTPUT_DIR"