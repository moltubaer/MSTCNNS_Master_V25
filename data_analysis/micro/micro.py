import os
import re
import argparse
import subprocess
from pathlib import Path

# Configure available analysis scripts
SCRIPT_MAP = {
    "aether": {
        "ue_reg": {
            "amf": {".json": ["ue_reg_kafka.py"]},
            "ausf": {".json": ["ue_reg_json.py"]},
            "pcf": {".json": ["ue_reg_json.py"]},
            "udm": {".json": ["ue_reg_json.py"]},
        },
        "ue_dereg": {
            "amf": {".json": ["ue_dereg.py"]},
        },
        "pdu_est": {
            "smf": {".json": ["pdu_est.py"]},
        },
        "pdu_rel": {
            "smf": {".json": ["pdu_rel.py"]},
        },
    },
    "open5gs": {
        "ue_reg": {
            "amf": {".pdml": ["ue_reg_ngap.py"]},
            "ausf": {".json": ["ue_reg_json.py"]},
            "pcf": {".json": ["ue_reg_json.py"]},
            "udm": {".json": ["ue_reg_json.py"]},
        },
        "ue_dereg": {
            "amf": {".pdml": ["ue_dereg_ngap.py"]},
            "udm": {".json": ["ue_dereg.py"]},
            # "pcf": {".json": ["ue_dereg.py"]},
        },
        "pdu_est": {
            "amf": {".pdml": ["pdu_est_ngap.py"]},
            "pcf": {".json": ["pdu_est_json.py"]},
            "smf": {".json": ["pdu_est_json.py"]},
            "udm": {".json": ["pdu_est_json.py"]},
        },
        "pdu_rel": {
            "amf": {".pdml": ["pdu_rel_ngap.py"]},
            "pcf": {".json": ["pdu_rel_json.py"]},
            "smf": {".json": ["pdu_rel_json.py"]},
            "udm": {".json": ["pdu_rel_json.py"]},
        },
    },
    "free5gc": {
        "ue_reg": {
            "amf": {".pdml": ["ue_reg_ngap.py"]},
            "ausf": {".json": ["ue_reg_json.py"]},
            "pcf": {".json": ["ue_reg_json.py"]},
            "udm": {".json": ["ue_reg_json.py"]},
        },
        "ue_dereg": {
            "amf": {".pdml": ["ue_dereg_ngap.py"]},
            "udm": {".json": ["ue_dereg.py"]},
            # "pcf": {".json": ["ue_dereg.py"]},
        },
        "pdu_est": {
            "amf": {".pdml": ["pdu_est_ngap.py"]},
            "pcf": {".json": ["pdu_est_json.py"]},
            "smf": {".json": ["pdu_est_json.py"]},
            "udm": {".json": ["pdu_est_json.py"]},
        },
        "pdu_rel": {
            "amf": {".pdml": ["pdu_rel_ngap.py"]},
            "pcf": {".json": ["pdu_rel.py"]},
            "smf": {".json": ["pdu_rel.py"]},
            "udm": {".json": ["pdu_rel.py"]},
        },
    },
}

def detect_and_run(base_dir, output_dir):
    base_path = Path(base_dir)
    pattern_dir = re.compile(r"(\d+)_.*_(ue_reg|ue_dereg|pdu_est|pdu_rel)_(aether|open5gs|free5gc)")
    # pattern_file = re.compile(r"(?P<ue_num>\d+|open5gs|free5gc|aether)_(?P<nf>[a-z0-9\-]+)_capture(?P<ext>\.json|\.pdml)$")
    pattern_file = re.compile(
        r"(?P<ue_num>\d+|open5gs|free5gc|aether)_(?P<nf>[a-z0-9\-]+)(?:_capture)?(?P<ext>\.json|\.pdml)$"
    )

    for path in base_path.rglob("*"):
        if not path.is_file():
            continue

        match_dir = pattern_dir.search(str(path.parent))
        match_file = pattern_file.match(path.name)

        if not match_dir or not match_file:
            if path.suffix in {'.pdml', '.json'}:
                print(f"[WARN] Skipping unrecognized file format: {path}")
            continue

        ue_count, operation, core = match_dir.groups()
        nf = match_file.group("nf")
        ext = match_file.group("ext")

        scripts = SCRIPT_MAP.get(core, {}).get(operation, {}).get(nf, {}).get(ext, [])

        for script in scripts:
            print("\n🔍 Detected:")
            print(f"   • File:         {path}")
            print(f"   • NF:           {nf}")
            print(f"   • Operation:    {operation}")
            print(f"   • Core:         {core}")
            print(f"   • Script:       {script}")

            # Create a destination folder for output
            out_subdir = Path(output_dir) / path.relative_to(base_path).parent
            out_subdir.mkdir(parents=True, exist_ok=True)

            # Call script via subprocess and pass args
            try:
                input_dir = str(path.parent)
                input_file = path.name

                # Build command
                cmd = ["python3", script, "--input", input_dir, "--name", input_file, "--output", str(out_subdir)]
                print(cmd)
                
                # If the script requires a pattern (like ue_reg_json.py), pass nf
                # if "ue_reg_json.py" in script:
                #     cmd += ["--pattern", nf]
                # elif "pdu_est.py" in script:
                #     cmd += ["--pattern", nf]
                # elif "pdu_rel.py" in script:
                #     cmd += ["--pattern", nf]

                cmd += ["--pattern", nf]


                subprocess.run(cmd, check=True)

                # Count lines in the resulting CSV file (if created)
                output_csv = out_subdir / f"{input_file}.csv"
                if output_csv.exists():
                    with open(output_csv, "r", encoding="utf-8") as f:
                        line_count = sum(1 for _ in f) - 1  # subtract 1 for header
                    print(f"📊 {output_csv.name}: {line_count} data row(s)")


            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to run {script} on {path}: {e}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect NF files and map to scripts")
    parser.add_argument("--input", "-i", default="/mnt/c/Dev/master/pcap_captures/open5gs/test", help="Path to search recursively")
    parser.add_argument("--output", "-o", default="/mnt/c/Dev/master/pcap_captures/open5gs/output", help="Directory to store outputs")
    args = parser.parse_args()

    detect_and_run(args.input, args.output)
