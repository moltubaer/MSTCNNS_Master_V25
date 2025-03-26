#!/bin/bash

duration=${1:-60}
host_interface="br-#########"  # CHANGE TO CORRECT BRIDGE INT
output_dir="./pcap_captures"
mkdir -p "$output_dir"

containers=("open5gs_amf" "open5gs_smf" "open5gs_upf")
timestamp=$(date +%Y%m%d_%H%M%S)
pids=()

# Start tcpdump on host
host_capture="$output_dir/host_capture_${timestamp}.pcap"
echo "[+] Starting tcpdump on host interface: $host_interface"
timeout "$duration" tcpdump -i "$host_interface" -w "$host_capture" > /dev/null 2>&1 &
pids+=($!)

# Start tcpdump in containers
for container in "${containers[@]}"; do
    echo "[+] Starting tcpdump in container $container..."
    docker exec "$container" timeout "$duration" tcpdump -tttt -i "$interface" -w "/tmp/${container}_capture.pcap" > /dev/null 2>&1 &
    pids+=($!)
done

# Wait for all tcpdump processes to complete
echo "[*] Waiting for all captures to complete..."
wait "${pids[@]}"
echo "[+] Captures complete."

# Copy container pcap files to host directory
for container in "${containers[@]}"; do
    file="${container}_capture_${timestamp}.pcap"
    docker cp "$container:/tmp/${container}_capture.pcap" "$output_dir/$file"
    docker exec "$container" rm -f "/tmp/${container}_capture.pcap"
done

echo "[✓] All .pcap files saved to $output_dir"
