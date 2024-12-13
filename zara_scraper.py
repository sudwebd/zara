import requests
import brotli
from bs4 import BeautifulSoup
import re
import os
import json
import atexit
import csv

json_data = []

def exit_handler():
    output_file = os.path.join(gender + "All.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4)    
    print(f"Saved {len(json_data)} products for gender {gender}")

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
        # print(f"[DEBUG] Content-Type Header: {response.headers.get('Content-Type')}")
        
        # Check Content-Encoding
        content_encoding = response.headers.get("content-encoding", "")
        # print(f"[DEBUG] Content-Encoding: {content_encoding}")
        
        raw_content = response.content

        # Decompress Brotli if indicated
        if content_encoding == "br":
            try:
                # print("[DEBUG] Brotli compression detected. Attempting decompression...")
                raw_content = brotli.decompress(raw_content)
                print("[DEBUG] Brotli decompression successful.")
            except brotli.error as e:
                print(f"[ERROR] Brotli decompression failed: {e}")
                print("[DEBUG] Falling back to raw content.")

        # Set encoding manually
        try:
            response_text = raw_content.decode("utf-8")
            print("[DEBUG] Response decoded successfully.")
        except UnicodeDecodeError as e:
            print(f"[ERROR] Unicode decode failed: {e}")
            response_text = raw_content.decode("latin-1", errors="replace")
            print("[DEBUG] Decoded using 'latin-1' with errors replaced.")
        
        # Save raw and decoded content for debugging
        with open("debug_raw_output.bin", "wb") as f:
            f.write(response.content)
        with open("debug_decoded_output.html", "w", encoding="utf-8") as f:
            f.write(response_text)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response_text, "html.parser")
        # print("[DEBUG] BeautifulSoup object created successfully.")
        
        # Debug: Output a snippet of the HTML
        # print(f"[DEBUG] HTML Snippet (first 500 chars):\n{response_text[:500]}")
        
        return soup

    except Exception as e:
        print(f"[ERROR] Failed to fetch or parse the page. Exception {e}")
        return None
    
def process_category(url):
    cat_soup = fetch_html_with_debugging(url)
    product_list = cat_soup.select('div.layout-content.layout-catalog-content--full ul.product-grid__product-list li.product-grid-product')
    print(f"**********Processing Category {category}**********")
    for product in product_list:
        if product.find_next('a'):
            print(f"Now processing product {product}")
            product_url = product.select_one('a')["href"]
            try:
                process_product(product_url)
            except Exception as e:
                print(f"[ERROR] Failed to process product {product_url}: {e}")
    
def process_product(url):
    product_soup = fetch_html_with_debugging(url)
    details = product_soup.select_one('div.layout.layout--grid-type-standard.layout-catalog.product-detail-view  div.layout-content.layout-catalog-content--full div.product-detail-view__main')
    sizes_txt = []
    sizes_num = []
    sizes_dt = details.select('div.new-size-selector.product-detail-info__new-size-selector ul.size-selector-sizes.size-selector-sizes--grid-gap li')
    for size in sizes_dt:
        s = size.select_one('div.size-selector-sizes-size__label').text
        sizes_txt.append(s)
        sizes_num.append(extract_size(s))

    reference_pre = "0" + details.select_one('button.product-color-extended-name__copy-action').text.replace("/", "")
    store_data = check_in_store(reference_pre, sizes_num).get("productAvailability", [])
    global json_data
    for store in store_data:
        size_avil = ""
        available_products = store.get("availableProducts", [])
        for product in available_products:
            size_avil += product.get("size") + ","
        # for a, b in store_data[0][1]:
        #     if a == "size":
        #         # size_avil.append(sizes["size"])
        #         size_avil += b + ","

        # print(store_data)
        # print(details.prettify())

        # sku_id = product_code = re.search(r'p(\d+)\.html', url).group(1)
        # print(sku_id)

        name = details.select_one('div.product-detail-view__side-bar h1').text

        price_discount_dt = details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.price__amount.price__amount--on-sale.price__amount--is-highlighted.price-current--with-background.price-current--is-highlighted span.price-current__amount span.money-amount__main')
        # price_discount_dt = details.find('span.price__amount--on-sale')
        # print(price_discount_dt)
        price_discount = re.sub(r"[^\d.,]", "", price_discount_dt.text) if price_discount_dt else "0"
        if price_discount != "0":
            price = re.sub(r"[^\d.,]", "", details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.price__amount--old-price-wrapper span.money-amount__main').text)
        else:    
            price = re.sub(r"[^\d.,]", "", details.select_one('div.product-detail-view__side-bar div.product-detail-info__price span.money-amount__main').text)
            price_discount = price

        sizes_dt = details.select('div.new-size-selector.product-detail-info__new-size-selector ul.size-selector-sizes.size-selector-sizes--grid-gap li')

        images_dt = details.select("div.product-detail-view__main-content div.product-detail-images__frame ul.product-detail-images__images li picture.media-image source:nth-of-type(1)")
        # images = []
        image_urls = ""
        url_pattern = r'https?://[^\s,]+'
        for image in images_dt:
            links = image.get("srcset")
            urls = re.findall(url_pattern, links)
            # images.append(urls[-1] if urls else None)
            image_urls += urls[-1] if urls else ""
            image_urls += ","
        # print(images)

        json_data.append({
            "category": category.lower(),
            "subcategory": sub_category.lower(),
            "name": name,
            "price": price_discount,
            "image_urls": image_urls,
            "product_link": url,
            "sizes": size_avil,  # Include store availability
            "gender": gender,
            "original_price": price
        })

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

# Example usage
# url = "https://www.zara.com/in/en/high-waist-trf-wide-leg-jeans-with-crossover-waistband-p00250232.html?v1=425257398&v2=2419235"

# category = "Jackets"
# gender = "man"
# sub_category = "Puffers"
# cat_url = "https://www.zara.com/in/en/man-outerwear-padded-l722.html?v1=2467342"
# # process_product(url)
# process_category(cat_url)

# def process_category(url):
#     print(f"Processing URL: {url}")

file_path = "categories.csv"  # Replace with the actual path to your CSV file

    # Open the CSV file and handle any encoding issues
with open(file_path, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    
    # Clean column names to remove potential spaces
    reader.fieldnames = [header.strip() for header in reader.fieldnames]

    tasks = []

    # Start processing rows
    for row in reader:
        # Extract cleaned values
        gender = row.get("Gender", "").strip()
        category = row.get("Category", "").strip()
        sub_category = row.get("Sub Category", "").strip()
        link = row.get("Link", "").strip()
        
        # Add to task queue
        try:
            process_category(link)
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to process {link}: {e}")


