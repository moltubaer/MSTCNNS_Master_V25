import os
import shutil
import argparse

def normalize_timestamp(s):
    return s.replace(":", ".")

def move_and_rename_system_csvs(input):
    entries = os.listdir(input)

    # Identify folders and CSV files
    folders = [entry for entry in entries if os.path.isdir(os.path.join(input, entry))]
    csv_files = [entry for entry in entries if entry.endswith('_system.csv')]

    # Build folder lookup with normalized names
    folder_lookup = {}
    for folder in folders:
        normalized = normalize_timestamp(folder)
        folder_lookup[normalized] = folder

    # Process each CSV file
    for csv_file in csv_files:
        original_path = os.path.join(input, csv_file)

        # Normalize filename (rename if needed)
        normalized_filename = normalize_timestamp(csv_file)
        normalized_path = os.path.join(input, normalized_filename)

        if csv_file != normalized_filename:
            os.rename(original_path, normalized_path)
            print(f"Renamed {csv_file} -> {normalized_filename}")
        else:
            print(f"No rename needed for {csv_file}")

        # Extract timestamp from filename
        timestamp_part = normalized_filename.replace('_system.csv', '')

        # Match with folder
        matched_folder = None
        for norm_folder_name, original_folder in folder_lookup.items():
            if timestamp_part in norm_folder_name:
                matched_folder = original_folder
                break

        if matched_folder:
            destination_path = os.path.join(input, matched_folder, normalized_filename)
            shutil.move(normalized_path, destination_path)
            print(f"Moved {normalized_filename} to {matched_folder}")
        else:
            print(f"No matching folder found for {normalized_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename system CSV files and move them into matching timestamp folders.")
    parser.add_argument("--input", "-i", help="Path to the directory containing CSVs and folders")

    args = parser.parse_args()
    move_and_rename_system_csvs(args.input)
