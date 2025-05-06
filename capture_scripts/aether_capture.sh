#!/bin/bash

# ===
# find right names of aether pods (NF's)
# ===

# Absolute path to Aether Onramp
AETHER_PATH="/home/ubuntu/aether-onramp"
SIGNAL_FILE="/home/ubuntu/done_signal.txt"  # Path to the signal file

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
host_pcap_path="$host_output_dir/host_capture.pcap"
mkdir -p "$host_output_dir/logs"

# ===
# HOST OS CAPTURE
# ===

# Start metrics capture in the background for 120 seconds
python3 /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/capture_with_metrics.py --duration 120 &

echo "[DEBUG] Starting tcpdump on host interface: $host_interface"
sudo timeout "$duration" tcpdump -i "$host_interface" -w "$host_pcap_path" > "$host_output_dir/host_tcpdump.log" 2>&1 &
host_pid=$!  # Store the process ID of the tcpdump command
echo "[DEBUG] tcpdump on host interface started in the background (PID: $host_pid)."

# ===
# POD CAPTURES
# ===

echo "[*] Starting tcpdump in pods..."

pod_pids=()  # Array to store process IDs of pod captures

for pod in "${matched_pods[@]}"; do
    echo "  [+] $pod capturing on interface '$pod_interface' for $duration seconds"

    if [[ "$pod" == "upf-0" ]]; then
        echo "[DEBUG] Starting kubectl sniff for pod: $pod (UPF) on interface: $pod_interface"
        timeout "$duration" kubectl sniff -n aether-5gc "$pod" -c pfcp-agent -i "$pod_interface" -o "$host_output_dir/${pod}_capture.pcap" > "$host_output_dir/logs/${pod}_sniff.log" 2>&1 &
        pod_pids+=($!)  # Store the process ID of the kubectl sniff command
    else
        echo "[DEBUG] Starting kubectl sniff for pod: $pod on interface: $pod_interface"
        timeout "$duration" kubectl sniff -n aether-5gc "$pod" -i "$pod_interface" -o "$host_output_dir/${pod}_capture.pcap" > "$host_output_dir/logs/${pod}_sniff.log" 2>&1 &
        pod_pids+=($!)  # Store the process ID of the kubectl sniff command
    fi

    echo "[DEBUG] kubectl sniff for pod: $pod started in the background (PID: ${pod_pids[-1]})."
done

# ===
# WAIT FOR SIGNAL FILE
# ===

echo "[*] Waiting for signal file: $SIGNAL_FILE"

timeout=300  # 5 minutes
elapsed=0
while [ ! -f "$SIGNAL_FILE" ]; do
    if [ $elapsed -ge $timeout ]; then
        echo "[ERROR] Timeout reached while waiting for signal file."
        exit 1
    fi
    sleep 5
    elapsed=$((elapsed + 5))
done

echo "[*] Signal file detected. Stopping capture processes."

# Stop all capture processes
for pid in "${pod_pids[@]}"; do
    kill "$pid" 2>/dev/null
done

kill "$host_pid" 2>/dev/null

echo "[✓] All capture processes stopped."

# Clean up the signal file
rm -f "$SIGNAL_FILE"
echo "[*] Signal file removed."

# ===
# WAITING FOR ALL CAPTURES
# ===

echo "[*] Waiting for all tcpdump and kubectl sniff processes to complete..."

# Track failures
failed_pids=()

# Wait for all pod capture processes to complete
for pid in "${pod_pids[@]}"; do
    if ! wait "$pid"; then
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo "[INFO] Pod capture process (PID: $pid) completed successfully."
        elif [ $exit_code -eq 124 ]; then
            echo "[INFO] Pod capture process (PID: $pid) was terminated by timeout. Treating as success."
        else
            echo "[ERROR] A pod capture process (PID: $pid) failed with exit code $exit_code. Check the corresponding log file for details."
            failed_pids+=("$pid")  # Track the failed PID
        fi
    fi
done

# Wait for the host capture process to complete
if ! wait "$host_pid"; then
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "[INFO] Host capture process (PID: $host_pid) completed successfully."
    elif [ $exit_code -eq 124 ]; then
        echo "[INFO] Host capture process (PID: $host_pid) was terminated by timeout. Treating as success."
    else
        echo "[ERROR] Host capture process (PID: $host_pid) failed with exit code $exit_code. Check $host_output_dir/host_tcpdump.log for details."
        failed_pids+=("$host_pid")  # Track the failed PID
    fi
fi

# Check if any processes failed
if [ ${#failed_pids[@]} -gt 0 ]; then
    echo "[ERROR] The following processes failed: ${failed_pids[*]}"
    echo "Please check the corresponding log files for more details."
    exit 1
fi

echo "[*] All tcpdump and kubectl sniff processes completed successfully."

# ===
# POST-CAPTURE TASKS
# ===

echo "[*] Changing ownership of output directory and files to ubuntu:ubuntu"
sudo chown -R ubuntu:ubuntu "$host_output_dir"

echo "[✓] PCAP collection complete: $host_output_dir"

