BRAND_GROUPS = {
    # Shared oil seal brands (used across categories)
    "NOK_JAPAN": {
        "LABEL": "NOK",
        "BRANDS": {"NOK", "NTC"},
        "ORIGIN": "Japan",
    },
    "TY_TAIWAN": {
        "LABEL": "T.Y.",
        "BRANDS": {
            "NQK", "SOG", "CHO", "NAK", "TTO", "PHLE", "SKF",
            "N/B", "ERIKS", "FOS", "TAIWAN", "SFK", "KOK", "NTK"
        },
        "ORIGIN": "Taiwan",
    },
    "MOS_PHILIPPINES": {
        "LABEL": "MOS",
        "BRANDS": {"MOS"},
        "ORIGIN": "(fab.)",
    },
    "MX_PHILIPPINES": {
        "LABEL": "MX",
        "BRANDS": {"MX"},
        "ORIGIN": "Local",
    },
    "JW_PHILIPPINES": {
        "LABEL": "JW",
        "BRANDS": {"JW"},
        "ORIGIN": "Local",
    },
    "MS_PHILIPPINES": {
        "LABEL": "MS",
        "BRANDS": {"MS"},
        "ORIGIN": "Local",
    },
    "NAT_USA": {
        "LABEL": "NAT",
        "BRANDS": {"NAT"},
        "ORIGIN": "U.S.",
    },
    "CR_USA": {
        "LABEL": "CR",
        "BRANDS": {"CR"},
        "ORIGIN": "U.S.",
    },
    "STEFA_SWEDEN": {
        "LABEL": "STEFA",
        "BRANDS": {"STEFA"},
        "ORIGIN": "Sweden",
    },
    "KACO_GERMANY": {
        "LABEL": "KACO",
        "BRANDS": {"KACO"},
        "ORIGIN": "Germany",
    },
    "ELRING_GERMANY": {
        "LABEL": "ELRING",
        "BRANDS": {"ELRING"},
        "ORIGIN": "Germany",
    },
    # Wiper-specific brands
    "ACE_USA": {
        "LABEL": "ACE",
        "BRANDS": {"ACE"},
        "ORIGIN": "USA",
    },
    "ARIZONA_USA": {
        "LABEL": "ARIZONA",
        "BRANDS": {"ARIZONA"},
        "ORIGIN": "USA",
    },
    "CHICAGO_USA": {
        "LABEL": "CHICAGO",
        "BRANDS": {"CHICAGO"},
        "ORIGIN": "USA",
    },
    "FREUDENBERG_GERMANY": {
        "LABEL": "FREUDENBERG",
        "BRANDS": {"FREUDENBERG", "FREUDENBERG SEALING TECHNOLOGIES"},
        "ORIGIN": "Germany",
    },
    "GOODYEAR_USA": {
        "LABEL": "GOODYEAR",
        "BRANDS": {"GOODYEAR"},
        "ORIGIN": "USA",
    },
    "KAWASAKI_JAPAN": {
        "LABEL": "KAWASAKI",
        "BRANDS": {"KAWASAKI"},
        "ORIGIN": "Japan",
    },
    "SAMSUNG_KOREA": {
        "LABEL": "SAMSUNG",
        "BRANDS": {"SAMSUNG"},
        "ORIGIN": "South Korea",
    },
    "CORTLAND_USA": {
        "LABEL": "CORTLAND",
        "BRANDS": {"CORTLAND"},
        "ORIGIN": "USA",
    },
    "USIT_USA": {
        "LABEL": "USIT",
        "BRANDS": {"USIT"},
        "ORIGIN": "USA",
    },
    "MERKEL_GERMANY": {
        "LABEL": "MERKEL",
        "BRANDS": {"MERKEL"},
        "ORIGIN": "Germany",
    },
    "TRELLEBORG_GERMANY": {
        "LABEL": "TRELLEBORG",
        "BRANDS": {"TRELLEBORG"},
        "ORIGIN": "Germany",
    },
    "EBRO_GERMANY": {
        "LABEL": "EBRO",
        "BRANDS": {"EBRO"},
        "ORIGIN": "Germany",
    },
    "HALLITE_USA": {
        "LABEL": "HALLITE",
        "BRANDS": {"HALLITE"},
        "ORIGIN": "USA",
    },
    "IDLER_USA": {
        "LABEL": "IDLER",
        "BRANDS": {"IDLER"},
        "ORIGIN": "USA",
    },
    "VULCAN_USA": {
        "LABEL": "VULCAN",
        "BRANDS": {"VULCAN"},
        "ORIGIN": "USA",
    },
    "GARLOCK_USA": {
        "LABEL": "GARLOCK",
        "BRANDS": {"GARLOCK"},
        "ORIGIN": "USA",
    },
    "HUTCHINSON_FRANCE": {
        "LABEL": "HUTCHINSON",
        "BRANDS": {"HUTCHINSON"},
        "ORIGIN": "France",
    },
    "WIPER_TECH_UNKNOWN": {
        "LABEL": "WIPER TECH",
        "BRANDS": {"WIPER TECH"},
        "ORIGIN": "Unknown",
    },
}


def canonicalize_brand(raw_brand):
	"""Return (canonical_label, origin) for a given brand string.
	If brand is not recognized, returns (normalized_brand, None).
	"""
	try:
		brand = (raw_brand or "").strip().upper()
		for group in BRAND_GROUPS.values():
			if brand in group["BRANDS"]:
				return group["LABEL"], group["ORIGIN"]
		return brand, None
	except Exception:
		return (raw_brand or "").strip().upper(), None
