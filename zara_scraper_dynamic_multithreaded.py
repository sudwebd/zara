import requests
import brotli
from bs4 import BeautifulSoup
import re
import os
import json
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from multiprocessing import Pool, Manager, Lock

gender = "Man"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
}

size_map = {
    'XXL': '08',
    'XS': '01',
    'S': '02',
    'M': '03',
    'L': '04',
    'XL': '05',
}

def slow_scroll(driver, scroll_pause_time=1, scroll_step=300):
    total_height = driver.execute_script("return document.body.scrollHeight")
    current_position = 0

    while current_position < total_height:
        driver.execute_script(f"window.scrollBy(0, {scroll_step});")
        time.sleep(scroll_pause_time)
        current_position += scroll_step
        total_height = driver.execute_script("return document.body.scrollHeight")

def get_driver():
    return uc.Chrome()

def open_category(url, retries=3):
    """
    Opens a category page using Selenium with retries for connection issues.
    Each call gets its own driver and quits it after use.
    """
    for attempt in range(retries):
        try:
            driver = get_driver()
            driver.get(url)
            wait = WebDriverWait(driver, 20)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            slow_scroll(driver, scroll_pause_time=1, scroll_step=600)
            return driver
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"[ERROR] Failed to open category page after {retries} attempts: {url}")
                return None

def extract_size(value):
    """
    Extract numeric size for 'EU ...' format or map string-only sizes.
    """
    eu_match = re.search(r"EU\s*(\d+)", value, re.IGNORECASE)
    if eu_match:
        return eu_match.group(1)
    return size_map.get(value.strip().upper(), "Unknown")

def check_in_store(product_pre, sizes):
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    suf_list = ["I2024", "V2025"]

    for suf in suf_list:
        base_url = "https://www.zara.com/in/en/store-stock?physicalStoreIds=16156&"
        for size in sizes:
            if size != "Unknown":
                reference = "references=" + product_pre + size + "-" + suf + "&"
                base_url += reference

        base_url += "sectionName=" + gender.upper() + "&ajax=true"

        print(base_url)

        try:
            response = requests.get(base_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if len(data.get("productAvailability", [])):       
                print(f"[DEBUG] product {product_pre} FOUND in store")
                return data
        except requests.RequestException as e:
            print(f"Error fetching store availability for: {e}")
    print(f"[TRACE] product {product_pre} NOT AVAILABLE in store")
    return {"productAvailability": []}

def fetch_html_with_debugging(url, retries=3):
    """
    Fetches the HTML content of a page with retry logic for connection issues.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    for attempt in range(retries):
        try:
            print(f"\n[DEBUG] Starting fetch for URL: {url}")
            response = session.get(url, timeout=20)
            print(f"[DEBUG] Response Status Code: {response.status_code}")

            # Brotli decompression if needed
            content_encoding = response.headers.get("content-encoding", "")
            raw_content = response.content
            if content_encoding == "br":
                raw_content = brotli.decompress(raw_content)
                print("[DEBUG] Brotli decompression successful.")

            response_text = raw_content.decode("utf-8")
            return BeautifulSoup(response_text, "html.parser")
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"[ERROR] Failed to fetch page after {retries} attempts: {url}")
                return None

def process_product(url, gender, category, sub_category, json_data, data_lock):
    product_soup = fetch_html_with_debugging(url)
    if not product_soup:
        print(f"Failed to fetch page for {url}")
        return

    details = product_soup.select_one('div.product-detail-view__main')
    if not details:
        print(f"No product details found for {url}")
        return

    sizes_num = []
    sizes_dt = details.select('ul.size-selector-sizes li')
    for size in sizes_dt:
        s = size.select_one('div.size-selector-sizes-size__label').text
        sizes_num.append(extract_size(s))

    reference_pre = "0" + details.select_one('button.product-color-extended-name__copy-action').text.replace("/", "")
    store_data = check_in_store(reference_pre, sizes_num).get("productAvailability", [])

    for store in store_data:
        size_avil = ""
        available_products = store.get("availableProducts", [])
        for product in available_products:
            size_avil += product.get("size") + ","

        name = details.select_one('h1').text.strip()
        price_discount_dt = details.select_one('span.money-amount__main')
        price_discount = re.sub(r"[^\d.,]", "", price_discount_dt.text) if price_discount_dt else "0"

        images_dt = details.select("ul.product-detail-images__images li source:nth-of-type(1)")
        image_urls_list = []
        for image in images_dt:
            srcset = image.get("srcset", "")
            found_urls = re.findall(r'https?://[^\s,]+', srcset)
            image_urls_list.extend(found_urls)
        image_urls = ",".join(image_urls_list)

        sku_id = re.search(r'p(\d+)\.html', url).group(1)
        color_dt = details.select_one('p.product-color-extended-name').text
        color = color_dt.split("|")[0].strip()
        color_code = color_dt.split("|")[1][-3:].strip()

        product_entry = {
            "category": category.lower(),
            "subcategory": sub_category.lower(),
            "name": name,
            "price": price_discount,
            "image_urls": image_urls,
            "product_link": url,
            "sku_id": sku_id,
            "sizes": size_avil,
            "gender": gender,
            "color": color,
            "color_code": color_code
        }

        with data_lock:
            json_data.append(product_entry)

def process_category(row, json_data, data_lock):
    try:
        category = row["Category"].strip()
        sub_category = row["Sub Category"].strip()
        url = row["Link"].strip()

        driver = open_category(url)
        if not driver:
            print(f"Failed to create driver for {url}")
            return

        try:
            product_elements = driver.find_elements(By.CSS_SELECTOR,
                                                    'ul.product-grid__product-list li.product-grid-product')
            print(f"**********Processing Category {category} | Sub-category {sub_category}**********")
            for product in product_elements:
                try:
                    product_url_element = product.find_element(By.TAG_NAME, "a")
                    product_url = product_url_element.get_attribute("href")
                    print(f"Processing product URL: {product_url}")
                    process_product(product_url, gender, category, sub_category, json_data, data_lock)
                except Exception as e:
                    print(f"[ERROR] Failed to process product element: {e}")
        finally:
            driver.quit()
    except Exception as e:
        print(f"[ERROR] Failed to process category row: {e}")

def main():
    file_path = "categories.csv"
    if not os.path.exists(file_path):
        print(f"[ERROR] CSV file not found: {file_path}")
        return

    # Use a Manager to share the json_data list and data_lock across processes
    with Manager() as manager:
        json_data = manager.list()
        data_lock = manager.Lock()

        # Read all rows first
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            reader.fieldnames = [header.strip() for header in reader.fieldnames]
            rows = list(reader)

        # Create a pool of worker processes. Adjust 'processes=5' as needed.
        with Pool(processes=5) as pool:
            # Use starmap to pass multiple arguments to process_category
            pool.starmap(process_category, [(row, json_data, data_lock) for row in rows])

        # After all processes finish, save the aggregated json_data
        output_file = os.path.join(gender + "All.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(list(json_data), f, indent=4)
        print(f"Saved {len(json_data)} products for gender {gender}")

if __name__ == "__main__":
    main()
