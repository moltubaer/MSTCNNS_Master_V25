#!/bin/bash

# ========================
# CONFIGURATION
# ========================

# List of Open5GS containers to capture from
containers=("open5gs_amf" "open5gs_smf" "open5gs_upf")

# Interface inside the containers (use "any" to capture all)
interface="any"

# Capture duration in seconds
duration=60

# Host output directory for collected pcaps
timestamp=$(date +%Y%m%d_%H%M%S)
host_output_dir="$HOME/pcap_captures/$timestamp"
mkdir -p "$host_output_dir"

# ========================
# CAPTURE FUNCTION
# ========================

echo "[*] Starting tcpdump in containers..."

for container in "${containers[@]}"; do
    echo "  [+] $container capturing on interface '$interface' for $duration seconds"
    
    docker exec "$container" \
        sh -c "timeout $duration tcpdump -i $interface -w /tmp/${container}_capture.pcap" &
done

# Wait for all background captures to finish
wait
echo "[*] All tcpdump processes completed."

# ========================
# COPY PCAPS TO HOST
# ========================

echo "[*] Copying .pcap files to host: $host_output_dir"

for container in "${containers[@]}"; do
    src_path="/tmp/${container}_capture.pcap"
    dest_path="$host_output_dir/${container}_capture.pcap"

    echo "  [+] Copying from $container:$src_path"
    docker cp "$container:$src_path" "$dest_path"

    # Clean up inside the container
    docker exec "$container" rm -f "$src_path"
done

echo "[✓] PCAP collection complete: $host_output_dir"
