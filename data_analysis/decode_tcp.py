import json
import re

input_file = "/home/alexandermoltu/pcap_captures/linear/core/100-open5gs-2025.04.25_13.07.15/ausf1.json"
output_file = "decoded_payloads.txt"

def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        return bytes.fromhex(hex_str_clean).decode("utf-8", errors="ignore")
    except Exception:
        return ""

# Improved JSON object extraction with full nesting support
def extract_complete_json_objects(text):
    brace_level = 0
    buffer = ""
    in_json = False
    objects = []

    for char in text:
        if char == '{':
            brace_level += 1
            in_json = True
        if in_json:
            buffer += char
        if char == '}':
            brace_level -= 1
            if brace_level == 0 and buffer:
                try:
                    obj = json.loads(buffer)
                    # Must contain supi and either authVector or authResult
                    if (
                        ("authType" in obj and "authenticationVector" in obj and "supi" in obj)
                        or ("authResult" in obj and "supi" in obj)
                    ):
                        objects.append(obj)
                except json.JSONDecodeError:
                    pass
                buffer = ""
                in_json = False
    return objects

with open(input_file, "r") as f:
    packets = json.load(f)

with open(output_file, "w") as out:
    for pkt in packets:
        layers = pkt.get("_source", {}).get("layers", {})
        tcp = layers.get("tcp", {})
        payload = tcp.get("tcp.payload")

        if not payload:
            continue

        decoded = decode_payload(payload)
        json_objects = extract_complete_json_objects(decoded)
        for obj in json_objects:
            out.write(json.dumps(obj) + "\n")

print(f"✅ Clean JSON payloads containing SUPI and relevant auth info written to {output_file}")
