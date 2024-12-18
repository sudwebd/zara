import csv
import json
import re
import requests
import time

# Size mapping function
size_map = {
    'XXL': '08',
    'XS': '01',
    'S': '02',
    'M': '03',
    'L': '04',
    'XL': '05',
}

def extract_size(value):
    """
    Extract numeric size for 'EU ...' format or map string-only sizes.
    """
    eu_match = re.search(r"EU\s*(\d+)", value, re.IGNORECASE)
    if eu_match:
        return eu_match.group(1)
    return size_map.get(value.strip().upper(), "Unknown")

def load_json(json_file):
    """Load JSON data from file."""
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def build_api_url(references, gender):
    """Construct the API URL for stock check."""
    suf_list = ["-I2024", "-V2025"]
    base_url = "https://www.zara.com/in/en/store-stock?physicalStoreIds=16156&"

    for ref in references:
        for suf in suf_list:
            base_url += f"references={ref}{suf}&"

    base_url += f"sectionName={gender.upper()}&ajax=true"
    return base_url

def check_availability(api_url):
    """Fetch stock availability from the API."""
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    try:
        print(f"Calling API: {api_url}")  # Debug: Print API URL
        response = requests.get(api_url, headers=headers, timeout=10)  # Added timeout
        print(f"Response Status: {response.status_code}")  # Debug: Print status code
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        print("[ERROR] API request timed out.")
    except requests.RequestException as e:
        print(f"[ERROR] API Request failed: {e}")
    return {"productAvailability": []}


def process_csv_and_json(csv_file, json_file, output_file):
    """Process the CSV and JSON files to update inventory."""
    # Load JSON data
    json_data = load_json(json_file)

    # Read the CSV file
    with open(csv_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8", newline="") as outfile:
        reader = csv.DictReader(infile, delimiter=",")
        fieldnames = reader.fieldnames + ["Variant Inventory Adjust"]  # Add new column
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        references = []  # Store references for API call
        rows_to_update = []  # Rows to update after API call
        previous_handle = None
        gender = None  # Dynamically fetched gender

        # Process rows in the CSV
        for row in reader:
            current_handle = row["Handle"]
            if previous_handle and current_handle != previous_handle:
                # Process the previous group
                # print(f"Current Handle {current_handle}")
                process_group(references, rows_to_update, writer, json_data, gender)
                references = []
                rows_to_update = []

            # Match handle and color in JSON
            sku_id, color_code, gender = match_json(row, json_data)
            if sku_id and color_code:
                ref = f"{sku_id}{color_code}{extract_size(row['Option2 Value'])}"
                references.append(ref)
                rows_to_update.append(row)
            else:
                handle = row["Handle"].zfill(8)
                print(f"Match failed for {handle}")

            previous_handle = current_handle

        # Process the last group
        if references:
            process_group(references, rows_to_update, writer, json_data, gender)

def match_json(row, json_data):
    """Match JSON entry based on Handle and Option1 Value."""
    handle = row["Handle"].zfill(8)  # Pad handle to 8 digits
    option1_value = row["Option1 Value"]

    for product in json_data:
        if product["sku_id"] == handle and product["color"].lower() == option1_value.lower():
            return product["sku_id"], product["color_code"], product.get("gender", "").lower()
    return None, None, None

# from concurrent.futures import ThreadPoolExecutor, as_completed

def process_group(references, rows_to_update, writer, json_data, gender):
    """Process a group of rows with the same handle."""
    if not gender:
        print(f"[WARNING] Gender not found for this group.")
        return

    api_url = build_api_url(references, gender)
    availability_data = check_availability(api_url)
    time.sleep(0.05)

    # Extract available references from the API response
    available_refs = []
    for store in availability_data.get("productAvailability", []):
        for product in store.get("availableProducts", []):
            available_refs.append(product["reference"])
    
    suff = ""
    if len(available_refs):
        suff = available_refs[0][-6:]
    else: 
        return

    # Update rows and write to the new CSV
    for row in rows_to_update:
        sku_id, color_code, _ = match_json(row, json_data)
        ref = f"{sku_id}{color_code}{extract_size(row['Option2 Value'])}"+suff
        print(f"ref created is {ref}")
        if ref in available_refs:
            row["Variant Inventory Adjust"] = 1000
        else:
            row["Variant Inventory Adjust"] = 0
        writer.writerow(row)

# Main function
if __name__ == "__main__":
    csv_file = "Original.csv"          # Input CSV file
    json_file = "scrapes/master.json"        # Input JSON file
    output_file = "output_2.csv"      # Output CSV file

    process_csv_and_json(csv_file, json_file, output_file)
    print(f"Processing completed. Output saved to {output_file}")
