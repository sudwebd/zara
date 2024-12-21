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
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import logging
from collections import deque
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import aiohttp
import asyncio
from queue import Queue
import pandas as pd

# Setup logging
logging.basicConfig(filename=f"logs/new_products_{time.time()}.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# Shared data and locks
json_data = []
processed_products = set()
master_skus = set()
data_lock = Lock()
session_lock = Lock()
api_lock = Lock()

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
}

# Configure session with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
session.mount("http://", adapter)
session.mount("https://", adapter)
session.headers.update(HEADERS)

def exit_handler():
    output_file = os.path.join("All.json")
    with data_lock:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)
        logging.info(f"Saved {len(json_data)} products")

atexit.register(exit_handler)

size_map = {
    'XS': '01', 'S': '02', 'M': '03', 'L': '04', 
    'XL': '05', 'XXL': '06', 'XXXL': '07', 'XXS': '08',
}

def extract_size(value):
    eu_match = re.search(r"EU\s*(\d+)", value, re.IGNORECASE)
    if eu_match:
        return eu_match.group(1)
    return size_map.get(value.strip().upper(), "Unknown")

async def check_in_store_async(product_pre, sizes, gender):
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "user-agent": HEADERS["user-agent"]
    }

    suf_list = ["I2024", "V2025"]
    async with aiohttp.ClientSession() as session:
        for suf in suf_list:
            base_url = "https://www.zara.com/in/en/store-stock?physicalStoreIds=16156&"
            for size in sizes:
                if size != "Unknown":
                    reference = f"references={product_pre}{size}-{suf}&"
                    base_url += reference
            base_url += f"sectionName={gender.upper()}&ajax=true"
            
            try:
                async with session.get(base_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("productAvailability", []):
                            return data
            except Exception as e:
                logging.info(f"Error fetching store availability: {e}")
                await asyncio.sleep(1)  # Add delay on error
    
    return {"productAvailability": []}

def process_product(url, category, sub_category, gender):
    """Process a single product URL"""
    try:
        sku_id = re.search(r'p(\d+)\.html', url).group(1)
        if sku_id in master_skus:
            logging.info(f"sku_id {sku_id} already on Shopin, skipping")
            return
        return
        with session_lock:
            response = session.get(url, headers=HEADERS)
            response.raise_for_status()
            product_soup = BeautifulSoup(response.content, 'html.parser')

        details = product_soup.select_one('div.layout-content.layout-catalog-content--full div.product-detail-view__main')
        if not details:
            return

        sizes_num = [extract_size(size.select_one('div.size-selector-sizes-size__label').text)
                    for size in details.select('ul.size-selector-sizes.size-selector-sizes--grid-gap li')]

        reference_pre = "0" + details.select_one('button.product-color-extended-name__copy-action').text.replace("/", "")
        
        # Run async store check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        store_data = loop.run_until_complete(check_in_store_async(reference_pre, sizes_num, gender))
        loop.close()

        if not store_data.get("productAvailability"):
            return

        # Extract product details and create entry
        color_dt = details.select_one('p[data-qa-qualifier="product-detail-info-color"]').text
        color = color_dt.split("|")[0].replace("Colour:", "").strip()
        color_code = color_dt.split("|")[1][-3:]

        product_id = f"{sku_id}{color_code}"
        
        with data_lock:
            if product_id in processed_products:
                return
            processed_products.add(product_id)

        # Create product entry
        name = details.select_one('div.product-detail-view__side-bar h1').text
        
        price_discount_dt = details.select_one('span.price__amount.price__amount--on-sale.price__amount--is-highlighted span.money-amount__main')
        price_discount = re.sub(r"[^\d.,]", "", price_discount_dt.text) if price_discount_dt else "0"
        
        if price_discount != "0":
            price = re.sub(r"[^\d.,]", "", details.select_one('span.price__amount--old-price-wrapper span.money-amount__main').text)
        else:    
            price = re.sub(r"[^\d.,]", "", details.select_one('span.money-amount__main').text)
            price_discount = price

        images_dt = details.select("div.product-detail-images__frame ul.product-detail-images__images li picture.media-image source:nth-of-type(1)")
        image_urls = ",".join(
            re.findall(r'https?://[^\s,]+', image.get("srcset", ""))[-1]
            for image in images_dt
            if re.findall(r'https?://[^\s,]+', image.get("srcset", ""))
        )

        size_avil = ",".join(product.get("size", "") 
                            for store in store_data.get("productAvailability", [])
                            for product in store.get("availableProducts", []))

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

        with data_lock:
            json_data.append(product_entry)
            logging.info(f"Added product {product_id} to dump")

    except Exception as e:
        logging.error(f"Error processing product {url}: {e}")
        time.sleep(1)  # Add delay on error

def slow_scroll(driver, scroll_pause_time=1):
    """Scroll the page slowly to load all content"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def process_categories(categories):
    """Process all categories using a single browser instance"""
    driver = None
    try:
        driver = uc.Chrome()
        
        for category_info in categories:
            try:
                url = category_info["Link"].strip()
                category = category_info["Category"].strip()
                sub_category = category_info["Sub Category"].strip()
                gender = category_info["Gender"].strip()
                
                logging.info(f"Processing category: {category}")
                
                # Load the category page
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Scroll to load all products
                slow_scroll(driver)
                
                # Get all product URLs
                product_elements = driver.find_elements(By.CSS_SELECTOR, 'ul.product-grid__product-list li.product-grid-product')
                v2 = url.split("v1=")[1]
                
                product_urls = []
                for product in product_elements:
                    try:
                        v1 = product.get_attribute("data-productid")
                        product_url = f"{product.find_element(By.CSS_SELECTOR, 'div.product-grid-product__figure a').get_attribute('href')}?v1={v1}&v2={v2}"
                        product_urls.append(product_url)
                    except Exception as e:
                        logging.error(f"Error extracting product URL: {e}")
                
                # Process products in parallel using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [
                        executor.submit(process_product, url, category, sub_category, gender)
                        for url in product_urls
                    ]
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logging.error(f"Error processing product: {e}")
                
                logging.info(f"Completed category: {category}")
                
            except Exception as e:
                logging.error(f"Error processing category {category_info['Category']}: {e}")
                continue  # Continue with next category on error
            
    except Exception as e:
        logging.error(f"Error initializing browser: {e}")
    finally:
        if driver:
            driver.quit()

def get_unique_handles_fast(csv_file):
    global master_skus
    """
    Very fast function to get unique handles from CSV file using pandas.
    
    Args:
        csv_file: Path to the combined CSV file
        
    Returns:
        list: List of unique handles
    """
    # Read only the Handle column
    handles = pd.read_csv(csv_file, usecols=['Handle'])['Handle'].unique()
    master_skus = [
        str(handle).zfill(8)
        for handle in handles.tolist()    
    ]

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    
    # Load master SKUs
    get_unique_handles_fast("master_merge.csv")
    print(master_skus)
    # if os.path.exists("master_csvs/master_file.csv"):
    #     with open("master_csvs/master_file.csv", "r", encoding="utf-8") as infile:
    #         master_skus = {row["sku_base"] for row in csv.DictReader(infile)}

    # Read categories
    with open("csv/categories_test.csv", mode="r", encoding="utf-8") as file:
        categories = list(csv.DictReader(file))
    
    # Process all categories with a single browser instance
    # process_categories(categories)
    
    logging.info("Scraping completed")