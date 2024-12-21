import os
import json
import pandas as pd
import re
import orjson

# Set to track unique product_id + color_code combinations
unique_product_variants = set()

def extract_product_id(product_link):
    """
    Extract the product ID from the product link.
    """
    try:
        return product_link.split("-p")[-1].split(".")[0]
    except IndexError:
        return None

def extract_color_code(image_url):
    """
    Extract the color code from the image URL.
    """
    try:
        return image_url.split("/")[-1].split("-")[0][-3:]
    except IndexError:
        return None

def clean_price(price):
    """
    Extract the numerical price value from the price field.
    """
    match = re.sub(r"[^\d.]", "", price)
    return match or "0"

product_img_idx = {}

sku_id_to_cc = {}

# def master_csv_maker(product):
#     if create_master_csv:
#         if product_id not in sku_id_to_cc:
#             sku_id_to_cc[product_id] = []
#         sku_id_to_cc[product_id].append((color_code + "#" + product.get("color_code") + "#" + product.get("sizes", "")[:-1], product.get("gender", "")))
#     all_rows = []
#     for sku_id, col_sz_list in sku_id_to_cc.items():
#         cols_sz = ""
#         for i, (col_sz, gender) in enumerate(col_sz_list):
#             cols_sz += col_sz
#             if(i < len(col_sz_list) - 1): cols_sz += "|"
#         base_row = {
#             "sku_base": sku_id,
#             "cols_sz": cols_sz, 
#             "gender": gender
#         }
#         all_rows.append(base_row)
#     return all_rows

def format_shopify_csv(product):
    """
    Format a single product dictionary into Shopify-compatible CSV rows.
    """
    global unique_product_variants, product_img_idx, sku_id_to_cc
    rows = []
    product_id = extract_product_id(product.get("product_link", ""))
    image_urls = product.get("image_urls", "").split(",")  # Split image URLs
    del image_urls[-1]
    sz_dt = product.get("sizes", "")
    sizes = []
    if "," in sz_dt:
        sizes = sz_dt.split(",")  # Split sizes
        del sizes[-1]
    else:
        sizes = [sz_dt]
    color_code = product.get("color", "")
    if not product_id or not color_code:
        return rows  # Skip products without valid product IDs or color codes

    # Check for duplicates
    variant_key = f"{product_id}_{color_code}"
    if variant_key in unique_product_variants:
        print(f"[INFO] Skipping duplicate variant: {variant_key}")
        return rows
    unique_product_variants.add(variant_key)

    title = product.get("name", "")
    category = product.get("category", "")
    sub_category = product.get("subcategory", "")
    price = clean_price(product.get("price", ""))
    original_price = clean_price(product.get("original_price", "")) or price
    gender = product.get("gender", "")
    tags = f"{gender}, {category}, {sub_category}"
    if price != original_price:
        tags += ", Sale"

    # Initialize or reset image position tracker for this product
    if product_id not in product_img_idx:
        product_img_idx[product_id] = 1        

    # Format rows for Shopify
    for idx, size in enumerate(sizes):
        base_row = {
            "Handle": product_id,
            "Title": title if idx == 0 else "",
            "Body (HTML)": "",
            "Vendor": "Zara",
            "Product Category": "",
            "Type": category,
            "Command": "REPLACE",
            "Tags": tags if idx == 0 else "",
            "Published": "TRUE" if idx == 0 else "",
            "Option1 Name": "Color",
            "Option1 Value": color_code,
            "Option2 Name": "Size",
            "Option2 Value": size.strip(),
            "Option3 Name": "",
            "Option3 Value": "",
            "Variant SKU": "",
            "Variant Grams": "",
            "Variant Inventory Tracker": "shopify",
            "Variant Inventory Qty": 1000,
            "Variant Inventory Policy": "deny",
            "Variant Fulfillment Service": "manual",
            "Variant Price": price,
            "Variant Compare At Price": original_price,
            "Variant Requires Shipping": "TRUE",
            "Variant Taxable": "",
            "Variant Barcode": "",
            "Image Src": image_urls[idx] if idx < len(image_urls) else "",
            "Image Position": product_img_idx[product_id] if idx < len(image_urls) else "",
            "Image Alt Text": "",
            "Gift Card": "",
            "SEO Title": "",
            "SEO Description": "",
            "Google Shopping / Google Product Category": "",
            "Google Shopping / Gender": "",
            "Google Shopping / Age Group": "",
            "Google Shopping / MPN": "",
            "Google Shopping / AdWords Grouping": "",
            "Google Shopping / AdWords Labels": "",
            "Google Shopping / Condition": "",
            "Google Shopping / Custom Product": "",
            "Google Shopping / Custom Label 0": "",
            "Google Shopping / Custom Label 1": "",
            "Google Shopping / Custom Label 2": "",
            "Google Shopping / Custom Label 3": "",
            "Google Shopping / Custom Label 4": "",
            "Variant Image": image_urls[0] if image_urls else "",
            "Variant Weight Unit": "",
            "Variant Tax Code": "",
            "Cost per item": "",
            "Price / International": "",
            "Compare At Price / International": "",
            "Status": "active" if idx == 0 else "",
        }
        if idx < len(image_urls): product_img_idx[product_id] += 1
        rows.append(base_row)

    # Add extra rows for remaining images without size information
    for img_idx in range(len(sizes), len(image_urls)):
        extra_row = {
            "Handle": product_id,
            "Command": "REPLACE",
            "Image Src": image_urls[img_idx],
            "Image Position": product_img_idx[product_id],
        }
        product_img_idx[product_id] += 1
        rows.append(extra_row)

    return rows

