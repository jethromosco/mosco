BRAND_GROUPS = {
    "ACE": ("ACE", "USA"),
    "ARIZONA": ("ARIZONA", "USA"),
    "CHICAGO": ("CHICAGO", "USA"),
    "FREUDENBERG": ("FREUDENBERG", "GERMANY"),
    "GOODYEAR": ("GOODYEAR", "USA"),
    "KAWASAKI": ("KAWASAKI", "JAPAN"),
    "NOK": ("NOK", "JAPAN"),
    "SAMSUNG": ("SAMSUNG", "SOUTH KOREA"),
    "SKF": ("SKF", "SWEDEN"),
    "CORTLAND": ("CORTLAND", "USA"),
    "USIT": ("USIT", "USA"),
    "MERKEL": ("MERKEL", "GERMANY"),
    "TRELLEBORG": ("TRELLEBORG", "GERMANY"),
    "KACO": ("KACO", "GERMANY"),
    "EBRO": ("EBRO", "GERMANY"),
    "HALLITE": ("HALLITE", "USA"),
    "IDLER": ("IDLER", "USA"),
    "VULCAN": ("VULCAN", "USA"),
    "GARLOCK": ("GARLOCK", "USA"),
    "FREUDENBERG SEALING TECHNOLOGIES": ("FREUDENBERG", "GERMANY"),
    "HUTCHINSON": ("HUTCHINSON", "FRANCE"),
    "WIPER TECH": ("WIPER TECH", "UNKNOWN"),
}


def canonicalize_brand(raw_brand):
    """
    Convert raw brand name to canonical label and origin.
    Returns tuple of (canonical_label, origin)
    """
    if not raw_brand:
        return "", "UNKNOWN"
    
    # Normalize to uppercase for lookup
    normalized = str(raw_brand).strip().upper()
    
    # Direct match
    if normalized in BRAND_GROUPS:
        return BRAND_GROUPS[normalized]
    
    # Check substrings for partial matches
    for key, (label, origin) in BRAND_GROUPS.items():
        if key in normalized or normalized in key:
            return (label, origin)
    
    # Default: return the raw brand as canonical with UNKNOWN origin
    return (normalized, "UNKNOWN")
