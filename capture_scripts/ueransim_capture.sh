#!/bin/bash

# ===
# Argument Parsing
# ===

# Default to 5 seconds if not provided
# duration=${1:-5}

# Default values
duration=5
ue_count=1
mode=""
test_script=""
core=""

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
        --mode)
            mode="$2"
            shift 2
            ;;
        --test)
            test_script="$2"
            shift 2
            ;;
        --core)
            core="$2"
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
    echo "ueransim [ERROR] Invalid UE count: $ue_count. It must be a positive integer."
    exit 1
fi

echo "[*] Capture duration set to $duration seconds."
echo "[*] UE count set to $ue_count."
echo "[*] Mode set to $mode."
echo "[*] Test script set to $test_script."

# ===
# CONFIGURATION
# ===

host_interface="enp2s0"

timestamp=$(date +%Y.%m.%d_%H.%M)
output_dir="/home/ubuntu/pcap_captures/${ue_count}_UEs_ueransim_${core}_${test_script}_${mode}_${timestamp}"
mkdir -p "$output_dir"

pids=()

# ===
# START CAPTURE
# ===

# Start metrics capture in the background
echo "[*] Starting metrics capture for $duration seconds..."
python3 /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py --duration "$duration" &

# Start tcpdump on host
host_capture="$output_dir/${ue_count}_${mode}_${test_script}_ueransim_capture.pcap"
echo "[+] Starting tcpdump on host interface: $host_interface"
sudo timeout "$duration" tcpdump -tttt -i "$host_interface" -w "$host_capture" > "$output_dir/ueransim_tcpdump.log" 2>&1 &
pids+=($!)

# ===
# WAIT FOR CAPTURE TO COMPLETE
# ===

echo "[*] Waiting for the capture to complete..."
wait "${pids[@]}"
echo "[+] Capture complete."

# ===
# POST-CAPTURE TASKS
# ===

# echo "[*] Changing ownership of output directory and files to ubuntu:ubuntu"
sudo chown -R ubuntu:ubuntu "$output_dir"

echo "[✓] .pcap file saved to $host_capture"
