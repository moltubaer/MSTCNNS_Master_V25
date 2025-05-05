import subprocess
import time
import os
import signal
import argparse
import numpy as np

import matplotlib.pyplot as plt


UE_CONFIG_DIR = "/home/ubuntu/UERANSIM/config/tests"
UE_BINARY = "/home/ubuntu/UERANSIM/build/nr-ue"
PID_FILE = "ue-pids.txt"
SIGNAL_FILE = "/home/ubuntu/done_signal.txt"  # Path to the signal file on the Aether core server
AETHER_HOST = "ubuntu@10.100.51.81"  # Aether core server SSH connection
AETHER_KEY = "~/.ssh/aether_core.key"  # Path to the SSH private key for the Aether core server

default_delay = 0.01    # 10 ms
launched_processes = []

def run_ues(count, mean_delay):
    if args.mode == "exponential":
        delays = np.random.exponential(scale=mean_delay, size=count - 1)
    elif args.mode == "linear":
        delays = [mean_delay] * (count - 1)

    with open(PID_FILE, "w") as pid_file:
        for i in range(1, count + 1):
            config_file = os.path.join(UE_CONFIG_DIR, f"{args.core}-ue-{i}.yaml")
            if not os.path.exists(config_file):
                print(f"⚠️ Config file not found: {config_file}")
                continue

            print(f"🚀 Launching UE {i} with config {config_file}")
            proc = subprocess.Popen([UE_BINARY, "-c", config_file])
            pid_file.write(str(proc.pid) + "\n")

            if i < count:
                time.sleep(delays[i - 1])

    # Signal the Aether core server that the UEs are done
    print(f"✅ All UEs launched. Signaling Aether core server...")
    try:
        subprocess.run(
            ["ssh", "-i", AETHER_KEY, AETHER_HOST, f"touch {SIGNAL_FILE}"],
            check=True,
        )
        print(f"✅ Signal file created on Aether core server: {SIGNAL_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create signal file on Aether core server: {e}")
        return

    # Keep UEs running
    print("✅ All UEs launched and signal sent. Keeping UEs running...")
    try:
        while True:
            time.sleep(10)  # Keep the script alive
    except KeyboardInterrupt:
        print("🛑 Terminating UEs...")
        kill_ues()

def kill_ues():
    if not os.path.exists(PID_FILE):
        print("⚠️ No PID file found. Did you run UEs from this script?")
        return

    with open(PID_FILE, "r") as pid_file:
        pids = [int(line.strip()) for line in pid_file]

    for pid in pids:
        try:
            os.kill(pid, signal.SIGINT)
            print(f"🚑 Killed PID {pid}")
        except ProcessLookupError:
            print(f"⚠️ PID {pid} not found (already exited?)")
        except Exception as e:
            print(f"⚠️ Error killing PID {pid}: {e}")

    os.remove(PID_FILE)
    print("✅ All UEs terminated and PID file cleaned up.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch and manage UERANSIM UEs.")
    parser.add_argument("--count", "-c", type=int, help="Number of UEs to run")
    parser.add_argument("--kill" , "-k", action="store_true", help="Kill UEs started from PID file")
    parser.add_argument("--mean-delay", "-md", type=float, default=default_delay, help="Average delay between UE starts (seconds)")
    parser.add_argument("--core", choices=["open5gs", "free5gc", "aether"], required=True, help="Type of delay buffer between UE PDU session starts")
    parser.add_argument("--mode", choices=["linear", "exponential"], required=True, help="Type of delay buffer between UE PDU session starts")
    args = parser.parse_args()

    if args.kill:
        kill_ues()
    elif args.count:
        run_ues(args.count, args.mean_delay)
