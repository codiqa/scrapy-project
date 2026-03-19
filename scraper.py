import pandas as pd
import requests
import time
import xml.etree.ElementTree as ET
import re
import os


# -----------------------------
# CONFIG
# -----------------------------
# IRS CSV URLs (Regions 1-4)
CSV_DIR = "CSVs"
IRS_FILES = {
    "CSVs//region1.csv": "https://www.irs.gov/pub/irs-soi/eo1.csv",
    "CSVs//region2.csv": "https://www.irs.gov/pub/irs-soi/eo2.csv",
    "CSVs//region3.csv": "https://www.irs.gov/pub/irs-soi/eo3.csv",
    "CSVs//region4.csv": "https://www.irs.gov/pub/irs-soi/eo4.csv"
}

OUTPUT_FILE = "output_utf8.csv"

# XML fields we want to extract
FIELDS = [
    "CYTotalRevenueAmt",
    "CYContributionsGrantsAmt",
    "MembershipDuesAmt",
    "GovernmentGrantsAmt",
    "NoncashContributionsAmt",
    "TotalVolunteersCnt"
]

# Delay between requests (seconds)
REQUEST_DELAY = 0.5


# -----------------------------
# FUNCTION: Download IRS CSV
# -----------------------------
def download_irs_csv(url, filename):
    try:
        print(f"Downloading {filename} from IRS...")
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        with open(filename, "wb") as f:
            f.write(res.content)
        print(f"✅ Saved {filename}")
    except Exception as e:
        print(f"[ERROR] Could not download {filename}: {e}")


# -----------------------------
# FUNCTION: Get ProPublica XML URL
# -----------------------------
def get_xml_url(ein):
    """
    Retrieve the XML link from ProPublica for a given EIN.
    """
    base_url = f"https://projects.propublica.org/nonprofits/organizations/{ein}"
    try:
        res = requests.get(base_url, timeout=10)
        if res.status_code != 200:
            return None

        # Search for XML link
        match = re.search(r'https://[^\s"]+\.xml', res.text)
        if match:
            return match.group(0)
    except Exception as e:
        print(f"[ERROR] EIN {ein}: {e}")
    return None


# -----------------------------
# FUNCTION: Extract XML Fields
# -----------------------------
def extract_xml_data(xml_url):
    """
    Download XML and extract specified fields.
    """
    data = {field: None for field in FIELDS}
    try:
        res = requests.get(xml_url, timeout=10)
        res.raise_for_status()
        root = ET.fromstring(res.content)

        for field in FIELDS:
            elem = root.find(f".//{field}")
            if elem is not None:
                data[field] = elem.text
    except Exception as e:
        print(f"[XML ERROR] {xml_url}: {e}")
    return data


# -----------------------------
# FUNCTION: Main Pipeline
# -----------------------------
def process_data():
    # Step 1: Download all IRS CSVs
    os.makedirs(CSV_DIR, exist_ok=True)

    for local_file, url in IRS_FILES.items():
        download_irs_csv(url, local_file )

    # Step 2: Read and combine CSVs
    all_dfs = []
    for local_file in IRS_FILES.keys():
        df = pd.read_csv(local_file, dtype={"EIN": str}, encoding="latin-1")
        all_dfs.append(df)
    df_combined = pd.concat(all_dfs, ignore_index=True)
    print(f"✅ Combined {len(df_combined)} rows from all regions")

    # Step 3: Process each EIN
    results = []
    for index, row in df_combined.iterrows():
        ein = row.get("EIN")
        if not ein:
            results.append({field: None for field in FIELDS})
            continue

        print(f"Processing EIN: {ein}")

        xml_url = get_xml_url(ein)
        if not xml_url:
            print("  No XML found")
            results.append({field: None for field in FIELDS})
            continue

        data = extract_xml_data(xml_url)
        results.append(data)

        time.sleep(REQUEST_DELAY)  # polite delay

    # Step 4: Merge results and save
    result_df = pd.DataFrame(results)
    final_df = pd.concat([df_combined, result_df], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"✅ Done! Output saved to {OUTPUT_FILE}")


# -----------------------------
# RUN SCRIPT
# -----------------------------
if __name__ == "__main__":
    process_data()
