import os
import csv
import re
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------------------------
# CONFIGURATION
# --------------------------
INPUT_FILE = "filtered_output.txt"
OUTPUT_RANKED_CSV = "aum_ranked.csv"
OUTPUT_FAILED_CSV = "aum_failed.csv"
SAMPLE_FILE = "sample_filing.txt"  # For saving a sample filing if needed

# Update with your real name and email per SEC guidelines.
HEADERS = {
    "User-Agent": "John Doe (john.doe@mycompany.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml"
}

# --------------------------
# RATE LIMITER SETUP
# --------------------------
global_lock = threading.Lock()
request_timestamps = []  # stores timestamps (in seconds) for recent requests

def acquire_token():
    """
    Blocks until the global rate limit allows a new request.
    Enforces a maximum of 9 requests per second.
    """
    while True:
        with global_lock:
            now = time.time()
            # Keep only timestamps from the last 1 second.
            valid_timestamps = [t for t in request_timestamps if now - t < 1.0]
            request_timestamps[:] = valid_timestamps
            if len(valid_timestamps) < 9:
                request_timestamps.append(now)
                return
            else:
                earliest = min(valid_timestamps)
                sleep_time = 1.0 - (now - earliest)
        if sleep_time > 0:
            time.sleep(sleep_time)

# --------------------------
# AUM EXTRACTION PATTERNS
# --------------------------
regex_patterns = [
    re.compile(r"<tableValueTotal>\s*([\d,]+(?:\.\d+)?)\s*</tableValueTotal>", re.IGNORECASE),
    re.compile(r"(?:AUM|Assets Under Management)[\s:]*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"Total Assets Under Management[\s:]*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"Assets\s+Under\s+Management[\s:]*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE)
]

def extract_aum(text):
    for pattern in regex_patterns:
        match = pattern.search(text)
        if match:
            num_str = match.group(1).replace(",", "")
            try:
                return float(num_str)
            except ValueError:
                continue
    return None

# --------------------------
# PROCESS A SINGLE LINE
# --------------------------
def process_line(idx, line, sample_saved_flag):
    if not line.strip():
        return None

    # Split the line on two or more whitespace characters.
    fields = re.split(r'\s{2,}', line.strip())
    if len(fields) < 5:
        return (False, {"line": line.strip(), "Error": "Not enough fields"})

    company_name = fields[0]
    form_type    = fields[1]
    cik          = fields[2]
    date_filed   = fields[3]
    file_name    = fields[4]

    if not file_name:
        return (False, {
            "Company Name": company_name,
            "Form Type": form_type,
            "CIK": cik,
            "Date Filed": date_filed,
            "File Name": file_name,
            "Error": "Missing File Name"
        })

    sec_url = f"https://www.sec.gov/Archives/{file_name}"
    acquire_token()  # enforce rate limit
    try:
        resp = requests.get(sec_url, headers=HEADERS, timeout=10)
    except Exception as e:
        return (False, {
            "Company Name": company_name,
            "Form Type": form_type,
            "CIK": cik,
            "Date Filed": date_filed,
            "File Name": file_name,
            "Error": f"Request error: {e}"
        })

    if resp.status_code != 200:
        return (False, {
            "Company Name": company_name,
            "Form Type": form_type,
            "CIK": cik,
            "Date Filed": date_filed,
            "File Name": file_name,
            "Error": f"HTTP {resp.status_code}"
        })

    filing_text = resp.text
    aum_value = extract_aum(filing_text)
    if aum_value is None:
        if not sample_saved_flag["saved"]:
            with open(SAMPLE_FILE, "w", encoding="utf-8") as sample_out:
                sample_out.write(filing_text[:1000])
            sample_saved_flag["saved"] = True
        return (False, {
            "Company Name": company_name,
            "Form Type": form_type,
            "CIK": cik,
            "Date Filed": date_filed,
            "File Name": file_name,
            "Error": "AUM not found or could not be parsed"
        })
    else:
        return (True, {
            "Company Name": company_name,
            "Form Type": form_type,
            "CIK": cik,
            "Date Filed": date_filed,
            "File Name": file_name,
            "AUM": aum_value
        })

# --------------------------
# MAIN EXECUTION
# --------------------------
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as fin:
        lines = fin.readlines()

    total_lines = len(lines)
    # Estimated total processing time based on 9 requests per second.
    estimated_seconds = total_lines / 9.0
    print(f"Estimated processing time: {estimated_seconds/60.0:.2f} minutes (at 9 requests/sec)")

    start_time = time.time()
    sample_saved_flag = {"saved": False}

    success_records = []
    failed_records = []
    processed = 0

    max_workers = 20
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_line, idx, line, sample_saved_flag): idx
                   for idx, line in enumerate(lines, start=1)}

        for future in as_completed(futures):
            result = future.result()
            processed += 1
            # Log progress every 50 processed records.
            if processed % 50 == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                avg_time = elapsed / processed
                remaining = (total_lines - processed) * avg_time
                print(f"Processed {processed}/{total_lines}. "
                      f"Avg time per record: {avg_time:.2f}s. "
                      f"Estimated time remaining: {remaining:.2f}s")
            if result is None:
                continue
            success, record = result
            if success:
                success_records.append(record)
            else:
                failed_records.append(record)

    total_time = time.time() - start_time
    print(f"Total processing time: {total_time/60.0:.2f} minutes")

    # Rank successful records by AUM (largest first).
    success_records.sort(key=lambda r: r["AUM"], reverse=True)

    fieldnames = ["Rank", "Company Name", "AUM", "Form Type", "CIK", "Date Filed", "File Name"]
    with open(OUTPUT_RANKED_CSV, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for rank, rec in enumerate(success_records, start=1):
            writer.writerow({
                "Rank": rank,
                "Company Name": rec["Company Name"],
                "AUM": rec["AUM"],
                "Form Type": rec["Form Type"],
                "CIK": rec["CIK"],
                "Date Filed": rec["Date Filed"],
                "File Name": rec["File Name"]
            })

    failed_fieldnames = ["Company Name", "Form Type", "CIK", "Date Filed", "File Name", "Error"]
    with open(OUTPUT_FAILED_CSV, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=failed_fieldnames)
        writer.writeheader()
        for rec in failed_records:
            writer.writerow(rec)

if __name__ == "__main__":
    main()
