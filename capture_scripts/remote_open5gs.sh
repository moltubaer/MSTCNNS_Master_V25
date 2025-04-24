#!/bin/bash

# ========================
# CONFIGURATION
# ========================

core1="ubuntu@10.100.51.80"
# core2="ubuntu@10.100.51.81"
ueransim="ubuntu@10.100.51.82"

system_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py"
core1_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/open5gs_capture.sh"
ueransim_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh"
# ueransim_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/control_plane_tests/single_ue_reg.sh"

# Default duration
DURATION=120

# Parse optional arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --duration)
      DURATION="$2"
      shift 2
      ;;
    *)
      echo "❌ Unknown argument: $1"
      exit 1
      ;;
  esac
done

# ========================
# EXECUTE REMOTE SCRIPTS
# ========================

echo "[*] Running script on $core1..."
# ssh -tt "$core1" "sudo bash $core1_script $DURATION && python3 $system_script -d $DURATION" &
ssh -tt "$core1" "sudo bash $core1_script $DURATION" &
ssh -tt "$core1" "python3 $system_script -d $DURATION" &
PID1=$!

echo "[*] Running script on $ueransim..."
# ssh -tt "$ueransim" "sudo bash $ueransim_script $DURATION && python3 $system_script -d $DURATION" &
ssh -tt "$ueransim" "sudo bash $ueransim_script $DURATION" &
ssh -tt "$ueransim" "python3 $system_script -d $DURATION" &
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