def process_shopify_csv(json_file, csv_file):
    """
    Process a single JSON file and convert it to Shopify-compatible CSV.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_rows = []
        for product in data:
            all_rows.extend(format_shopify_csv(product))
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(all_rows)
        df.to_csv(csv_file, index=False, encoding="utf-8")
        print(f"Converted {json_file} to {csv_file}")
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

import orjson

def merge_json_files_fast(file1, file2, output_file):
    # Read and parse the first JSON file
    with open(file1, "rb") as f1:  # Read in binary mode for orjson
        data1 = orjson.loads(f1.read())  # Parse JSON
    
    # Read and parse the second JSON file
    with open(file2, "rb") as f2:
        data2 = orjson.loads(f2.read())
    
    # Merge the two lists
    merged_data = data1 + data2
    
    # Write the merged data to the output file
    with open(output_file, "wb") as fout:
        fout.write(orjson.dumps(merged_data, option=orjson.OPT_INDENT_2))  # Write JSON

# Example usage

def process_product_data(shopify_file, inventory_file, json_file, output_file):
    # Read Shopify product file
    df_shopify = pd.read_csv(shopify_file)
    
    # Filter out image rows (keeping only variant rows)
    df_variants = df_shopify[df_shopify['Option1 Value'].notna()].copy()
    
    # Read inventory file
    df_inventory = pd.read_csv(inventory_file)
    
    # Read JSON file
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    df_json = pd.json_normalize(json_data)
    
    # Ensure Handle is string type in both dataframes
    df_variants['Handle'] = df_variants['Handle'].astype(str)
    df_inventory['Handle'] = df_inventory['Handle'].astype(str)
    
    # Create matching keys for inventory
    df_variants['match_key'] = df_variants['Handle'] + '_' + \
                              df_variants['Option1 Value'].astype(str) + '_' + \
                              df_variants['Option2 Value'].astype(str)
    
    df_inventory['match_key'] = df_inventory['Handle'] + '_' + \
                               df_inventory['Option1 Value'].astype(str) + '_' + \
                               df_inventory['Option2 Value'].astype(str)
    
    # Match variants with inventory data
    df_merged = df_variants.merge(
        df_inventory[['ID', 'Variant ID', 'match_key']],
        on='match_key',
        how='left'
    )
    
    # Prepare JSON data for matching (handle and color)
    # Remove leading zeros from sku_id to match Handle format
    df_json['sku_id_cleaned'] = df_json['sku_id'].str.lstrip('0')
    df_json['json_match_key'] = df_json['sku_id_cleaned'] + '_' + df_json['color']
    
    # Create corresponding match key in merged data
    df_merged['json_match_key'] = df_merged['Handle'] + '_' + df_merged['Option1 Value'].astype(str)
    
    # Match with JSON data
    df_final = df_merged.merge(
        df_json[['json_match_key', 'product_link', 'color_code', 'gender']],
        on='json_match_key',
        how='left'
    )
    
    # Select and rename final columns
    columns_to_keep = [
        'Handle', 'Title', 'ID', 'Variant ID', 
        'Option1 Name', 'Option1 Value',  # Color
        'Option2 Name', 'Option2 Value',  # Size
        'Variant Price', 'Variant Compare At Price',
        'Variant Inventory Qty', 'Variant Image',
        'product_link', 'color_code', 'gender'
    ]
    
    df_final = df_final[columns_to_keep]
    
    df_final.to_csv(output_file, index=False)

# Main Execution
if __name__ == "__main__":
    # meant for new product csv creation
    json_file = "All_new.json"  # Replace with the actual JSON file path
    csv_file = "new_products_21-12-2024.csv"  # Replace with the desired CSV output path
    # meant for master csv creation
    create_master_csv = True
    if create_master_csv:
        variant_csv = "latest_masters/master_inventory_19-12-2024.csv"
        last_upload_csv = "latest_masters/master_upload_19-12-2024.csv"
        new_products = "latest_masters/new_products_19122024.csv"
        full_new_json = "full_new.json"
        merge_json_files_fast("latest_masters/All.json", "latest_masters/new_19122024.json", full_new_json)
        process_product_data(last_upload_csv, variant_csv, full_new_json, "master_merge.csv")
        print("Data processing complete. Check combined_product_data.csv")
    else:
        process_shopify_csv(json_file, csv_file)
