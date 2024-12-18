import re

size_map = {
    'XS': '01',
    'S': '02',
    'M': '03',
    'L': '04', 
    'XL': '05',
    'XXL': '06',
    'XXXL': '07',
    'XXS': '08',
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