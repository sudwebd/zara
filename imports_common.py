import requests
from bs4 import BeautifulSoup
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
import atexit

category_products_map = {}
def exit_handler():
    for category, product in category_products_map.items():
        # Save products to file
        output_file = os.path.join(category, "products.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(product, f, indent=4)

        print(f"Saved {len(product)} products for subcategory {category}")

atexit.register(exit_handler)

# Thread-safe shared data storage
scraped_data_lock = Lock()
scraped_data = []

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

BASE_URL = "https://www2.hm.com"

def scrape_hnm_category(type, dir, ranges):
    """Scrape the main category and get subcategory links."""
    base_url = f"https://www2.hm.com/en_in/{type}.html"
    output_dir = dir

    try:
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        get_category_link(soup, output_dir, ranges)
    except requests.RequestException as e:
        print(f"Error occurred while scraping main category: {e}")

def get_category_link(soup, folder, ranges):
    """Extract subcategory links from the main page."""
    categories = []
    for i in ranges:
        category_elements = soup.select('div#menu-label > ul > li:nth-of-type(' + str(i) +') ul > li')
    
        for category in category_elements:
            try:
                category_name = category.select_one('a').text.strip()
                if category_name == "View all" or category_name == "View All" or category_name == "Premium Selection" or category_name == "Sale" or category_name == "H&M Edition" or category_name == "Merch & Graphics" or category_name == "Sports": 
                    continue                  
                category_url = category.select_one('a').get('href')      
                categories.append({
                    'name': category_name,
                    'url': category_url
                })
            except Exception as e:
                print(f"Error parsing category: {e}")
                continue

    if not os.path.exists(folder):
        os.makedirs(folder)
    output_file = os.path.join(folder, "all_category.json")

    with open(output_file, "w") as f:
        json.dump(categories, f, indent=4)

    # Process subcategories
    scrape_subcategories(categories, folder)

def scrape_subcategories(categories, folder):
    """Scrape all subcategories in parallel."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for category in categories:
            futures.append(executor.submit(process_subcategory, category, folder))
        for future in as_completed(futures):
            try:
                future.result()  # Wait for all threads to complete
            except Exception as e:
                print(f"Error processing subcategory: {e}")

def process_subcategory(category, folder):
    global category_products_map       
    """Process an individual subcategory."""
    category_url = BASE_URL + category["url"]
    try:
        response = requests.get(category_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract products
        subcategory_name = category["name"]
        subcategory_folder = os.path.join(folder, subcategory_name)
        if not os.path.exists(subcategory_folder):
            os.makedirs(subcategory_folder)

        if subcategory_folder not in category_products_map:
            category_products_map[subcategory_folder] = []
        products = []
        page = 1
        while True:
            print(f"Scraping page {page} of subcategory {subcategory_name}...")
            page_url = f"{category_url}?page={page}"
            page_response = requests.get(page_url, headers=HEADERS)
            if page_response.status_code != 200:
                break

            page_soup = BeautifulSoup(page_response.content, 'html.parser')
            product_container = page_soup.select_one('div#products-listing-section ul')
            if not product_container:
                break

            product_items = product_container.find_all('li', recursive=False)
            for item in product_items:
                try:
                    product = process_product(item, subcategory_name)
                    if product:
                        products.append(product)
                        category_products_map[subcategory_folder].append(product)
                except Exception as e:
                    print(f"Error processing product: {e}")

            page += 1

        # Save products to file
        output_file = os.path.join(subcategory_folder, "products.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=4)

        print(f"Saved {len(products)} products for subcategory {subcategory_name}")
    except requests.RequestException as e:
        print(f"Error scraping subcategory {category['name']}: {e}")

# def process_product(item, subcategory_name):
#     """Extract product details."""
#     first_div = item.select_one('section > article > div:nth-of-type(1)')
#     second_div = item.select_one('section > article > div:nth-of-type(2)')

#     if first_div and second_div:
#         product_link = BASE_URL + first_div.select_one('ul > li > a').get("href", "")
#         img_urls = [img.get('src') for img in first_div.select('ul > li img') if img]
#         name = second_div.select_one('h2').text.strip()
#         prices = [price.text.strip().replace(',', '') for price in second_div.select('span')]
#         price = ', '.join(prices[-2:]) if prices else "N/A"

#         return {
#             "subcategory": subcategory_name,
#             "name": name,
#             "price": price,
#             "image_urls": img_urls,
#             "product_link": product_link
#         }

#     return None

# def fetch_store_availability(product_link):
#     """Fetch store availability for a product in Bangalore."""
#     headers = {
#         'accept': 'application/json',
#         'accept-language': 'en-GB,en;q=0.9',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36'
#     }

#     # Extract product ID and article ID from the product link
#     try:
#         product_id = product_link.split('/')[-1].split('.')[1]
#         art_id = product_id[-3:]
#         product_id = product_id[:-3]
#     except IndexError:
#         print(f"Error parsing product ID from the product link: {product_link}")
#         return []

#     # API endpoint for store availability
#     url = f"https://www2.hm.com/en_in/sis/in/{product_id}/{art_id}"
#     params = {
#         'latitude': '12.9715987',  # Latitude for Bangalore
#         'longitude': '77.5945627',  # Longitude for Bangalore
#         'radiusinmeters': '10000',
#         'maxnumberofstores': '100',
#         'brand': '000',
#         'channel': '02'
#     }

#     try:
#         response = requests.get(url, headers=headers, params=params)
#         response.raise_for_status()
#         data = response.json()

#         stores = []
#         for store in data.get("stores", []):
#             available_sizes = [
#                 size for size in store.get("sizes", {}).get("size", []) if size.get("avaiQty", 0) > 0
#             ]
#             if available_sizes:
#                 stores.append({
#                     "name": store["name"],
#                     "sizes": available_sizes
#                 })

#         return stores
#     except requests.RequestException as e:
#         print(f"Error fetching store availability for {product_link}: {e}")
#         return []


def process_product(item, subcategory_name):
    """Extract product details and fetch store availability."""
    first_div = item.select_one('section > article > div:nth-of-type(1)')
    second_div = item.select_one('section > article > div:nth-of-type(2)')
    if first_div and second_div:
        product_link = first_div.select_one('ul > li > a').get("href", "")
        # Fetch store availability
        stores = fetch_store_availability(product_link)
        if(len(stores)):        
            img_urls = [img.get('src') for img in first_div.select('ul > li img') if img]
            name = second_div.select_one('h2').text.strip()
            # prices = [price.text.strip().replace(',', '') for price in second_div.select('span')]
            # price = ', '.join(prices[-2:]) if prices else "N/A"
            # price = second_div.select('span:nth-of-type(1)').text.strip().replace(',', '')
            current_price = ""
            original_price = ""
            for price_span in second_div.select('span'):
                price = price_span.text.strip().replace(',', '')
                if(price[:3] != "Rs."): break
                if(current_price == ""): current_price = price
                else: original_price = price
            category_hierarichy = fetch_category_hierarchy(product_link)
            return {
                "subcategory": subcategory_name,
                "name": name,
                "price": current_price,
                "image_urls": img_urls,
                "product_link": product_link,
                "stores": stores,  # Include store availability
                "category_hierarichy": category_hierarichy,
                "original_price": original_price
            }

    return None

def fetch_category_hierarchy(product_link):
    """
    Fetch the category hierarchy for the given product link.
    """
    try:
        response = requests.get(product_link, headers=HEADERS)
        response.raise_for_status()
        product_soup = BeautifulSoup(response.content, 'html.parser')
        # print("Fetching Hierarchy: Successfully fetched page content.")

        levels = product_soup.select('nav > ol > li')
        if not levels:
            print("Fetching Hierarchy: No levels found.")
            return ""

        category_level = ""
        for level in levels:
            try:
                # Check for either <a> or <span> tag and extract the text
                name = None
                if level.select_one('a'):
                    name = level.select_one('a').text.strip()
                elif level.select_one('span'):
                    name = level.select_one('span').text.strip()

                # Skip "HM.com" or other undesired entries
                if name and name != "HM.com":
                    category_level += f"/{name}"
            except Exception as e:
                print(f"Error parsing category hierarchy: {e}")
                continue

        return category_level
    except Exception as e:
        print(f"Error fetching category hierarchy for {product_link}: {e}")
        return ""

def fetch_store_availability(product_link):
    """
    Fetch store availability for a product in Bangalore based on its product link.
    """
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "referer": product_link,
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    # Extract product ID and article ID from the product link
    try:
        # Example product_link: https://www2.hm.com/en_in/productpage.0979945003.html
        product_id = product_link.split("/")[-1].split(".")[1]  # Extract 0979945
        art_id = product_id[-3:]  # Extract the last three digits (003)
        product_id = product_id[:-3]  # Remaining part of product_id (0979945)
    except IndexError:
        print(f"Error parsing product ID from product link: {product_link}")
        return []

    # API endpoint for "Find in Store"
    url = f"https://www2.hm.com/en_in/sis/in/{product_id}/{art_id}"
    params = {
        "latitude": "12.9715987",  # Bangalore's latitude
        "longitude": "77.5945627",  # Bangalore's longitude
        "radiusinmeters": "10000",  # Search radius in meters
        "maxnumberofstores": "100",
        "brand": "000",
        "channel": "02"
    }

    # Send request to the "Find in Store" API
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Parse the response for store availability
        stores = []
        for store in data.get("stores", []):
            available_sizes = [
                size for size in store.get("sizes", {}).get("size", []) if size.get("avaiQty", 0) > 0
            ]
            if available_sizes:
                stores.append({
                    "name": store["name"],
                    "sizes": available_sizes
                })

        return stores
    except requests.RequestException as e:
        print(f"Error fetching store availability for {product_link}: {e}")
        print(f"Sleeping for 10 minutes to avoid further blocks")
        time.sleep(10 * 60)
        return []

def scrape_hnm_categories_parallel(dir):
    """Main function to scrape all categories in parallel."""
    with open(f"{dir}/all_category.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scrape_data, category["name"]) for category in categories]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing category: {e}")

def scrape_data(category_name):
    """Scrape individual category data."""
    print(f"Scraping data for category: {category_name}")

def start_scraper(type, dir, ranges):
     # Step 1: Scrape main category and subcategories
    scrape_hnm_category(type, dir, ranges)

    # Step 2: Scrape products in parallel
    scrape_hnm_categories_parallel(dir)
