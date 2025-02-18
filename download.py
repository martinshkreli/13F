import os
import csv
import datetime

# Folder containing the daily index files.
INDEX_FOLDER = "daily_index_files"

# List to hold all parsed filing records.
all_records = []

# Function to parse one daily index file.
def parse_idx_file(filepath):
    records = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Look for the dashed line that separates header from data.
    data_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("-"):
            # Assume this dashed line is the divider.
            data_start = i + 1
            break

    if data_start is None:
        print(f"Warning: No data separator found in {os.path.basename(filepath)}. Skipping file.")
        return records

    # Process each record line after the dashed line.
    for line in lines[data_start:]:
        # Skip empty lines.
        if not line.strip():
            continue
        # Ensure the line is long enough to contain all fields.
        if len(line) < 96:
            continue

        # Fixed-width slicing based on known format.
        # (These positions may need adjustment depending on the file.)
        company_name = line[0:62].strip()
        form_type    = line[62:74].strip()
        cik          = line[74:84].strip()
        date_filed   = line[84:96].strip()
        file_name    = line[96:].strip()

        record = {
            "Company Name": company_name,
            "Form Type": form_type,
            "CIK": cik,
            "Date Filed": date_filed,
            "File Name": file_name
        }
        records.append(record)
    return records

# Loop over each .idx file in the folder.
for filename in os.listdir(INDEX_FOLDER):
    if not filename.endswith(".idx"):
        continue
    filepath = os.path.join(INDEX_FOLDER, filename)
    recs = parse_idx_file(filepath)
    if not recs:
        print(f"Warning: No records parsed from {filename}.")
    all_records.extend(recs)

print(f"Parsed {len(all_records)} total records from the daily index files.")

# Function to parse the filing date (assumes format YYYYMMDD).
def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        return None

# Group records by quarter (1-4).
records_by_quarter = {1: [], 2: [], 3: [], 4: []}
combined_records = []

for record in all_records:
    date_str = record.get("Date Filed", "").strip()
    filing_date = parse_date(date_str)
    if filing_date is None:
        print(f"Warning: Could not parse date '{date_str}' in record: {record}")
        continue
    record["Parsed Date"] = filing_date
    # Determine quarter based on month.
    quarter = ((filing_date.month - 1) // 3) + 1
    records_by_quarter[quarter].append(record)
    combined_records.append(record)

# For each quarter, sort records by filing date and assign a rank.
for q in records_by_quarter:
    records_by_quarter[q].sort(key=lambda r: r["Parsed Date"])
    for rank, rec in enumerate(records_by_quarter[q], start=1):
        rec["Rank"] = rank

# Write out CSV files for each quarter.
csv_fieldnames = ["Rank", "Company Name", "Form Type", "CIK", "Date Filed", "File Name"]
for q, records in records_by_quarter.items():
    output_filename = f"ranked_QTR{q}.csv"
    with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow({
                "Rank": rec.get("Rank", ""),
                "Company Name": rec.get("Company Name", ""),
                "Form Type": rec.get("Form Type", ""),
                "CIK": rec.get("CIK", ""),
                "Date Filed": rec.get("Date Filed", ""),
                "File Name": rec.get("File Name", "")
            })
    print(f"Wrote {len(records)} records to {output_filename}")

# Create one huge combined CSV (overall ranking sorted by filing date).
combined_records.sort(key=lambda r: r["Parsed Date"])
with open("huge_ranked.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
    writer.writeheader()
    for rank, rec in enumerate(combined_records, start=1):
        writer.writerow({
            "Rank": rank,
            "Company Name": rec.get("Company Name", ""),
            "Form Type": rec.get("Form Type", ""),
            "CIK": rec.get("CIK", ""),
            "Date Filed": rec.get("Date Filed", ""),
            "File Name": rec.get("File Name", "")
        })
print(f"Wrote combined CSV with {len(combined_records)} records to huge_ranked.csv")
