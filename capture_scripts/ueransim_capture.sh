#!/bin/bash

duration=${1:-120}  # default to 120 seconds if not provided
host_interface="any"
output_dir="/home/ubuntu/pcap_captures"
mkdir -p "$output_dir"

timestamp=$(date +%Y.%m.%d_%H.%M.%S)
pids=()

# Start metrics capture in background for 120 seconds
python3 /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py --duration 120 &

# Start tcpdump on host
host_capture="$output_dir/ueransim_capture_${timestamp}.pcap"
echo "[+] Starting tcpdump on host interface: $host_interface"
timeout "$duration" tcpdump -tttt -i "$host_interface" -w "$host_capture" > /dev/null 2>&1 &
pids+=($!)

# Wait for all tcpdump processes to complete
echo "[*] Waiting for the capture to complete..."
wait "${pids[@]}"
echo "[+] Capture complete."

echo "[*] Changing ownership of output directory and files to ubuntu:ubuntu"
sudo chown -R ubuntu:ubuntu "$output_dir"

echo "[✓] .pcap file saved to $output_dir"
