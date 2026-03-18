import pandas as pd
import requests
import time
import xml.etree.ElementTree as ET

# -----------------------------
# CONFIG
# -----------------------------
INPUT_FILE = "irs.csv"
OUTPUT_FILE = "output.csv"

# XML fields we want
FIELDS = [
    "CYTotalRevenueAmt",
    "CYContributionsGrantsAmt",
    "MembershipDuesAmt",
    "GovernmentGrantsAmt",
    "NoncashContributionsAmt",
    "TotalVolunteersCnt"
]

# -----------------------------
# HELPER: Get XML URL
# -----------------------------
def get_xml_url(ein):
    """
    Try to find XML URL from ProPublica
    """
    url = f"https://projects.propublica.org/nonprofits/organizations/{ein}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return None

        # Simple way: look for XML link
        if "xml" in res.text.lower():
            start = res.text.lower().find(".xml")
            snippet = res.text[start-200:start+50]

            # crude extraction
            import re
            match = re.search(r'https://[^\s"]+\.xml', snippet)
            if match:
                return match.group(0)

    except Exception as e:
        print(f"[ERROR] EIN {ein}: {e}")

    return None


# -----------------------------
# HELPER: Extract XML fields
# -----------------------------
def extract_xml_data(xml_url):
    """
    Download XML and extract required fields
    """
    data = {field: None for field in FIELDS}

    try:
        res = requests.get(xml_url, timeout=10)
        if res.status_code != 200:
            return data

        root = ET.fromstring(res.content)

        for field in FIELDS:
            elem = root.find(f".//{field}")
            if elem is not None:
                data[field] = elem.text

    except Exception as e:
        print(f"[XML ERROR] {xml_url}: {e}")

    return data


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def process_data():
    df = pd.read_csv(INPUT_FILE, dtype={"EIN": str}, encoding="latin-1")

    results = []

    for index, row in df.iterrows():
        ein = row["EIN"]

        print(f"Processing EIN: {ein}")

        xml_url = get_xml_url(ein)

        if not xml_url:
            print("  No XML found")
            results.append({field: None for field in FIELDS})
            continue

        data = extract_xml_data(xml_url)
        results.append(data)

        # polite delay (avoid blocking)
        time.sleep(0.5)

    # Merge results
    result_df = pd.DataFrame(results)
    final_df = pd.concat([df, result_df], axis=1)

    final_df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done! Output saved to", OUTPUT_FILE)


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    process_data()