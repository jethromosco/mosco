BRAND_GROUPS = {
	"JAPAN": {
		"LABEL": "NOK",
		"BRANDS": {"NOK", "NTC"},
		"ORIGIN": "Japan",
	},
	"TAIWAN": {
		"LABEL": "T.Y.",
		"BRANDS": {"NQK", "SOG", "CHO", "NAK", "TTO", "PHLE", "SKF", "N/B", "ERIKS"},
		"ORIGIN": "Taiwan",
	},
	"PHILIPPINES": {
		"LABEL": "MOS",
		"BRANDS": {"MOS"},
		"ORIGIN": "Philippines",
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