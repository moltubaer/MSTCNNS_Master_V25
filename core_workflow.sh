#!/bin/bash

# Usage: ./core_workflow.sh -e [aether|open5gs|free5gc] --duration [seconds] --count [number_of_ues] --test [test_script] --mode [linear|exponential]

CONFIG_DIR="./cores"
CONFIG_FILE=""
DURATION=120  # Default duration
UE_COUNT=100  # Default number of UEs
TEST_SCRIPT="run_ues.py"  # Default test script
MODE="linear"  # Default mode

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
    --count)
      UE_COUNT="$2"
      shift 2
      ;;
    --test)
      TEST_SCRIPT="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
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

# Validate the test script
if [[ "$TEST_SCRIPT" != "run_ues.py" && "$TEST_SCRIPT" != "pdu_session.py" && "$TEST_SCRIPT" != "ue_dereg.py" ]]; then
  echo "❌ Invalid test script: $TEST_SCRIPT. Valid options are: run_ues.py, pdu_session.py, ue_dereg.py."
  exit 1
fi

# Validate the mode
if [[ "$MODE" != "linear" && "$MODE" != "exponential" ]]; then
  echo "❌ Invalid mode: $MODE. Valid options are: linear, exponential."
  exit 1
fi

# Calculate the duration for aether_capture.sh
MEAN_DELAY=0.01  # Mean delay between UE registrations (in seconds)
BUFFER_TIME=30  # Additional buffer time (in seconds)

# Total duration = (UE_COUNT * $MEAN_DELAY + $BUFFER_TIME)
CAPTURE_DURATION=$(echo "$UE_COUNT * $MEAN_DELAY + $BUFFER_TIME" | bc)
CAPTURE_DURATION=${CAPTURE_DURATION%.*}  # Convert to integer
echo "[*] Calculated capture duration: $CAPTURE_DURATION seconds"

# Start capture script on the Aether core machine
echo "[*] Starting capture script on the Aether core machine for $CAPTURE_DURATION seconds..."
ssh -tt -i "$CORE_KEY" "$CORE_CONNECTION" "source ~/.profile && bash $CORE_CAPTURE_SCRIPT --duration $CAPTURE_DURATION --ue-count $UE_COUNT > /tmp/capture.log 2>&1" &
capture_pid=$!  # Capture the PID of the capture process

# Wait for a short delay to ensure the capture script starts
echo "[*] Waiting for 5 seconds to ensure capture starts..."
sleep 5

# Start the selected test script on the UERANSIM machine
echo "[*] Starting $TEST_SCRIPT on the UERANSIM machine..."
ssh -tt -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "python3 /home/ubuntu/MSTCNNS_Master_V25/test_scripts/$TEST_SCRIPT --count $UE_COUNT --core aether --mode $MODE --mean-delay 0.01 --duration $DURATION > /tmp/ues_output.log 2>&1" &
ues_pid=$!  # Capture the PID of the UERANSIM process

# Wait for both processes to complete
echo "[*] Waiting for both capture and UERANSIM processes to complete..."
wait "$capture_pid"
echo "[✓] Capture script on the Aether core machine completed."

wait "$ues_pid"
echo "[✓] $TEST_SCRIPT script completed on the UERANSIM machine."

# Cleanup remote processes
echo "[*] Cleaning up remote processes..."
ssh -tt -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "pkill nr-ue; pkill nr-gnb" > /dev/null 2>&1
ssh -tt -i "$CORE_KEY" "$CORE_CONNECTION" "pkill tcpdump" > /dev/null 2>&1
echo "[✓] Cleanup completed."

echo "[✓] Workflow completed successfully."
