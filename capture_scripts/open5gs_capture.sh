#!/usr/bin/env bash
set -euo pipefail

# ===
# Argument Parsing
# ===

# Default values
duration=5
ue_count=100
test_script_name="default_test"
mode="default_mode"
mean_delay=""

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
        --mean-delay)
            mean_delay="$2"
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

echo "⏱️  Capture duration: ${duration}s"
echo "[*] UE count set to $ue_count."
echo "[*] Test script name set to $test_script_name."
echo "[*] Mode set to $mode."
echo "[*] Mean delay set to $mean_delay."

# ===
# CONFIGURATION
# ===

# Containers to monitor
containers=(
    open5gs_amf open5gs_smf open5gs_upf open5gs_udr
    open5gs_ausf open5gs_bsf open5gs_pcf open5gs_udm
    open5gs_nssf open5gs_nrf open5gs_scp
)

timestamp=$(date +%Y.%m.%d_%H.%M)
current_date=$(date +%d.%m.%Y)
output_dir="/home/ubuntu/pcap_captures/open5gs_${current_date}_captures/${ue_count}_${mode}_${mean_delay}_${test_script_name}_open5gs_${timestamp}"
mkdir -p "$output_dir"

declare -a pids

# ===
# START CAPTURE
# ===

# Start metrics capture in the background
python3 /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py --duration "$duration" &

for container in "${containers[@]}"; do
    echo "📡 Processing: $container"

    # Ensure container is running
    if [[ "$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null)" != "true" ]]; then
        echo "  ⚠️  $container is not running. Skipping."
        continue
    fi

    # Get container PID
    pid=$(docker inspect -f '{{.State.Pid}}' "$container")
    echo "  🔍 PID = $pid"

    # Get iflink inside container
    iflink=$(docker exec "$container" cat /sys/class/net/eth0/iflink)
    echo "  🔗 iflink = $iflink"

    # Find host veth interface
    veth_path=$(grep -l "^${iflink}$" /sys/class/net/veth*/ifindex || true)
    if [[ -z "$veth_path" ]]; then
        echo "  ⚠️  No veth@ifindex=$iflink on host. Skipping."
        continue
    fi
    veth_iface=$(basename "$(dirname "$veth_path")")
    echo "  ✅ Host veth = $veth_iface"

    # Start tcpdump
    pcap_file="$output_dir/${container}.pcap"
    echo "  📝 Writing to $pcap_file"
    sudo tcpdump -i "$veth_iface" -n -w "$pcap_file" > "$output_dir/${container}_tcpdump.log" 2>&1 &
    pids+=("$!")
done

# ===
# WAIT FOR CAPTURE TO COMPLETE
# ===

echo "⏳ Capturing traffic for ${duration}s..."
sleep "$duration"

echo "⏹️  Stopping tcpdump processes..."
for pid in "${pids[@]}"; do
    sudo kill "$pid" || true
done

# ===
# SET FILE OWNERSHIP
# ===

echo "[*] Changing ownership of output directory and files to ubuntu:ubuntu"
sudo chown -R ubuntu:ubuntu "$output_dir"

echo "🎉 Done! Captures saved in $output_dir"