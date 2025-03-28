import subprocess
import time
import os
import signal

UE_CONFIG_DIR = "/home/ubuntu/UERANSIM/config/tests"
UE_BINARY = "/home/ubuntu/UERANSIM/build/nr-ue"  # 🔁 <-- Change this to your actual `nr-ue` binary

launched_processes = []

def run_ues(count):
    for i in range(1, count + 1):
        config_file = os.path.join(UE_CONFIG_DIR, f"open5gs-ue-{i}.yaml")
        if not os.path.exists(config_file):
            print(f"⚠️ Config file not found: {config_file}")
            continue
        print(f"🚀 Launching UE {i} with config {config_file}")
        proc = subprocess.Popen([UE_BINARY, "-c", config_file])
        launched_processes.append(proc)

def kill_ues():
    print("🛑 Killing all launched UEs...")
    for proc in launched_processes:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=5)
        except Exception as e:
            print(f"⚠️ Failed to kill process: {e}")
    print("✅ All UEs terminated.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Launch and manage UERANSIM UEs.")
    parser.add_argument("--count", type=int, help="Number of UEs to run")
    parser.add_argument("--kill", action="store_true", help="Kill running UEs from this session")
    parser.add_argument("--duration", type=int, default=None, help="Time in seconds before auto-killing UEs")

    args = parser.parse_args()

    if args.kill:
        kill_ues()
    elif args.count:
        run_ues(args.count)
        if args.duration:
            print(f"⏳ Waiting {args.duration} seconds before killing UEs...")
            time.sleep(args.duration)
            kill_ues()
