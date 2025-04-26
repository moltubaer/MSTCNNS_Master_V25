import json

path = "/home/alexandermoltu/pcap_captures/linear/core/100-open5gs-2025.04.25_13.07.15/"
input_file = "udm1.json"
output_file = input_file + ".decoded.txt"

def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        return bytes.fromhex(hex_str_clean).decode("utf-8", errors="ignore")
    except Exception:
        return ""

with open(path + input_file, "r") as f:
    packets = json.load(f)

with open(output_file, "w") as out:
    for pkt in packets:
        layers = pkt.get("_source", {}).get("layers", {})
        frame_number = layers.get("frame", {}).get("frame.number", "unknown")
        tcp = layers.get("tcp", {})
        payload = tcp.get("tcp.payload")

        if not payload:
            continue

        decoded = decode_payload(payload)
        if decoded.strip():  # Only print non-empty payloads
            line = f"Frame {frame_number}:\n{decoded}\n{'='*40}\n"
            print(line)
            out.write(line)

print(f"✅ Decoded TCP payloads printed and saved to {output_file}")
