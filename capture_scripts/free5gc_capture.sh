#!/bin/bash

# ========================
# CONFIGURATION
# ========================

# List of Free5gc containers to capture from
containers=("free5gc_amf" "free5gc_smf" "free5gc_upf" "free5gc_udm" "free5gc_ausf" "free5gc_pcf" "free5gc_nssf" "free5gc_udr" "free5gc_nrf")

container_interface="any"
host_interface="any"

# === Argument Parsing ===
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
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

# Default to 120 seconds if not provided
duration=${DURATION:-120}

echo "ueransim_capture.sh"
echo "Duration: $duration"

# Host output directory for collected pcaps
timestamp=$(date +%Y.%m.%d_%H.%M.%S)
host_output_dir="/home/ubuntu/pcap_captures/free5gc-$timestamp"
mkdir -p "$host_output_dir"

# ========================
# HOST OS CAPTURE
# ========================

# Start metrics capture in background for 120 seconds
# python3 /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py --duration 120 &

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

    if [[ "$container" == "free5gc_upf" ]]; then
        # UPF has bash, use bash
        docker exec "$container" \
            bash -c "timeout $duration tcpdump -i $container_interface -w /tmp/${container}_capture.pcap" > /dev/null 2>&1 &
    else
        # Default to sh for others
        docker exec "$container" \
            sh -c "timeout $duration tcpdump -i $container_interface -w /tmp/${container}_capture.pcap" > /dev/null 2>&1 &
    fi
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

# ========================
# SET FILE OWNERSHIP
# ========================

echo "[*] Changing ownership of output directory and files to ubuntu:ubuntu"
sudo chown -R ubuntu:ubuntu "$host_output_dir"

echo "[✓] PCAP collection complete: $host_output_dir"