#!/bin/bash

# Usage: ./core_workflow.sh -e [aether|open5gs|free5gc] --duration [seconds]

# ------ DEFINED IN CONFIG ------
# ENV - for echo information purposes
# CORE_CONNECTION - ssh connection to core
# UERANSIM_CONNECTION - ssh connection to ueransim
# CORE_KEY - path to core private key file
# UERANSIM_KEY - path to ueransim private key file
# CORE_CAPTURE_SCRIPT - path to script for capture on different core network functions
# UERANSIM_CAPTURE_SCRIPT - path to script for capture traffic on ueransim
# RUN_UES_SCRIPT - path to the run_ues.py script on the UERANSIM machine

CONFIG_DIR="./cores"
CONFIG_FILE=""
DURATION=120  # Default duration

# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    -e)
      CONFIG_FILE="$CONFIG_DIR/${2}.sh"
      shift 2
      ;;
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

# Ensure config file was specified and exists
if [ -z "$CONFIG_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found. Use -e [aether|open5gs|free5gc] and ensure it exists in '$CONFIG_DIR'."
  exit 1
fi

# Load config
source "$CONFIG_FILE"

# Function to run a remote script and handle errors
run_remote_script() {
  local key_file="$1"
  local host="$2"
  local script="$3"
  local duration="$4"

  echo "[*] Running capture-script on $host for $duration seconds..." >&2
  ssh -tt -i "$key_file" "$host" "source ~/.profile && bash $script $duration" > /tmp/${host}_output.log 2>&1 &
  local pid=$!  # Capture the PID of the background process
  echo "$pid"  # Return the PID to the caller
}

# Function to run the UERANSIM `run_ues.py` script
run_ues_script() {
  local key_file="$1"
  local host="$2"
  local script="$3"
  local count="$4"
  local mean_delay="$5"
  local mode="$6"

  echo "[*] Starting UERANSIM run_ues.py script on $host..." >&2
  ssh -tt -i "$key_file" "$host" "python3 $script --count $count --core aether --mode $mode --mean-delay $mean_delay" > /tmp/${host}_ues_output.log 2>&1
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    echo "❌ UERANSIM run_ues.py script failed on $host. Check the log file: /tmp/${host}_ues_output.log"
    exit 1
  else
    echo "[✓] UERANSIM run_ues.py script completed successfully on $host. Check the log file: /tmp/${host}_ues_output.log"
  fi
}

# Function to wait for a process and handle errors
wait_for_process() {
  local pid="$1"
  local host="$2"

  if ! wait "$pid"; then
    echo "❌ Script on $host failed. Check the log file: /tmp/${host}_output.log"
    exit 1
  else
    echo "[✓] Script on $host completed successfully. Check the log file: /tmp/${host}_output.log"
  fi
}

# Start capture scripts on both remote machines
PID1=$(run_remote_script "$CORE_KEY" "$CORE_CONNECTION" "$CORE_CAPTURE_SCRIPT" "$DURATION")
PID2=$(run_remote_script "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "$UERANSIM_CAPTURE_SCRIPT" "$DURATION")

# Wait for 5 seconds to ensure capture starts
echo "[*] Waiting for 5 seconds to ensure capture starts..."
sleep 5

# Run the UERANSIM `run_ues.py` script
run_ues_script "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "$RUN_UES_SCRIPT" 100 0.01 "exponential"

# Wait for both capture processes to complete
wait_for_process "$PID1" "$CORE_CONNECTION"
wait_for_process "$PID2" "$UERANSIM_CONNECTION"

# Securely copy captured files to the local machine
echo "[*] Copying captured files to the local machine..."
scp -i "$CORE_KEY" "$CORE_CONNECTION:/home/ubuntu/pcap_captures/*" ./captures/core/ > /dev/null 2>&1
scp -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION:/home/ubuntu/pcap_captures/*" ./captures/ueransim/ > /dev/null 2>&1
echo "[✓] Captured files copied successfully."

# Start analysis workflow
echo "[*] Starting analysis workflow on captured files..."
python3 analyze_captures.py --input ./captures/ --output ./analysis_results/
echo "[✓] Analysis workflow completed successfully."

# Cleanup remote processes
echo "[*] Cleaning up remote processes..."
ssh -tt -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "pkill nr-ue; pkill nr-gnb" > /dev/null 2>&1
ssh -tt -i "$CORE_KEY" "$CORE_CONNECTION" "pkill tcpdump" > /dev/null 2>&1
echo "[✓] Cleanup completed."

echo "[✓] Workflow completed successfully."