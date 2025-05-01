#!/bin/bash

# RUN ON LOCAL MACHINE
# ===
# CONFIGURATION
# ===

set -a
source ../.env
set +a

core2="ubuntu@10.100.51.81"
ueransim="ubuntu@10.100.51.82"

core2_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/aether_capture.sh"
ueransim_script="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh"

DURATION=120  # Default duration

# ===
# Parse Optional Arguments
# ===
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

# ====
# Execute Remote Scripts
# ====

# Function to check SSH connection
check_ssh_connection() {
  local host="$1"
  echo "[*] Checking SSH connection to $host..."
  if ssh -o BatchMode=yes -o ConnectTimeout=5 "$host" "exit" 2>/dev/null; then
    echo "[✓] SSH connection to $host successful."
  else
    echo "❌ Failed to connect to $host. Please check your SSH configuration."
    exit 1
  fi
}

# Function to run a remote script and handle errors
run_remote_script() {
  local key_file="$1"
  local host="$2"
  local script="$3"
  local duration="$4"

  echo "[*] Running script on $host..."
  ssh -tt -i "$key_file" "$host" "sudo bash $script $duration" > /tmp/${host}_output.log 2>&1 &
  local pid=$!
  echo "[*] Script on $host is running in the background (PID: $pid)."
  echo $pid  # Return the PID of the background process
}

# Check SSH connections
check_ssh_connection "$core2"
check_ssh_connection "$ueransim"

# Run scripts on both remote machines
PID1=$(run_remote_script "$core2_key_path" "$core2" "$core2_script" "$DURATION")
PID2=$(run_remote_script "$ueransim_key_path" "$ueransim" "$ueransim_script" "$DURATION")

# ====
# WAIT FOR BOTH TO FINISH
# ===

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