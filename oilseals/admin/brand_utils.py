BRAND_GROUPS = {
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
        "ORIGIN": "Philippines",
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