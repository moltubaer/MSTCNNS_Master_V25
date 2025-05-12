#!/bin/bash

# Usage: ./core_workflow.sh -e [aether|open5gs|free5gc] --duration [seconds] --count [number_of_ues] --test [test_script] --mode [linear|exponential] --mean-delay [seconds]

CONFIG_DIR="./cores"
CONFIG_FILE=""
DURATION=120  # Default duration
UE_COUNT=100  # Default number of UEs
TEST_SCRIPT=""  # Default test script (empty to ensure it must be explicitly set)
MODE="linear"  # Default mode
MEAN_DELAY=0.01  # Default mean delay (10 ms)

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
    --mean-delay)
      MEAN_DELAY="$2"
      shift 2
      ;;
    *)
      echo "❌ Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Debug: Print the value of TEST_SCRIPT
echo "[DEBUG] TEST_SCRIPT is set to: $TEST_SCRIPT"

# Ensure config file was specified and exists
if [ -z "$CONFIG_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found. Use -e [aether|open5gs|free5gc] and ensure it exists in '$CONFIG_DIR'."
  exit 1
fi

# Load config
source "$CONFIG_FILE"

# Validate the test script
if [[ "$TEST_SCRIPT" != "run_ues.py" && "$TEST_SCRIPT" != "pdu_sessions.py" && "$TEST_SCRIPT" != "ue_dereg.py" ]]; then
  echo "❌ Invalid test script: $TEST_SCRIPT. Valid options are: run_ues.py, pdu_sessions.py, ue_dereg.py."
  exit 1
fi

# Validate the mode
if [[ "$MODE" != "linear" && "$MODE" != "exponential" ]]; then
  echo "❌ Invalid mode: $MODE. Valid options are: linear, exponential."
  exit 1
fi

# Validate the mean delay
if ! [[ "$MEAN_DELAY" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  echo "❌ Invalid mean delay: $MEAN_DELAY. It must be a positive number."
  exit 1
fi

# Calculate the duration for the capture scripts
BUFFER_TIME=30  # Additional buffer time (in seconds)

# Remove the .py extension from the test script name for descriptive filenames
TEST_SCRIPT_NAME=$(basename "$TEST_SCRIPT" .py)
echo "The test script name is: $TEST_SCRIPT_NAME"

# Total duration = (UE_COUNT * MEAN_DELAY + BUFFER_TIME)
CAPTURE_DURATION=$(echo "$UE_COUNT * $MEAN_DELAY + $BUFFER_TIME" | bc)
CAPTURE_DURATION=${CAPTURE_DURATION%.*}  # Convert to integer
echo "[*] Calculated capture duration: $CAPTURE_DURATION seconds"

# Start the core capture script
echo "[*] Starting capture script on the $CORE core machine for $CAPTURE_DURATION seconds..."
ssh -tt -i "$CORE_KEY" "$CORE_CONNECTION" "source ~/.profile && bash $CORE_CAPTURE_SCRIPT --duration $CAPTURE_DURATION --ue-count $UE_COUNT --test-script-name $TEST_SCRIPT_NAME --mode $MODE > /tmp/capture.log 2>&1" &
capture_pid=$!  # Capture the PID of the capture process

# Wait for a short delay to ensure the capture script starts
echo "[*] Waiting for 5 seconds to ensure capture starts..."
sleep 5

# Start the selected test script on the UERANSIM machine
echo "[*] Starting $TEST_SCRIPT on the UERANSIM machine..."
ssh -tt -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "nohup python3 /home/ubuntu/MSTCNNS_Master_V25/test_scripts/$TEST_SCRIPT --count $UE_COUNT --core $CORE --mode $MODE --duration $DURATION --mean-delay $MEAN_DELAY > /tmp/ues_output.log 2>&1" &
ues_pid=$!  # Capture the PID of the UERANSIM process

# Start the UERANSIM capture script
echo "[*] Starting UERANSIM capture script..."
ssh -tt -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "nohup bash /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh --duration $CAPTURE_DURATION --ue-count $UE_COUNT --mode $MODE --test $TEST_SCRIPT_NAME > /tmp/ueransim_capture.log 2>&1" &
ueransim_capture_pid=$!  # Capture the PID of the UERANSIM capture process

# Wait for all processes to complete
echo "[*] Waiting for all processes to complete..."
wait "$capture_pid"
echo "[✓] Capture script on the $CORE core machine completed."

wait "$ues_pid"
echo "[✓] $TEST_SCRIPT script completed on the UERANSIM machine."

wait "$ueransim_capture_pid"
echo "[✓] UERANSIM capture script completed."

# Wait for 1 minute before cleanup
echo "[*] Waiting for 1 minute before cleaning up..."

# Cleanup remote processes
echo "[*] Cleaning up remote processes..."
echo " [+] Killing tcpdump on $CORE"
ssh -tt -i "$CORE_KEY" "$CORE_CONNECTION" "sudo pkill tcpdump" > /dev/null 2>&1

echo "[✓] Workflow completed successfully."