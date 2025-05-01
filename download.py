import os
import csv
import datetime

# Folder containing the daily index files.
INDEX_FOLDER = "daily_index_files"

# Function to parse one line
def parse_record(line):
    # Skip empty lines.
    if not line.strip():
        return None
    # Ensure the line is long enough to contain all fields.
    if len(line) < 96:
        return None
    try:
        # Fixed-width slicing based on known format.
        # (These positions may need adjustment depending on the file.)
        company_name = line[0:62].strip()
        form_type    = line[62:74].strip()
        cik          = line[74:84].strip()
        date_filed   = line[84:96].strip()
        file_name    = line[96:].strip()
        filing_date = datetime.datetime.strptime(date_filed, "%Y%m%d").date()
        # Determine quarter based on month. (1-4)
        quarter = ((filing_date.month - 1) // 3) + 1

        return {
            "Company Name": company_name,
            "Form Type": form_type,
            "CIK": cik,
            "Date Filed": date_filed,
            "File Name": file_name,
            "Parsed Date": filing_date,
            "Quarter": quarter
        }
    except ValueError:
        return None

# Removed up to and including the dashed line
def drop_header(lines):
    # Look for the dashed line that separates header from data.
    data_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("-"):
            # Assume this dashed line is the divider.
            data_start = i + 1
            break

    if data_start is None:
        print(f"Warning: No data separator found in {os.path.basename(filepath)}. Skipping file.")
        return []

    return lines[data_start:]

# Function to parse one daily index file.
def parse_idx_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Process each record line after the dashed line.
    return filter(None, map(parse_record, drop_header(lines)))

def parse_files(folder):
    records = []
    for idx_file in [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".idx")]:
        recs = parse_idx_file(idx_file)
        if not recs:
            print(f"Warning: No records parsed from {idx_file}.")
        records.extend(recs)

    print(f"Parsed {len(records)} total records from the daily index files.")
    records.sort(key=lambda r: r["Parsed Date"])
    return records

def write_output(output_filename, records):
    csv_fieldnames = ["Rank", "Company Name", "Form Type", "CIK", "Date Filed", "File Name"]
    with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
        writer.writeheader()
        for rank, rec in enumerate(records, start=1):
            writer.writerow({
                "Rank": rank,
                "Company Name": rec.get("Company Name", ""),
                "Form Type": rec.get("Form Type", ""),
                "CIK": rec.get("CIK", ""),
                "Date Filed": rec.get("Date Filed", ""),
                "File Name": rec.get("File Name", "")
            })
    print(f"Wrote {len(records)} records to {output_filename}")

all_records = parse_files(INDEX_FOLDER)
write_output("huge_ranked.csv", all_records);
for q in [1, 2, 3, 4]:
    write_output(f"ranked_QTR{q}.csv", [rec for rec in all_records if rec["Quarter"] == q]);
