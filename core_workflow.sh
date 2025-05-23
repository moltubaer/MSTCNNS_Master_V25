#!/bin/bash

# Usage: ./core_workflow.sh -e [aether|open5gs|free5gc] --duration [seconds] --count [number_of_ues] --test [test_script] --mode [linear|exponential] --mean-delay [seconds]

CONFIG_DIR="./core_config"
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

current_date=$(date +%d.%m.%Y)

# Ensure config file was specified and exists
if [ -z "$CONFIG_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found. Use -e [aether|open5gs|free5gc] and ensure it exists in '$CONFIG_DIR'."
  exit 1
fi

# Load config
source "$CONFIG_FILE"

# Validate the test script
if [[ "$TEST_SCRIPT" != "ue_reg.py" && "$TEST_SCRIPT" != "pdu_est.py" && "$TEST_SCRIPT" != "ue_dereg.py" && "$TEST_SCRIPT" != "pdu_rel.py" && "$TEST_SCRIPT" != "ue_reg_pdu.py" ]]; then
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
BUFFER_TIME=$DURATION  # Additional buffer time (in seconds)

# Remove the .py extension from the test script name for descriptive filenames
TEST_SCRIPT_NAME=$(basename "$TEST_SCRIPT" .py)

# Total duration = (UE_COUNT * MEAN_DELAY + BUFFER_TIME)
CAPTURE_DURATION=$(echo "$UE_COUNT * $MEAN_DELAY + $BUFFER_TIME" | bc)
CAPTURE_DURATION=${CAPTURE_DURATION%.*}  # Convert to integer
echo "[*] Calculated capture duration: $CAPTURE_DURATION seconds"

# Start the core capture script
echo "[*] Starting capture script on the $CORE core machine for $CAPTURE_DURATION seconds..."
ssh -tt -i "$CORE_KEY" "$CORE_CONNECTION" "source ~/.profile && bash $CORE_CAPTURE_SCRIPT --duration $CAPTURE_DURATION --ue-count $UE_COUNT --test-script-name $TEST_SCRIPT_NAME --mode $MODE > /tmp/capture.log 2>&1" &
capture_pid=$!  # Capture the PID of the capture process

# Start the UERANSIM capture script
echo "[*] Starting UERANSIM capture script..."
ssh -tt -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "nohup bash /home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh --duration $CAPTURE_DURATION --ue-count $UE_COUNT --mode $MODE --test $TEST_SCRIPT_NAME --core $CORE --mean-delay $MEAN_DELAY > /tmp/ueransim_logs/${CORE}_${UE_COUNT}_${TEST_SCRIPT}_${MODE}_${current_date}_ueransim_capture.log 2>&1" &
ueransim_capture_pid=$!  # Capture the PID of the UERANSIM capture process
# Wait for a short delay to ensure the capture script starts
echo "[*] Waiting for 10 seconds to ensure capture starts..."
sleep 10

# Start the selected test script on the UERANSIM machine
echo "[*] Starting $TEST_SCRIPT on the UERANSIM machine..."
ssh -tt -i "$UERANSIM_KEY" "$UERANSIM_CONNECTION" "nohup python3 /home/ubuntu/MSTCNNS_Master_V25/test_scripts/$TEST_SCRIPT --count $UE_COUNT --core $CORE --mode $MODE --duration $DURATION --mean-delay $MEAN_DELAY > /tmp/ue_logs/${CORE}_${UE_COUNT}_${TEST_SCRIPT}_${MEAN_DELAY}_${MODE}_${current_date}_ues_output.log 2>&1" &
ues_pid=$!  # Capture the PID of the UERANSIM process


# Wait for all processes to complete
echo "[*] Waiting for all processes to complete..."

# ====
# PROGRESS BAR
# ====

dur=$DURATION

# get full terminal width
cols=$(tput cols)
# reserve space for brackets, percentage and a space
bar_width=$(( cols - 8 ))

for (( elapsed=1; elapsed<=dur; elapsed++ )); do
  sleep 1

  percent=$(( elapsed * 100 / dur ))

  hashes=$(( elapsed * bar_width / dur ))
  spaces=$(( bar_width - hashes ))

  bar_hashes=$(printf '%*s' "$hashes" '' | tr ' ' '#')
  bar_spaces=$(printf '%*s' "$spaces" '')

  printf "\r[%s%s] %3d%%" "$bar_hashes" "$bar_spaces" "$percent"
done

printf "\n"




wait "$capture_pid"
echo "[✓] Capture script on the $CORE core machine completed."

wait "$ues_pid"
echo "[✓] $TEST_SCRIPT script completed on the UERANSIM machine."

wait "$ueransim_capture_pid"
echo "[✓] UERANSIM capture script completed."

# Cleanup remote processes
echo "[*] Cleaning up remote processes..."
echo " [+] Killing tcpdump on $CORE"
ssh -tt -i "$CORE_KEY" "$CORE_CONNECTION" "sudo pkill tcpdump" > /dev/null 2>&1

echo "[✓] Workflow completed successfully."