import requests
import brotli
from bs4 import BeautifulSoup
import re
import sys, os
import json
import atexit
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import logging
logging.basicConfig(level=logging.INFO)
# Shared data and locks
json_data = []
processed_products = []
data_lock = Lock()
session_lock = Lock()
api_lock = Lock()

# Shared session
session = requests.Session()

def exit_handler():
    output_file = os.path.join(gender + "All.json")
    with data_lock:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)
        logging.info(f"Saved {len(json_data)} products for gender {gender}")

atexit.register(exit_handler)

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
}

def slow_scroll(driver, scroll_pause_time=1, scroll_step=300):
    total_height = driver.execute_script("return document.body.scrollHeight")
    current_position = 0

    while current_position < total_height:
        driver.execute_script(f"window.scrollBy(0, {scroll_step});")
        time.sleep(scroll_pause_time)
        current_position += scroll_step
        total_height = driver.execute_script("return document.body.scrollHeight")

def open_category(url, scroll):
    driver = uc.Chrome()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        if scroll == 1:
            slow_scroll(driver, scroll_pause_time=1, scroll_step=600)
        return driver
    except Exception as e:
        logging.info(f"Error: {e}")
        return None

def fetch_html_with_debugging(url):
    global session
    try:
        with session_lock:
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
    
    Args:
    - value (str): The size string.
    
    Returns:
    - str: Extracted size as a string.
    """
    # Match patterns like 'EU 32 (UK 4)'
    eu_match = re.search(r"EU\s*(\d+)", value, re.IGNORECASE)
    if eu_match:
        return eu_match.group(1)
    
    # If not 'EU ...', use the map for strings like 'L', 'XL', etc.
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

    # physicalStoreIds=9217&physicalStoreIds=16157&physicalStoreIds=9218

    for suf in suf_list:
        base_url = "https://www.zara.com/in/en/store-stock?physicalStoreIds=16156&" 

        for size in sizes:
            if size != "Unknown":
                reference = "references=" + product_pre + size + "-" + suf + "&"
                base_url += reference

        base_url += "sectionName=" + gender.upper() + "&ajax=true"

        logging.info(base_url)

        try:
            with api_lock:
                response = requests.get(base_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if len(data.get("productAvailability", [])):       
                    logging.info(f"[DEBUG] product {product_pre} FOUND in store")
                    return data
        except requests.RequestException as e:
            logging.info(f"Error fetching store availability for: {e}")
    logging.info(f"[TRACE] product {product_pre} NOT AVAILABLE in store")
    return {"productAvailability": []}

# Add this near the top of your script, after the imports
processed_products = []

def process_product(url):
    global processed_products, json_data
    sku_id = re.search(r'p(\d+)\.html', url).group(1)
    logging.info(f"Processing product URL: {url}")
    product_soup = fetch_html_with_debugging(url)
    if not product_soup:
        logging.info(f"Failed to create driver for {url}")
        return
    details = product_soup.select_one('div.layout.layout--grid-type-standard.layout-catalog.product-detail-view  div.layout-content.layout-catalog-content--full div.product-detail-view__main')
    sizes_num = []
    sizes_dt = details.select('div.new-size-selector.product-detail-info__new-size-selector ul.size-selector-sizes.size-selector-sizes--grid-gap li')
    for size in sizes_dt:
        s = size.select_one('div.size-selector-sizes-size__label').text
        sizes_num.append(extract_size(s))

    reference_pre = "0" + details.select_one('button.product-color-extended-name__copy-action').text.replace("/", "")
    store_data = check_in_store(reference_pre, sizes_num).get("productAvailability", [])
    
    # Move the product entry creation outside the store_data loop
    # This ensures we create a product entry even if store_data is empty
    if store_data:
        for store in store_data:
            color_dt = details.select_one('div.product-detail-view__side-bar div.product-detail-info__actions p[data-qa-qualifier="product-detail-info-color"]').text
            color = color_dt.split("|")[0]
            if "Colour" in color:
                color = color.split(":")[1].strip()
            else: 
                color = color.strip()
            color_code = color_dt.split("|")[1][-3:]    

            product_id = sku_id + color_code
            with data_lock:
                if product_id in processed_products:
                    logging.info(f"Duplicate product detected {product_id}, skipping")
                    return
                processed_products.append(product_id)

            size_avil = ""
            available_products = store.get("availableProducts", [])
            for product in available_products:
                size_avil += product.get("size") + ","

            name = details.select_one('div.product-detail-view__side-bar h1').text

            price_discount_dt = details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.price__amount.price__amount--on-sale.price__amount--is-highlighted.price-current--with-background.price-current--is-highlighted span.price-current__amount span.money-amount__main')
            price_discount = re.sub(r"[^\d.,]", "", price_discount_dt.text) if price_discount_dt else "0"
            if price_discount != "0":
                price = re.sub(r"[^\d.,]", "", details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.price__amount--old-price-wrapper span.money-amount__main').text)
            else:    
                price = re.sub(r"[^\d.,]", "", details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.money-amount__main').text)
                price_discount = price

            images_dt = details.select("div.product-detail-view__main-content div.product-detail-images__frame ul.product-detail-images__images li picture.media-image source:nth-of-type(1)")
            image_urls = ""
            url_pattern = r'https?://[^\s,]+'
            for image in images_dt:
                links = image.get("srcset")
                urls = re.findall(url_pattern, links)
                image_urls += urls[-1] if urls else ""
                image_urls += ","

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
                "original_price": price,
                "color": color,
                "color_code": color_code
            }

            # Append to shared JSON data safely
            with data_lock:
                json_data.append(product_entry)
                logging.info(f"Added product {product_id} to dump")
    else:
        # If no store data, you might want to log this or handle it differently
        logging.info(f"No store data found for product: {url}")

def process_category(url, scroll):
    driver = open_category(url, scroll)
    if not driver:
        logging.info(f"Failed to open category page: {url}")
        return
    v2 = url.split("v1=")[1]
    try:
        product_elements = driver.find_elements(By.CSS_SELECTOR, 'ul.product-grid__product-list li.product-grid-product')
        logging.info(f"**********Processing Category {category}**********")
        product_urls = []
        sku_id = ""
        for product in product_elements:
            try:
                v1 = product.get_attribute("data-productid")
                product_url_element = product.find_element(By.CSS_SELECTOR, "div.product-grid-product__figure a")
                
                sku_id = re.search(r'p(\d+)\.html', product_url_element.get_attribute("href")).group(1)   
                product_url = product_url_element.get_attribute("href") +  "?v1=" + v1 + "&v2=" + v2
                product_urls.append(product_url)
            except Exception as e:
                logging.info(f"[ERROR] Failed to extract product URL: {e}")

        # Process products in parallel
        
        # if sku_id == "05584361":
        with ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(process_product, product_urls)

    finally:
        driver.quit()

if __name__ == "__main__":
    file_path = "categories.csv"  # Replace with the actual path to your CSV file
    gender = "Woman"

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            category = row.get("Category", "").strip()
            sub_category = row.get("Sub Category", "").strip()
            link = row.get("Link", "").strip()
            process_category(link, scroll=1)
