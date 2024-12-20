import csv
import json
import re
import requests
import time
import logging
import sys, os
from imports_common import *
import requests
import brotli
from bs4 import BeautifulSoup
logging.basicConfig(filename=f"logs/inventory_fetch{time.time()}.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
# session_lock = Lock()
# api_lock = Lock()

# Shared session
# session = requests.Session()
#size guide:
    # 'XS': '01',
    # 'S': '02',
    # 'M': '03',
    # 'L': '04', 
    # 'XL': '05',
    # 'XXL': '06',
    # 'XXXL': '07',
    # 'XXS': '08',
    # 26-50 in EU codes(2 increments)

def create_api_string(sku_base, colors, suf, gender):
    s = "https://www.zara.com/in/en/store-stock?physicalStoreIds=16156"
    for color in colors:
        ref = f"&references={sku_base}{color}"
        for i in range(1, 8):
            s += ref + ("0" if(i < 10) else "") + str(i) + suf
        for i in range(26, 50, 2):
            s += ref + ("0" if(i < 10) else "") + str(i) + suf       
    s += f"&sectionName={gender.upper()}&ajax=true"
    return s

headers = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

def fetch_inventory(sku_base, colors, gender):
    suf_list = ["-I2024", "-V2025"]
    for suf in suf_list:
        url = create_api_string(sku_base, colors, suf, gender)
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if len(data.get("productAvailability", [])):       
                logging.info(f"[DEBUG] product {sku_base} FOUND in store")
                return data
        except requests.RequestException as e:
            logging.info(f"Error fetching store availability for: {e}")
    logging.info(f"[TRACE] product {sku_base} NOT AVAILABLE in store")            
    return {"productAvailability": []}


new_sizes = {}
def match_sizes_with_original(csv_master_file, upload_master_file, output_file):
    # col -> sz orig
    # col -> sz new
    # col -> sz of orig not in new (Inventory Update)
    # col -> sz of new not in orig (New Product Update)
    color_to_size_new = {}
    color_size_removed = []
    with open(csv_master_file, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile, delimiter=",")    
        for row in reader:
            sku_base = row["sku_base"]
            # if sku_base != "05320406": continue
            col_sz = []
            if "|" in row["cols_sz"]:
                col_sz = row["cols_sz"].split("|")    
            else:
                col_sz.append(row["cols_sz"])
            colors_original = []
            color_to_size_new.clear()
            for sz in col_sz:
                col_code = sz.split("#")[1]
                colors_original.append(col_code)
                color_to_size_new[col_code] = []          
            logging.debug(f"colors found {colors_original}")
            new_inventory = fetch_inventory(sku_base, colors_original, row["gender"]).get("productAvailability", [])
            if not new_inventory:
                logging.debug(f"Full Inventory Gone for SKU {sku_base}")  
            for store in new_inventory:
                available_products = store.get("availableProducts", [])
                for product in available_products:
                    color_code = product.get("reference")[-11:-8]
                    # if not color in color_to_size_new:
                    #     color_to_size_new[color] = []
                    color_to_size_new[color_code].append(product.get("size"))
            for sz in col_sz:
                info = sz.split("#")
                col_orig = info[0]
                col_code_orig = info[1]
                size_orig = info[2].split(",")
                # size_pdp = info[3]
                # color_size_removed[sku_base] = {}
                # color_size_removed[sku_base][col_orig] = 
                logging.debug(f"map {color_to_size_new}")
                removed = list(set(size_orig) - set(color_to_size_new.get(col_code_orig, [])))
                new = list(set(color_to_size_new.get(col_code_orig, [])) - set(size_orig))
                if len(new):
                    if sku_base not in new_sizes: new_sizes[sku_base] = {}
                    new_sizes[sku_base][col_orig] = new
                for s in removed:
                    search_and_append(upload_master_file, output_file, (sku_base.lstrip("0"), col_orig, s))

# def search_and_append(csv_file, output_file, search_criteria):
#     """
#     Search for a row in the CSV based on Handle, Option1 Value, and Option2 Value
#     and append it to a new file with an additional value 0.

#     :param csv_file: Input CSV file path.
#     :param output_file: Output CSV file path.
#     :param search_criteria: Tuple containing (Handle, Option1 Value, Option2 Value).
#     """
#     lookup = {}
#     # Step 1: Build the lookup dictionary
#     with open(csv_file, 'r', encoding='utf-8') as infile:
#         reader = csv.DictReader(infile)
#         for row in reader:
#             key = (row['Handle'], row['Option1 Value'], row['Option2 Value'])
#             lookup[key] = row  # Store the row for fast access

#     # Step 2: Search in the dictionary
#     handle, option1_value, option2_value = search_criteria
#     key_to_find = (handle, option1_value, option2_value)
#     matching_row = lookup.get(key_to_find)

#     # Step 3: Write the matching row to a new file with "0" appended
#     if matching_row:
#         with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
#             fieldnames = list(matching_row.keys()) + ["Variant Inventory Adjust"]
#             writer = csv.DictWriter(outfile, fieldnames=fieldnames)
#             writer.writeheader()
            
#             # Append '0' to the row and write it
#             matching_row["Variant Inventory Adjust"] = 0
#             writer.writerow(matching_row)
#             logging.debug(f"Row written to {output_file}: {matching_row}")
#     else:
#         logging.debug("No matching row found.")
    
def search_and_append(csv_file, output_file, search_criteria):
    """
    Search for a row in the CSV based on Handle, Option1 Value, and Option2 Value
    and append it to a new file with an additional value 0.
    """
    lookup = {}
    with open(csv_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            key = (row['Handle'], row['Option1 Value'], row['Option2 Value'])
            lookup[key] = row

    handle, option1_value, option2_value = search_criteria
    key_to_find = (handle, option1_value, option2_value)
    matching_row = lookup.get(key_to_find)

    if matching_row:
        file_exists = os.path.isfile(output_file)  # Check if file exists
        with open(output_file, 'a', encoding='utf-8', newline='') as outfile:
            fieldnames = list(matching_row.keys()) + ["Variant Inventory Adjust"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            if not file_exists:  # Write the header once
                writer.writeheader()

            matching_row["Variant Inventory Adjust"] = 0
            writer.writerow(matching_row)
            logging.debug(f"Row written to {output_file}: {matching_row}")
    else:
        logging.debug("No matching row found.")

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
}

def fetch_html_with_debugging(url):
    global session
    try:
        # with session_lock:
        logging.info(f"[DEBUG] Starting fetch for URL: {url}")
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()
        
        # Brotli decompression if needed
        content_encoding = response.headers.get("content-encoding", "")
        raw_content = response.content
        if content_encoding == "br":
            raw_content = brotli.decompress(raw_content)
        
        response_text = raw_content.decode("utf-8")
        return BeautifulSoup(response_text, "html.parser")
    except Exception as e:
        logging.info(f"[ERROR] Failed to fetch or parse the page. Exception {e}")
        return None

def fetch_product_prices(pdp_link):
    product_soup = fetch_html_with_debugging(pdp_link)
    if not product_soup:
        logging.info(f"Failed to create driver for {pdp_link}")
        return
    details = product_soup.select_one('div.layout.layout--grid-type-standard.layout-catalog.product-detail-view  div.layout-content.layout-catalog-content--full div.product-detail-view__main') 
    price_discount_dt = details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.price__amount.price__amount--on-sale.price__amount--is-highlighted.price-current--with-background.price-current--is-highlighted span.price-current__amount span.money-amount__main')
    price_discount = re.sub(r"[^\d.,]", "", price_discount_dt.text) if price_discount_dt else "0"
    if price_discount != "0":
        price = re.sub(r"[^\d.,]", "", details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.price__amount--old-price-wrapper span.money-amount__main').text)
    else:    
        price = re.sub(r"[^\d.,]", "", details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.money-amount__main').text)
        price_discount = price   
    return (price_discount, price)    

def add_new_sizes_to_csv(input_csv, output_csv):
    """
    Process a CSV file, fetch existing information, and add rows for new sizes.

    :param input_csv: Path to the input CSV file.
    :param output_csv: Path to the output CSV file with new sizes added.
    :param new_sizes: Dictionary with Handles and their respective colors and sizes.
    """
    with open(input_csv, "r", encoding="utf-8") as infile, open(output_csv, "w", encoding="utf-8", newline="") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        writer.writeheader()  # Write header to the output file
        rows_to_add = []  # List to store new rows

        lookup = {}
        # Step 1: Build a lookup dictionary for fetching extra information
        for row in reader:
            key = (row["Handle"], row["Option1 Value"])
            if key not in lookup:
                lookup[key] = row.copy()

        # Step 2: Process new sizes and create new rows
        for handle, colors in new_sizes.items():
            for color, sizes in colors.items():
                # (price_discount, price) = fetch_product_prices(pdp_link)
                # print(price_discount, price)
                key = (handle, color)
                if key in lookup:
                    base_row = lookup[key]  # Fetch the base row for this handle and color
                    for size in sizes:
                        new_row = base_row.copy()
                        new_row["Title"] = ""
                        new_row["Option2 Value"] = size  # Update size
                        new_row["Command"] = "MERGE"     # Update command to MERGE
                        new_row["Tags"] = ""
                        # new_row["Variant Price"] = price_discount,
                        # new_row["Variant Compare At Price"] = price,                        
                        new_row["Image Src"] = ""
                        new_row["Image Position"] = ""
                        new_row["Variant Inventory Qty"] = 1000  # Clear inventory for new rows
                        rows_to_add.append(new_row)
        # Step 3: Write only the new rows to the output CSV
        for row in rows_to_add:
            writer.writerow(row)
        print(f"Processing complete! New rows added and saved to {output_csv}")

if __name__ == "__main__":  

    # new_sizes["05070660"] = {}
    # new_sizes["05070660"]["Grey marl"] = (["M", "L"], "https://www.zara.com/in/en/soft-button-coat-p05070660.html?v1=423157370&v2=2419020")

    match_sizes_with_original("master_file.csv", "last_upload_master.csv", "removal.csv")
    add_new_sizes_to_csv("csv/master_upload.csv", "new_upload.csv")