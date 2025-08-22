import os

# === File Paths ===
ICON_PATH = os.path.join(os.path.dirname(__file__), "icons")

# Category structure
categories = {
    "OIL SEALS": {"MM": None, "INCH": None},
    "O-RINGS": {
        "NITRILE (NBR)": {"MM": None, "INCH": None},
        "SILICONE": {"MM": None, "INCH": None},
        "VITON (FKM)": {"MM": None, "INCH": None}
    },
    "O-CORDS": {
        "NITRILE (NBR)": {},
        "SILICONE": {},
        "VITON (FKM)": {},
        "POLYCORD": {}
    },
    "O-RING KITS": {},
    "PACKING SEALS": {
        "MONOSEALS": {"MM": None, "INCH": None},
        "WIPER SEALS": {"MM": None, "INCH": None},
        "WIPERMONO": {},
        "VEE PACKING": {"MM": None, "INCH": None},
        "ZF PACKING": {}
    },
    "MECHANICAL SHAFT SEALS": "COMING_SOON",
    "LOCK RINGS (CIRCLIPS)": {
        "INTERNAL": {"MM": None, "INCH": None},
        "EXTERNAL": {"MM": None, "INCH": None},
        "E-RINGS": {}
    },
    "V-RINGS": {"VS": {}, "VA": {}, "VL": {}},
    "QUAD RINGS (AIR SEALS)": {"MM": None, "INCH": None},
    "PISTON CUPS": {"PISTON CUPS": {}, "DOUBLE ACTION": {}},
    "OIL CAPS": "COMING_SOON",
    "RUBBER DIAPHRAGMS": "COMING_SOON",
    "COUPLING INSERTS": "COMING_SOON",
    "IMPELLERS": "COMING_SOON",
    "BUSHINGS (FLAT RINGS)": "COMING_SOON",
    "BALL BEARINGS": "COMING_SOON",
    "GREASE & SEALANTS": "COMING_SOON",
    "ETC. (SPECIAL)": "COMING_SOON"
}

# Icon mapping
icon_mapping = {
    "OIL SEALS": f"{ICON_PATH}\\oilseals.png",
    "O-RINGS": f"{ICON_PATH}\\orings.png",
    "O-CORDS": f"{ICON_PATH}\\o-ring cords.png",
    "O-RING KITS": f"{ICON_PATH}\\o-ring kits.png",
    "PACKING SEALS": f"{ICON_PATH}\\packing seals.png",
    "MECHANICAL SHAFT SEALS": f"{ICON_PATH}\\mechanical shaft seals.png",
    "LOCK RINGS (CIRCLIPS)": f"{ICON_PATH}\\lock rings.png",
    "V-RINGS": f"{ICON_PATH}\\v-rings.png",
    "QUAD RINGS (AIR SEALS)": f"{ICON_PATH}\\quad rings.png",
    "PISTON CUPS": f"{ICON_PATH}\\piston cups.png",
    "OIL CAPS": f"{ICON_PATH}\\oil caps.png",
    "RUBBER DIAPHRAGMS": f"{ICON_PATH}\\rubber diaphragms.png",
    "COUPLING INSERTS": f"{ICON_PATH}\\coupling inserts.png",
    "IMPELLERS": f"{ICON_PATH}\\impellers.png",
    "BUSHINGS (FLAT RINGS)": f"{ICON_PATH}\\bushings.png",
    "BALL BEARINGS": f"{ICON_PATH}\\ball bearings.png",
    "GREASE & SEALANTS": f"{ICON_PATH}\\grease and sealants.png",
    "ETC. (SPECIAL)": f"{ICON_PATH}\\special.png"
}

# Re-export GUI classes so old imports still work
from gui_home_page import HomePage, CategoryPage, ComingSoonPage
