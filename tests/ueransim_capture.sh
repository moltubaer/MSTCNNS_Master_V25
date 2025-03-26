#!/bin/bash

duration=${1:-60}
interface=${2:-any}
host_interface="any"
output_dir="/home/ubuntu/pcap_captures"
mkdir -p "$output_dir"

timestamp=$(date +%Y%m%d_%H%M%S)
pids=()

# Start tcpdump on host
host_capture="$output_dir/ueransim_capture_${timestamp}.pcap"
echo "[+] Starting tcpdump on host interface: $host_interface"
timeout "$duration" tcpdump -tttt -i "$host_interface" -w "$host_capture" > /dev/null 2>&1 &
pids+=($!)

# Wait for all tcpdump processes to complete
echo "[*] Waiting for the capture to complete..."
wait "${pids[@]}"
echo "[+] Capture complete."

echo "[✓] .pcap file saved to $output_dir"
