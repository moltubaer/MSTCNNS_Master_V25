#!/bin/bash

# ===
# find right names of aether pods (NF's)
# ===

# Absolute path to Aether Onramp
AETHER_PATH="/home/ubuntu/aether-onramp"

# Step 1: Ensure kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "[ERROR] 'kubectl' command not found. Please install it first."
    exit 1
fi

# Step 2: Ensure the aether-onramp directory exists
if [ ! -d "$AETHER_PATH" ]; then
    echo "[ERROR] Directory '$AETHER_PATH' does not exist."
    exit 1
fi

# Step 3: Change into the aether-onramp directory
cd "$AETHER_PATH" || {
    echo "[ERROR] Failed to change directory to '$AETHER_PATH'."
    exit 1
}

# Step 4: Check if 'aether-5gc' namespace exists
if ! kubectl get ns aether-5gc &> /dev/null; then
    echo "[ERROR] Namespace 'aether-5gc' not found. Is Aether running?"
    exit 1
fi

# Step 5: Check if any pods are running in the namespace
if ! kubectl get pods -n aether-5gc | grep -q "Running"; then
    echo "[ERROR] No pods are currently running in the 'aether-5gc' namespace."
    exit 1
fi

# Step 6: Define core network functions of interest
target_nfs=("amf" "ausf" "smf" "upf" "pcf" "nssf" "udm" "nrf" "udr")
matched_pods=()

# Step 7: Get pod names in the namespace
pod_names=$(kubectl get pods -n aether-5gc -o custom-columns=NAME:.metadata.name --no-headers)

# Step 8: Match pods to the list
for nf in "${target_nfs[@]}"; do
    for pod in $pod_names; do
        if [[ "$pod" == "$nf"* ]]; then
            matched_pods+=("$pod")
        fi
    done
done

# Step 9: Print results
if [ ${#matched_pods[@]} -eq 0 ]; then
    echo "[INFO] No matching 5GC network function pods found."
else
    echo "Matched 5GC Core Network Function Pods:"
    for pod in "${matched_pods[@]}"; do
        echo " - $pod"
    done
fi

# ===
# GET READY
# ===

# Interface for pod, any to caputure all
pod_interface="any"

host_interface="any"

duration=${1:-120} # Default, 120 secods if not provided

timestamp=$(date +%Y.%m.%d_%H.%M.%S)
host_output_dir="/home/ubuntu/pcap_captures/aether-$timestamp"
mkdir -p "$host_output_dir"

# ===
# HOST OS CAPTURE
# ===

# start metrics capture in background for 120 seconds
python3 /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py --duration 120 &

echo "[*] Starting tcpdump on host interface: $host_interface"


host_pcap_path="$host_output_dir/host_capture.pcap"
# ! what is this? why capture on host?
# todo: find out later
sudo timeout "$duration" tcpdump -i "$host_interface" -w "$host_pcap_path" > /dev/null 2>&1 &
host_pid=$!

# ===
# POD CAPTURES
# ===

echo "[*] Starting tcpdump in pods..."

pod_pids=()

for pod in "${matched_pods[@]}"; do
    echo "  [+] $pod capturing on interface '$pod_interface' for $duration seconds"

    if [[ "$pod" == "upf-0"]]; then
        # capture with sniff for upf,
        sudo timeout "$duration" kubectl sniff -n aether-5gc "$pod" -c pfcp-agent -i "$pod_interface" -o "$host_output_dir" > /dev/null 2>&1 &
    else
        sudo timeout "$duration" kubectl sniff -n aether-5gc "$pod" -i "$pod_interface" -o "$host_output_dir" > /dev/null 2>&1 &
    fi
    pod_pids+=($!)
done

# ===
# WAITING FOR ALL CAMPTURES
# ===

echo "[*] Waiting for all tcpdump processes to complete..."
wait "${pod_pids[@]}"
wait "$host_pid"
echo "[*] All tcpdump processes completed"

echo "[*] Changing ownership of output directory and files to ubuntu:ubuntu"
sudo chown -R ubuntu:ubuntu "$host_output_dir"

echo "[✓] PCAP collection complete: $host_output_dir"

