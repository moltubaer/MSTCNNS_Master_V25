#!/bin/bash

# CONFIGURATION
core2="ubuntu@10.100.51.81"
core2_key_path="~/.ssh/core2.key"
ueransim="ubuntu@10.100.51.82"
ueransim_key_path="~/.ssh/marc_ueransim.key"

core2_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/aether_capture.sh"
ueransim_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh"

DURATION=30  # Default duration

# Parse Optional Arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
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

# Function to run a remote script and handle errors
run_remote_script() {
  local key_file="$1"
  local host="$2"
  local script="$3"
  local duration="$4"

  echo "[*] Running script on $host..." >&2  # Redirect debug message to stderr

  # Add `source ~/.profile` for core2
  if [[ "$host" == "$core2" ]]; then
    ssh -tt -i "$key_file" "$host" "source ~/.profile && bash $script $duration" > /tmp/${host}_output.log 2>&1 &
  else
    ssh -tt -i "$key_file" "$host" "bash $script $duration" > /tmp/${host}_output.log 2>&1 &
  fi

  local pid=$!  # Capture the PID of the background process
  echo "$pid"  # Return only the PID to stdout
}

# Run scripts on both remote machines
PID1=$(run_remote_script "$core2_key_path" "$core2" "$core2_script" "$DURATION")
PID2=$(run_remote_script "$ueransim_key_path" "$ueransim" "$ueransim_script" "$DURATION")

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

# Wait for both processes
wait_for_process "$PID1" "$core2"
wait_for_process "$PID2" "$ueransim"

echo "[✓] Both remote scripts completed successfully."