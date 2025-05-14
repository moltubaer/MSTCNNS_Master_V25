import os
from pathlib import Path

def generate_open5gs_ue_configs(template_path, output_dir, start_index, end_index, base_imsi_str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(template_path, 'r') as file:
        template = file.read()

    base_number = int(base_imsi_str)

    for i in range(start_index, end_index + 1):
        imsi = f'imsi-{base_number + (i - start_index):015d}'
        content = template.replace("supi: 'imsi-208930100006001'", f"supi: '{imsi}'")

        filename = f"aether-ue-{i}.yaml"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as out_file:
            out_file.write(content)

        print(f"Generated {filename} with IMSI {imsi}")

# Example usage
generate_open5gs_ue_configs(
    template_path='../config/aether-ue.yaml',
    output_dir='/home/ubuntu/UERANSIM/config/tests-pdu',
    start_index=1,
    end_index=10,
    base_imi_str="208930100006001"
)
