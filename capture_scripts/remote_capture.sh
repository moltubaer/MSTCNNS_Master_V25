#!/bin/bash

set -e

# === SSH ===
core1="ubuntu@10.100.51.80"
core2="ubuntu@10.100.51.81"
ueransim="ubuntu@10.100.51.82"


# === Configuration ===
FREE5GC_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/free5gc_capture.sh"
OPEN5GS_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/open5gs_capture.sh"
AETHER_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/aether_capture.sh"
UEARNSIM_SCRIPT="/home/ubuntu/MSTCNNS_Master_V25/capture_scripts/ueransim_capture.sh"

# === Parse Arguments ===
CORE=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
    --core)
        CORE="$2"
        shift 2
        ;;
    *)
        echo "❌ Unknown argument: $1"
        exit 1
        ;;
    esac
done

if [[ -z "$CORE" ]]; then
    echo "❌ Please specify --core free5gc|open5gs|aether"
    exit 1
fi

# === Dispatch to correct script ===
if [[ "$CORE" == "free5gc" ]]; then
    echo "[*] Running script on $core1..."
    ssh -tt "$core1" "sudo bash $FREE5GC_SCRIPT" &
    PID1=$!
    echo "[*] Running script on $ueransim..."
    ssh -tt "$ueransim" "sudo bash $ueransim_script" &
    PID2=$!
elif [[ "$CORE" == "open5gs" ]]; then
    echo "[*] Running script on $core1..."
    ssh -tt "$core1" "sudo bash $FREE5GC_SCRIPT" &
    PID1=$!
    echo "[*] Running script on $ueransim..."
    ssh -tt "$ueransim" "sudo bash $UERANSIM_SCRIPT" &
    PID2=$!
elif [[ "$CORE" == "aether" ]]; then
    echo "[*] Running script on $core2..."
    ssh -tt "$core2" "sudo bash $AETHER_SCRIPT" &
    PID1=$!
    echo "[*] Running script on $ueransim..."
    ssh -tt "$ueransim" "sudo bash $UERANSIM_SCRIPT" &
    PID2=$!
else
    echo "❌ Invalid core: $CORE. Must be free5gc, open5gs or aether."
    exit 1
fi

wait $PID1
wait $PID2

echo "[✓] Both remote scripts completed."
