BRAND_GROUPS = {
    "JAPAN": {
        "LABEL": "NOK",
        "BRANDS": {"NOK", "NTC"},
        "ORIGIN": "Japan",
    },
    "TAIWAN": {
        "LABEL": "T.Y.",
        "BRANDS": {
            "NQK", "SOG", "CHO", "NAK", "TTO", "PHLE", "SKF",
            "N/B", "ERIKS", "FOS", "TAIWAN", "SFK", "KOK", "NTK"
        },
        "ORIGIN": "Taiwan",
    },
    "PHILIPPINES": {
        "MOS": {
            "LABEL": "MOS",
            "BRANDS": {"MOS"},
            "ORIGIN": "Philippines",
        },
        "MX": {
            "LABEL": "MX",
            "BRANDS": {"MX"},
            "ORIGIN": "Philippines",
        },
        "JW": {
            "LABEL": "JW",
            "BRANDS": {"JW"},
            "ORIGIN": "Philippines",
        },
        "MS": {
            "LABEL": "MS",
            "BRANDS": {"MS"},
            "ORIGIN": "Philippines",
        },
    },
    "USA": {
        "NAT": {
            "LABEL": "NAT",
            "BRANDS": {"NAT"},
            "ORIGIN": "U.S.",
        },
        "CR": {
            "LABEL": "CR",
            "BRANDS": {"CR"},
            "ORIGIN": "U.S.",
        },
    },
    "SWEDEN": {
        "STEFA": {
            "LABEL": "STEFA",
            "BRANDS": {"STEFA"},
            "ORIGIN": "Sweden",
        },
        "ELRING": {
            "LABEL": "ELRING",
            "BRANDS": {"ELRING"},
            "ORIGIN": "Sweden",
        },
    },
    "GERMANY": {
        "KACO": {
            "LABEL": "KACO",
            "BRANDS": {"KACO"},
            "ORIGIN": "Germany",
        },
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