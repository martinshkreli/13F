import requests
import datetime
import os

# Replace with your actual name and email address as per SEC guidelines.
headers = {
    "User-Agent": "John Doe (john.doe@mycompany.com)",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Define the date range (last 3 days from today's date: 2025-02-14)
end_date = datetime.date(2025, 2, 14)
start_date = end_date - datetime.timedelta(days=3)
start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

# SEC EDGAR Full-Text Search API endpoint
api_url = "https://efts.sec.gov/LATEST/search-index"

# Build the query DSL payload to filter on filings with root_forms "13F-HR" and the given date range.
payload = {
    "_source": {"exclude": ["doc_text"]},
    "query": {
        "bool": {
            "filter": [
                {"term": {"root_forms": "13F-HR"}},
                {"range": {"file_date": {"gte": start_date_str, "lte": end_date_str}}}
            ]
        }
    },
    "from": 0,     # pagination start (0 for the first page)
    "size": 100,   # number of filings to return per page; adjust if needed
    "aggregations": {
        "form_filter": {"terms": {"field": "root_forms", "size": 30}},
        "entity_filter": {"terms": {"field": "display_names.raw", "size": 30}},
        "sic_filter": {"terms": {"field": "sics", "size": 30}},
        "biz_states_filter": {"terms": {"field": "biz_states", "size": 30}}
    }
}

try:
    # Send the POST request with the JSON payload
    response = requests.post(api_url, json=payload, headers=headers)
    response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
except requests.exceptions.HTTPError as e:
    print(f"HTTP error occurred: {e}")
    exit(1)

data = response.json()
print("Raw JSON response:", data)

# Extract filings from the response (they are nested under hits -> hits)
filings = data.get('hits', {}).get('hits', [])
print(f"Found {len(filings)} filings between {start_date_str} and {end_date_str}.")

# Create a directory to save downloaded filings.
download_dir = "13F_filings"
os.makedirs(download_dir, exist_ok=True)

# Iterate over each filing and attempt to download the filing document.
for filing in filings:
    source = filing.get('_source', {})
    accession_number = source.get("accessionNumber", "unknown_accession")
    cik = source.get("cik", "unknown_cik")
    filing_date = source.get("file_date", "unknown_date")
    form_type = source.get("formType", "unknown_form")
    
    # Retrieve the document URL – verify the field name against the latest API documentation.
    document_url = source.get("documentUrl")
    
    if document_url:
        print(f"Downloading filing {accession_number} for CIK {cik} filed on {filing_date}...")
        doc_response = requests.get(document_url, headers=headers)
        if doc_response.status_code == 200:
            filename = os.path.join(download_dir, f"{cik}_{accession_number}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(doc_response.text)
        else:
            print(f"Error downloading filing {accession_number}: HTTP {doc_response.status_code}")
    else:
        print(f"Filing {accession_number} does not have a downloadable document URL.")
