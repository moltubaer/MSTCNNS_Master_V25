import subprocess
import time
import os
import signal
import argparse

UE_CONFIG_DIR = "/home/ubuntu/UERANSIM/config/tests"
UE_BINARY = "/home/ubuntu/UERANSIM/build/nr-ue"  # 🔁 <-- Change this to your actual `nr-ue` binary
PID_FILE = "ue-pids.txt"

launched_processes = []

def run_ues(count):
    with open(PID_FILE, "w") as pid_file:
        for i in range(1, count + 1):
            config_file = os.path.join(UE_CONFIG_DIR, f"open5gs-ue-{i}.yaml")
            if not os.path.exists(config_file):
                print(f"⚠️ Config file not found: {config_file}")
                continue
            print(f"🚀 Launching UE {i} with config {config_file}")
            proc = subprocess.Popen([UE_BINARY, "-c", config_file])
            pid_file.write(str(proc.pid) + "\n")

def kill_ues():
    if not os.path.exists(PID_FILE):
        print("⚠️ No PID file found. Did you run UEs from this script?")
        return

    with open(PID_FILE, "r") as pid_file:
        pids = [int(line.strip()) for line in pid_file]

    for pid in pids:
        try:
            os.kill(pid, signal.SIGINT)
            print(f"🛑 Killed PID {pid}")
        except ProcessLookupError:
            print(f"⚠️ PID {pid} not found (already exited?)")
        except Exception as e:
            print(f"⚠️ Error killing PID {pid}: {e}")

    os.remove(PID_FILE)
    print("✅ All UEs terminated and PID file cleaned up.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch and manage UERANSIM UEs.")
    parser.add_argument("--count", type=int, help="Number of UEs to run")
    parser.add_argument("--kill", action="store_true", help="Kill UEs started from PID file")
    parser.add_argument("--duration", type=int, help="Run duration before auto-kill (optional)")

    args = parser.parse_args()

    if args.kill:
        kill_ues()
    elif args.count:
        run_ues(args.count)
        if args.duration:
            print(f"⏳ Running for {args.duration} seconds...")
            time.sleep(args.duration)
            kill_ues()
