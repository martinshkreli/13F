import os

input_dir = "daily_index_files"
output_file = "filtered_output.txt"

with open(output_file, "w", encoding="utf-8") as fout:
    # Loop through each file in the daily_index_files folder.
    for filename in os.listdir(input_dir):
        if filename.endswith(".idx"):
            filepath = os.path.join(input_dir, filename)
            print(f"Processing {filepath}...")
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fin:
                for line in fin:
                    if "13F" in line:
                        fout.write(line)
                        
print(f"Filtered lines have been written to {output_file}")
