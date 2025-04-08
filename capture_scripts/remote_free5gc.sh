#!/bin/bash

# ========================
# CONFIGURATION
# ========================

core1="ubuntu@10.100.51.80"
# core2="ubuntu@10.100.51.81"
ueransim="ubuntu@10.100.51.82"

core1_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/free5gc_capture.sh"
ueransim_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh"
# ueransim_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/control_plane_tests/single_ue_reg.sh"

# ========================
# EXECUTE REMOTE SCRIPTS
# ========================

echo "[*] Running script on $core1..."
ssh -tt "$core1" "sudo bash $core1_script" &
PID1=$!

echo "[*] Running script on $ueransim..."
ssh -tt "$ueransim" "sudo bash $ueransim_script" &
PID2=$!

# ========================
# WAIT FOR BOTH TO FINISH
# ========================

wait $PID1
wait $PID2

echo "[✓] Both remote scripts completed."

# # Create local dir
# mkdir -p "$LOCAL_OUTPUT_DIR"

# # Download the .pcap files
# echo "[*] Downloading .pcap files..."
# scp "$CORE:$REMOTE_OUTPUT_DIR/*.pcap" "$LOCAL_OUTPUT_DIR"
# scp "$UERANSIM:$REMOTE_OUTPUT_DIR/*.pcap" "$LOCAL_OUTPUT_DIR"

# echo "[✓] PCAPs downloaded to $LOCAL_OUTPUT_DIR"