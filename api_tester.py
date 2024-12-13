import requests
import time
import json
def fetch_store_availability():
    """
    Fetch store availability for a product in Bangalore based on its product link.
    """
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

    # # Extract product ID and article ID from the product link
    # try:
    #     # Example product_link: https://www2.hm.com/en_in/productpage.0979945003.html
    #     product_id = product_link.split("/")[-1].split(".")[1]  # Extract 0979945
    #     art_id = product_id[-3:]  # Extract the last three digits (003)
    #     product_id = product_id[:-3]  # Remaining part of product_id (0979945)
    # except IndexError:
    #     print(f"Error parsing product ID from product link: {product_link}")
    #     return []

    # API endpoint for "Find in Store"
    url = "https://www.zara.com/in/en/store-stock?physicalStoreIds=9217&physicalStoreIds=16156&physicalStoreIds=16157&physicalStoreIds=9218&references=0306721080001-V2025&references=0306721080002-V2025&references=0306721080003-V2025&references=0306721080004-V2025&references=0306721080005-V2025&references=0306721080008-V2025&sectionName=WOMAN&ajax=true"
    # params = {
    #     "latitude": "12.9715987",  # Bangalore's latitude
    #     "longitude": "77.5945627",  # Bangalore's longitude
    #     "radiusinmeters": "10000",  # Search radius in meters
    #     "maxnumberofstores": "100",
    #     "brand": "000",
    #     "channel": "02"
    # }

    # Send request to the "Find in Store" API
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # json_object = json.loads(data)
        print(data)
        
        # Indent keyword while dumping the
        # data decides to what level 
        # spaces the user wants.
        # print(json.dumps(json_object, indent = 1))
        # Parse the response for store availability
        # stores = []
        # for store in data.get("stores", []):
        #     available_sizes = [
        #         size for size in store.get("sizes", {}).get("size", []) if size.get("avaiQty", 0) > 0
        #     ]
        #     if available_sizes:
        #         stores.append({
        #             "name": store["name"],
        #             "sizes": available_sizes
        #         })

        # return stores
    except requests.RequestException as e:
        print(f"Error fetching store availability for: {e}")
        print(f"Sleeping for 10 minutes to avoid further blocks")
        time.sleep(10 * 60)
        return []
    
fetch_store_availability()
