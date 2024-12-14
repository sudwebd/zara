import os
import json
import pandas as pd
import re

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

def format_shopify_csv(product):
    """
    Format a single product dictionary into Shopify-compatible CSV rows.
    """
    global unique_product_variants
    rows = []
    product_id = extract_product_id(product.get("product_link", ""))
    image_urls = product.get("image_urls", "").split(",")  # Split image URLs
    del image_urls[-1]
    sizes = product.get("sizes", "").split(",")  # Split sizes
    del sizes[-1]
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
            "Image Position": idx + 1 if idx < len(image_urls) else "",
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
        rows.append(base_row)

    # Add extra rows for remaining images without size information
    for img_idx in range(len(sizes), len(image_urls)):
        extra_row = {
            "Handle": product_id,
            "Command": "REPLACE",
            "Image Src": image_urls[img_idx],
            "Image Position": img_idx + 1,
        }
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

# Main Execution
if __name__ == "__main__":
    json_file = "ManAll.json"  # Replace with the actual JSON file path
    csv_file = "zara_Man.csv"  # Replace with the desired CSV output path
    process_shopify_csv(json_file, csv_file)
