#!/bin/bash

# ========================
# CONFIGURATION
# ========================

# List of Open5GS containers to capture from
containers=("open5gs_amf" "open5gs_smf" "open5gs_upf")

# Interface inside the containers (use "any" to capture all)
container_interface="any"

# Interface on the host OS to capture from (e.g., eth0, br-xxxx)
host_interface="br-1234567890ab"  # <-- CHANGE this to match your setup

# Capture duration in seconds
duration=60

# Host output directory for collected pcaps
timestamp=$(date +%Y%m%d_%H%M%S)
host_output_dir="/home/ubuntu/pcap_captures/$timestamp"
mkdir -p "$host_output_dir"

# ========================
# HOST OS CAPTURE
# ========================

echo "[*] Starting tcpdump on host interface: $host_interface"

host_pcap_path="$host_output_dir/host_capture.pcap"
sudo timeout "$duration" tcpdump -i "$host_interface" -w "$host_pcap_path" > /dev/null 2>&1 &
host_pid=$!

# ========================
# CONTAINER CAPTURES
# ========================

echo "[*] Starting tcpdump in containers..."

container_pids=()

for container in "${containers[@]}"; do
    echo "  [+] $container capturing on interface '$container_interface' for $duration seconds"

    docker exec "$container" \
        sh -c "timeout $duration tcpdump -i $container_interface -w /tmp/${container}_capture.pcap" > /dev/null 2>&1 &

    container_pids+=($!)
done

# ========================
# WAIT FOR ALL CAPTURES
# ========================

echo "[*] Waiting for all tcpdump processes to complete..."
wait "${container_pids[@]}"
wait "$host_pid"
echo "[*] All tcpdump processes completed."

# ========================
# COPY PCAPS TO HOST DIR
# ========================

echo "[*] Copying container .pcap files to host: $host_output_dir"

for container in "${containers[@]}"; do
    src_path="/tmp/${container}_capture.pcap"
    dest_path="$host_output_dir/${container}_capture.pcap"

    echo "  [+] Copying from $container:$src_path"
    docker cp "$container:$src_path" "$dest_path"

    # Clean up inside the container
    docker exec "$container" rm -f "$src_path"
done

echo "[✓] PCAP collection complete: $host_output_dir"
