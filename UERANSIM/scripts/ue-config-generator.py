import os
from pathlib import Path

def generate_open5gs_ue_configs(template_path, output_dir, start_index, end_index, base_imsi):
    # Ensure the output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Read the template content
    with open(template_path, 'r') as file:
        template = file.read()

    for i in range(start_index, end_index + 1):
        # Generate new IMSI (15 digits)
        imsi = f'imsi-{base_imsi + (i - start_index):015d}'
        content = template.replace("supi: 'imsi-001010000000001'", f"supi: '{imsi}'")

        # Write to new file
        filename = f"open5gs-ue-{i}.yaml"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as out_file:
            out_file.write(content)

        print(f"Generated {filename} with IMSI {imsi}")

# Example usage:
# generate_open5gs_ue_configs('open5gs-ue.yaml', './output', 1, 10, 001010000000010)
generate_open5gs_ue_configs(
    template_path='../config/open5gs-ue.yaml',
    output_dir='./ues',
    start_index=1,
    end_index=10,
    base_imsi=001010000000010
)

