#!/bin/bash

# ========================
# CONFIGURATION
# ========================

# Paths to your UERANSIM binaries
UERANSIM_Path="/home/ubuntu/UERANSIM"

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
timeout "$DURATION" $UERANSIM_Path/build/nr-gnb -c config/open5gs-gnb.yaml > gnb.log 2>&1 &
GNB_PID=$!

sleep 2  # Give gNB time to initialize

echo "[*] Starting UE..."
timeout "$DURATION" $UERANSIM_Path/build/nr-ue -c config/open5gs-ue-1.yaml -n 2 > ue.log 2>&1 &
UE_PID=$!

# ========================
# WAIT THEN KILL
# ========================

echo "[*] Running for $DURATION seconds..."
sleep "$DURATION"
wait "$GNB_PID" "$UE_PID"

echo "[✓] UERANSIM gNB and UE stopped after $DURATION seconds."
