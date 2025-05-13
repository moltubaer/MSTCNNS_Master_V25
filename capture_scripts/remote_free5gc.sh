#!/bin/bash

# ========================
# CONFIGURATION
# ========================

core1="ubuntu@10.100.51.80"
# core2="ubuntu@10.100.51.81"
ueransim="ubuntu@10.100.51.82"

system_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py"
core1_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/free5gc_capture.sh"
ueransim_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh"

# # Default value if not specified
# DURATION=${1:-5}

# echo "Duration is $DURATION"

# Default values
duration=5
ue_count=100

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --duration)
            duration="$2"
            shift 2
            ;;
        --ue-count)
            ue_count="$2"
            shift 2
            ;;
        *)
            echo "❌ Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Validate UE count
if ! [[ "$ue_count" =~ ^[0-9]+$ ]]; then
    echo "remote [ERROR] Invalid UE count: $ue_count. It must be a positive integer."
    exit 1
fi

echo "[*] Capture duration set to $duration seconds."
echo "[*] UE count set to $ue_count."

# ========================
# EXECUTE REMOTE SCRIPTS
# ========================

echo "[*] Running script on $core1..."
ssh -tt "$core1" "sudo bash $core1_script --duration $duration --ue-count $ue_count" &
ssh -tt "$core1" "sudo python3 $system_script -d $duration" &
PID1=$!

echo "[*] Running script on $ueransim..."
ssh -tt "$ueransim" "sudo bash $ueransim_script --duration $duration --ue-count $ue_count --core free5gc" &
ssh -tt "$ueransim" "sudo python3 $system_script -d $duration" &
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