#!/bin/bash

# Usage: ./remote_runner.sh -e [aether|open5gs|free5gc] --duration [seconds] 
# todo: include also what test to run

# ------ DEFINED IN CONFIG ------
# ENV - for echo information purposes
# CORE_CONNECTION - ssh connection to core
# UERANSIM_CONNECTION - ssh connection to ueransim
# CORE_KEY - path to core private key file
# UERANSIM_KEY - path to ueransim private key file
# CORE_CAPTURE_SCRIPT - path to script for capture on different core network functions
# UERANSIM_CAPTURE_SCRIPT - path to script for capture traffic on ueransim 


CONFIG_DIR="./cores"
CONFIG_FILE=""

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

  echo "[*] Running capture-script on $host for $duration seconds..." >&2  # Redirect debug message to stderr

  # Add `source ~/.profile` for core2
  if [[ "$host" == "$CORE_CONNECTION" ]]; then
    ssh -tt -i "$key_file" "$host" "source ~/.profile && bash $script $duration" > /tmp/${host}_output.log 2>&1
  else
    ssh -tt -i "$key_file" "$host" "bash $script $duration" > /tmp/${host}_output.log 2>&1
  fi

  local exit_code=$?  # Capture the exit code of the SSH command
  echo "$exit_code"  # Return the exit code to the caller
}

# Run scripts on both remote machines in the background
run_remote_script "$CORE_KEY" "$CORE_CONNECTION" "$CORE_CAPTURE_SCRIPT" "$DURATION" &
PID1=$!
run_remote_script "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "$UERANSIM_CAPTURE_SCRIPT" "$DURATION" &
PID2=$!

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
wait_for_process "$PID1" "$CORE_CONNECTION"
wait_for_process "$PID2" "$UERANSIM_CONNECTION"

# todo: Decide what control plane test to run on ueransim machine
# ? UE-register, UE-PDU-session-establishment, UE-deregister

# todo: Write those captured files to a nice and descriptive file.

# todo: securecopy all those files from remote to locally

# todo: start a analysis workflow on those files

# todo: cleanup (pkill nr-ue, pkill nr-gnb)




echo "[✓] Both remote capture scripts completed successfully."