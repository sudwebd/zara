import csv
import json
import logging
import sys
import time
import requests

logging.basicConfig(filename=f"logs/inventory_fetch{time.time()}.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

def create_api_string(sku_base, colors, suf, gender="WOMAN"):
    s = "https://www.zara.com/in/en/store-stock?physicalStoreIds=16156"
    for color in colors:
        ref = f"&references={sku_base}{color}"
        for i in range(1, 8):
            s += ref + ("0" if(i < 10) else "") + str(i) + suf
        for i in range(26, 50, 2):
            s += ref + ("0" if(i < 10) else "") + str(i) + suf       
    s += f"&sectionName={gender}&ajax=true"
    return s

headers = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

def fetch_inventory(sku_base, colors, gender="WOMAN"):
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

def process_inventory_changes(master_file, output_removal_file, output_new_file):
    """
    Process inventory changes using the combined master file.
    
    Args:
        master_file: Path to our combined CSV file
        output_removal_file: Path to save items that are no longer in stock
        output_new_file: Path to save newly available items
    """
    # Group products by Handle and color_code
    products_by_handle = {}
    
    # Read the master file and organize data
    with open(master_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            handle = row['Handle']
            if handle not in products_by_handle:
                products_by_handle[handle] = {
                    'color_codes': set(),
                    'sizes_by_color': {},
                    'rows_by_key': {},
                    'product_link': row['product_link']
                }
            
            color = row['Option1 Value']
            color_code = row['color_code']
            size = row['Option2 Value']
            
            products_by_handle[handle]['color_codes'].add(color_code)
            if color not in products_by_handle[handle]['sizes_by_color']:
                products_by_handle[handle]['sizes_by_color'][color] = set()
            products_by_handle[handle]['sizes_by_color'][color].add(size)
            
            # Store the full row for later use
            key = f"{handle}_{color}_{size}"
            products_by_handle[handle]['rows_by_key'][key] = row

    # Process each product
    removed_items = []
    new_items = []
    
    for handle, product_data in products_by_handle.items():
        sku_base = handle.zfill(8)  # Pad with zeros to match Zara's format
        colors = list(product_data['color_codes'])
        
        # Fetch current inventory
        inventory_data = fetch_inventory(sku_base, colors)
        
        # Process inventory data
        current_sizes_by_color = {}
        for store in inventory_data.get('productAvailability', []):
            for item in store.get('availableProducts', []):
                color_code = item['reference'][-11:-8]
                size = item['size']
                
                if color_code not in current_sizes_by_color:
                    current_sizes_by_color[color_code] = set()
                current_sizes_by_color[color_code].add(size)

        # Compare with existing data and identify changes
        for color, existing_sizes in product_data['sizes_by_color'].items():
            color_code = next((code for code in colors if code in product_data['color_codes']), None)
            if not color_code:
                continue
                
            current_sizes = current_sizes_by_color.get(color_code, set())
            
            # Find removed sizes
            removed_sizes = existing_sizes - current_sizes
            for size in removed_sizes:
                key = f"{handle}_{color}_{size}"
                row = product_data['rows_by_key'].get(key)
                if row:
                    row = row.copy()
                    row['Variant Inventory Adjust'] = 0
                    removed_items.append(row)
            
            # Find new sizes
            new_sizes = current_sizes - existing_sizes
            for size in new_sizes:
                # Create new row based on existing color variant
                base_key = f"{handle}_{color}_{next(iter(existing_sizes))}"  # Get any existing size as template
                base_row = product_data['rows_by_key'].get(base_key)
                if base_row:
                    new_row = base_row.copy()
                    new_row['Option2 Value'] = size
                    new_row['Variant Inventory Qty'] = 1000
                    new_row['Command'] = 'MERGE'
                    new_items.append(new_row)

    # Write removed items
    if removed_items:
        write_removal_csv(output_removal_file, removed_items)
        
    # Write new items
    if new_items:
        write_new_sizes_csv(output_new_file, new_items)

def write_removal_csv(filename, rows):
    """
    Write rows to removal CSV with the exact required format.
    """
    fieldnames = [
        'ID', 'Handle', 'Variant ID', 'Option1 Name', 'Option1 Value', 
        'Option2 Name', 'Option2 Value', 'Variant Inventory Adjust', 
        'Variant Inventory Adjust'  # Duplicated field as per format
    ]
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            output_row = {
                'ID': row['ID'],
                'Handle': row['Handle'],
                'Variant ID': row['Variant ID'],
                'Option1 Name': 'Color',
                'Option1 Value': row['Option1 Value'],
                'Option2 Name': 'Size',
                'Option2 Value': row['Option2 Value'],
                'Variant Inventory Adjust': 0
            }
            writer.writerow(output_row)

def write_new_sizes_csv(filename, rows):
    """
    Write rows to new sizes CSV with the exact required format.
    """
    fieldnames = [
        'Handle', 'Vendor', 'Type',
        'Command', 'Published', 'Option1 Name', 'Option1 Value',
        'Option2 Name', 'Option2 Value', 'Variant Inventory Tracker',
        'Variant Inventory Qty', 'Variant Inventory Policy',
        'Variant Fulfillment Service', 'Variant Price', 'Variant Compare At Price',
        'Variant Requires Shipping', 'Variant Image', 'Status'
    ]
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            output_row = {
                'Handle': row['Handle'].zfill(8),  # Ensure 8 digits
                'Vendor': 'Zara',
                'Type': row.get('Type', ''),  # Get from original row if available
                'Command': 'MERGE',
                'Published': 'TRUE',
                'Option1 Name': 'Color',
                'Option1 Value': row['Option1 Value'],
                'Option2 Name': 'Size',
                'Option2 Value': row['Option2 Value'],
                'Variant Inventory Tracker': 'shopify',
                'Variant Inventory Qty': 1000,
                'Variant Inventory Policy': 'deny',
                'Variant Fulfillment Service': 'manual',
                'Variant Price': row['Variant Price'],
                'Variant Compare At Price': row['Variant Compare At Price'],
                'Variant Requires Shipping': 'TRUE',
                'Variant Image': row.get('Variant Image', ''),
                'Status': 'active'
            }
            writer.writerow(output_row)

def write_csv(filename, rows):
    """Helper function to write rows to CSV file."""
    if not rows:
        return
        
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    master_file = "master_merge.csv"  # Our new combined file
    output_removal_file = "random_tests/removal.csv"
    output_new_file = "random_tests/new_upload.csv"
    
    process_inventory_changes(master_file, output_removal_file, output_new_file)