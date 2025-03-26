#!/bin/bash

# ========================
# CONFIGURATION
# ========================

# Paths to your UERANSIM binaries
GNB_BIN="/home/ubuntu/UERANSIM/build/nr-gnb"
UE_BIN="/home/ubuntu/UERANSIM/build/nr-ue"

# Configuration files
GNB_CONFIG="/home/ubuntu/UERANSIM/config/open5gs-gnb.yaml"
UE_CONFIG="/home/ubuntu/UERANSIM/config/open5gs-ue-1.yaml"

# Duration to run (in seconds)
DURATION=60

# ========================
# START TRAFFIC CAPTURE
# ========================
sudo ../ueransim_capture.sh &

# ========================
# START GNB & UE
# ========================

echo "[*] Starting gNB..."
$GNB_BIN -c "$GNB_CONFIG" > gnb.log 2>&1 &
GNB_PID=$!

sleep 2  # Give gNB time to initialize

echo "[*] Starting UE..."
$UE_BIN -c "$UE_CONFIG" > ue.log 2>&1 &
UE_PID=$!

# ========================
# WAIT THEN KILL
# ========================

echo "[*] Running for $DURATION seconds..."
sleep "$DURATION"

echo "[*] Killing gNB (PID $GNB_PID) and UE (PID $UE_PID)..."
kill "$GNB_PID" "$UE_PID"

echo "[✓] UERANSIM gNB and UE stopped after $DURATION seconds."
