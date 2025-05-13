#!/bin/bash

# ===
# Argument Parsing
# ===

# Default values
duration=120
ue_count=100
test_script_name="default_test"
mode="default_mode"

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
        --test-script-name)
            test_script_name="$2"
            shift 2
            ;;
        --mode)
            mode="$2"
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
    echo "[ERROR] Invalid UE count: $ue_count. It must be a positive integer."
    exit 1
fi

echo "[*] Capture duration set to $duration seconds."
echo "[*] UE count set to $ue_count."
echo "[*] Test script name set to $test_script_name."
echo "[*] Mode set to $mode."

# ========================
# CONFIGURATION
# ========================

# List of Free5gc containers to capture from
containers=("free5gc_amf" "free5gc_smf" "free5gc_upf" "free5gc_udm" "free5gc_ausf" "free5gc_pcf" "free5gc_nssf" "free5gc_udr" "free5gc_nrf")

container_interface="eth0"
host_interface="enp2s0"

# Host output directory for collected pcaps
timestamp=$(date +%Y.%m.%d_%H.%M.%S)
host_output_dir="/home/ubuntu/pcap_captures/${ue_count}_${mode}_${test_script_name}_free5gc_${timestamp}"
host_pcap_path="$host_output_dir/${ue_count}_${mode}_${test_script_name}_host_capture.pcap"
mkdir -p "$host_output_dir/logs"

# ========================
# HOST OS CAPTURE
# ========================

echo "[*] Starting tcpdump on host interface: $host_interface"

sudo timeout "$duration" tcpdump -i "$host_interface" -w "$host_pcap_path" > "$host_output_dir/logs/host_tcpdump.log" 2>&1 &
host_pid=$!

if [ -z "$host_pid" ]; then
    echo "[ERROR] Failed to start tcpdump on host interface. Exiting."
    exit 1
fi

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
            bash -c "timeout $duration tcpdump -i $container_interface -w /tmp/${container}_capture.pcap" > "$host_output_dir/logs/${container}_tcpdump.log" 2>&1 &
    else
        # Default to sh for others
        docker exec "$container" \
            sh -c "timeout $duration tcpdump -i $container_interface -w /tmp/${container}_capture.pcap" > "$host_output_dir/logs/${container}_tcpdump.log" 2>&1 &
    fi
    container_pids+=($!)
done

# ========================
# WAIT FOR ALL CAPTURES
# ========================

echo "[*] Waiting for all tcpdump processes to complete..."

# Track failures
failed_pids=()

# Wait for all container capture processes
for pid in "${container_pids[@]}"; do
    wait "$pid"
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "[INFO] Container capture process (PID: $pid) completed successfully."
    elif [ $exit_code -eq 124 ]; then
        echo "[INFO] Container capture process (PID: $pid) was terminated by timeout. Treating as success."
    else
        echo "[ERROR] A container capture process (PID: $pid) failed with exit code $exit_code. Check the corresponding log file for details."
        failed_pids+=("$pid")  # Track the failed PID
    fi
done

# Wait for the host capture process
if ! wait "$host_pid"; then
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "[INFO] Host capture process (PID: $host_pid) completed successfully."
    elif [ $exit_code -eq 124 ]; then
        echo "[INFO] Host capture process (PID: $host_pid) was terminated by timeout. Treating as success."
    else
        echo "[ERROR] Host capture process (PID: $host_pid) failed with exit code $exit_code. Check $host_output_dir/logs/host_tcpdump.log for details."
        failed_pids+=("$host_pid")  # Track the failed PID
    fi
fi
# echo "[*] Waiting for all tcpdump processes to complete..."
# ! may cause an error this, but still pushes it
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
    docker cp "$container:$src_path" "$dest_path" > "$host_output_dir/logs/${container}_copy.log" 2>&1

    if [ $? -eq 0 ]; then
        echo "  [INFO] Successfully copied $container:$src_path to $dest_path"
    else
        echo "  [ERROR] Failed to copy $container:$src_path. Check $host_output_dir/logs/${container}_copy.log for details."
    fi

    # Clean up inside the container
    docker exec "$container" rm -f "$src_path" > /dev/null 2>&1
done

# ========================
# SET FILE OWNERSHIP
# ========================

echo "[*] Changing ownership of output directory and files to ubuntu:ubuntu"
sudo chown -R ubuntu:ubuntu "$host_output_dir"

echo "[✓] PCAP collection complete: $host_output_dir"