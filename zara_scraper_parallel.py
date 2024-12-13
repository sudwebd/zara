import requests
import brotli
from bs4 import BeautifulSoup
import re
import os
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import atexit

# Tracking JSON data by gender
json_data_by_gender = {}
num_threads = 2  # Default number of concurrent threads

def exit_handler():
    for gender, data in json_data_by_gender.items():
        output_dir = os.path.join(gender)
        os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists
        output_file = os.path.join(output_dir, f"{gender}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Saved {len(data)} products for gender {gender}")

atexit.register(exit_handler)

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
}

def fetch_html_with_debugging(url):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        print(f"\n[DEBUG] Starting fetch for URL: {url}")
        response = session.get(url)
        print(f"[DEBUG] Response Status Code: {response.status_code}")
        print(f"[DEBUG] Content-Type Header: {response.headers.get('Content-Type')}")
        
        content_encoding = response.headers.get("content-encoding", "")
        print(f"[DEBUG] Content-Encoding: {content_encoding}")
        
        raw_content = response.content

        if content_encoding == "br":
            try:
                print("[DEBUG] Brotli compression detected. Attempting decompression...")
                raw_content = brotli.decompress(raw_content)
                print("[DEBUG] Brotli decompression successful.")
            except brotli.error as e:
                print(f"[ERROR] Brotli decompression failed: {e}")
                print("[DEBUG] Falling back to raw content.")

        try:
            response_text = raw_content.decode("utf-8")
            print("[DEBUG] Response decoded successfully.")
        except UnicodeDecodeError as e:
            print(f"[ERROR] Unicode decode failed: {e}")
            response_text = raw_content.decode("latin-1", errors="replace")
            print("[DEBUG] Decoded using 'latin-1' with errors replaced.")
        
        soup = BeautifulSoup(response_text, "html.parser")
        print("[DEBUG] BeautifulSoup object created successfully.")
        return soup

    except Exception as e:
        print(f"[ERROR] Failed to fetch or parse the page. Exception {e}")
        return None

def process_category(url, gender, category, sub_category):
    print(f"[INFO] Processing URL: {url} | Gender: {gender} | Category: {category} | Sub-category: {sub_category}")
    cat_soup = fetch_html_with_debugging(url)
    if not cat_soup:
        return

    product_list = cat_soup.select('ul.product-grid__product-list li.product-grid-product')

    for product in product_list:
        if product.find_next('a'):
            product_url = product.select_one('a')["href"]
            process_product(product_url, gender, category, sub_category)

def process_product(url, gender, category, sub_category):
    product_soup = fetch_html_with_debugging(url)
    if not product_soup:
        return

    details = product_soup.select_one('div.product-detail-view__main')
    if not details:
        print(f"[ERROR] Product details not found for {url}")
        return

    sizes_txt = []
    sizes_num = []
    sizes_dt = details.select('ul.size-selector-sizes li')
    for size in sizes_dt:
        s = size.select_one('div.size-selector-sizes-size__label').text
        sizes_txt.append(s)
        sizes_num.append(extract_size(s))

    name = details.select_one('h1').text.strip()

    price_element = details.select_one('span.money-amount__main')
    price = re.sub(r"[^\d.,]", "", price_element.text) if price_element else "0"

    images_dt = details.select("li picture.media-image source:nth-of-type(1)")
    image_urls = ",".join(
        re.findall(r'https?://[^\s,]+', image.get("srcset", ""))[-1]
        for image in images_dt
        if image
    )

    global json_data_by_gender
    if gender not in json_data_by_gender:
        json_data_by_gender[gender] = []

    json_data_by_gender[gender].append({
        "subcategory": sub_category.lower(),
        "category": category.lower(),
        "name": name,
        "price": price,
        "image_urls": image_urls,
        "product_link": url,
        "sizes": sizes_txt,
        "gender": gender,
    })

def extract_size(value):
    eu_match = re.search(r"EU\s*(\d+)", value, re.IGNORECASE)
    if eu_match:
        return eu_match.group(1)
    return size_map.get(value.strip().upper(), "Unknown")

size_map = {
    'XXL': '08',
    'XS': '01',
    'S': '02',
    'M': '03',
    'L': '04',
    'XL': '05',
}

def process_csv(file_path):
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = [(row["Gender"].strip().lower(), row["Category"].strip().lower(), row["Sub Category"].strip().lower(), row["Link"].strip()) for row in reader]
            return rows
    except Exception as e:
        print(f"[ERROR] Failed to process CSV: {e}")
        return []

def main():
    file_path = "categories.csv"  # Replace with the actual path to your CSV file
    rows = process_csv(file_path)

    if not rows:
        print("[ERROR] No rows to process. Exiting...")
        return

    tasks = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for gender, category, sub_category, link in rows:
            tasks.append(executor.submit(process_category, link, gender, category, sub_category))

        for future in as_completed(tasks):
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Task failed: {e}")

if __name__ == "__main__":
    main()
