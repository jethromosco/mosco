from typing import Dict, List, Tuple, Any
from ..database import connect_db
import tkinter as tk

LOW_STOCK_THRESHOLD = 5
OUT_OF_STOCK = 0

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


def parse_number(val: Any) -> float:
    try:
        return float(val)
    except Exception:
        return 0.0


def format_display_value(value: Any) -> str:
    value_str = str(value).strip()
    if "/" in value_str:
        return value_str
    try:
        num = float(value_str)
        return str(int(num)) if num.is_integer() else str(num)
    except ValueError:
        return value_str


def convert_mm_to_inches_display(raw_value: str) -> Tuple[str, bool]:
    text = ""
    is_error = False
    raw = (raw_value or "").replace("mm", "").strip()
    if not raw:
        return text, is_error

    def mm_to_inches(mm: float) -> float:
        return mm * 0.0393701

    try:
        parts = raw.split("/")
        inches_list: List[str] = []
        for part in parts:
            if not part.strip():
                continue
            mm_val = float(part.strip())
            inches = mm_to_inches(mm_val)
            inches_list.append(f"{inches:.3f}")
        text = "/".join(inches_list) + '"'
    except ValueError:
        text = "⚠ Invalid input"
        is_error = True
    return text, is_error


def _build_query_and_params(search_filters: Dict[str, str]) -> Tuple[str, List[Any]]:
    query = (
        """SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price FROM products WHERE 1=1"""
    )
    params: List[Any] = []
    for key, val in search_filters.items():
        val = (val or "").strip()
        if not val:
            continue

        if key == "brand":
            # Replace brand with canonical label for searching but also
            # allow matching the raw input. Some DB rows store raw brands
            # (e.g., NTK) while users may search using canonical labels
            # (e.g., T.Y.). Match either.
            canonical_label, _ = canonicalize_brand(val)
            # Match canonical label OR the raw/partial value (case-insensitive)
            query += " AND ( UPPER(brand) = UPPER(?) OR UPPER(brand) LIKE UPPER(?) )"
            params.extend([canonical_label, f"{val}%"])
            continue

        if key in ("id", "od", "th"):
            if val.isdigit():
                query += f" AND ( {key} = ? OR {key} LIKE ? OR {key} LIKE ? )"
                params.extend([val, f"{val}.%", f"{val}/%"])
            else:
                query += f" AND {key} LIKE ?"
                params.append(f"{val}%")
        else:
            query += f" AND UPPER({key}) LIKE UPPER(?)"
            params.append(f"{val}%")

    return query, params


def _fetch_products(search_filters: Dict[str, str]) -> List[Tuple[Any, ...]]:
    query, params = _build_query_and_params(search_filters)
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
    return rows


def _fetch_all_transactions() -> List[Tuple[Any, ...]]:
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT type, id_size, od_size, th_size, brand, quantity, is_restock FROM transactions ORDER BY date ASC"""
        )
        rows = cur.fetchall()
    return rows


def _compute_stock_map(all_transactions: List[Tuple[Any, ...]]) -> Dict[Tuple[str, str, str, str], int]:
    stock_map: Dict[Tuple[str, str, str, str, str], int] = {}
    for row in all_transactions:
        # Expect: type, id, od, th, brand, quantity, is_restock
        type_, id_raw, od_raw, th_raw, brand, quantity, is_restock = row
        key = (type_, id_raw, od_raw, th_raw, str(brand).strip().upper())
        if is_restock == 2:
            stock_map[key] = int(quantity)
        else:
            stock_map[key] = stock_map.get(key, 0) + int(quantity)
    return stock_map


def _parse_thickness_sort(th_raw: Any) -> Tuple[float, float]:
    val = str(th_raw).strip()
    if "/" in val:
        try:
            main, sub = map(float, val.split("/", 1))
            return (main, sub)
        except Exception:
            try:
                return (float(val.split("/")[0]), 0.0)
            except ValueError:
                return (0.0, 0.0)
    else:
        try:
            return (float(val), 0.0)
        except Exception:
            return (0.0, 0.0)


def _parse_multi_component_sort(val: Any) -> Tuple[float, float]:
    """Parse ID/OD values for sorting.
    If value contains a slash, treat it as two separate components (like TH).
    Returns a tuple (primary, secondary) where secondary is 0.0 if missing or invalid.
    """
    s = str(val).strip()
    if "/" in s:
        try:
            a, b = s.split("/", 1)
            a_f = float(a) if a.strip() else 0.0
            b_f = float(b) if b.strip() else 0.0
            return (a_f, b_f)
        except Exception:
            try:
                return (float(s.split("/")[0]), 0.0)
            except Exception:
                return (0.0, 0.0)
    else:
        try:
            return (float(s), 0.0)
        except Exception:
            return (0.0, 0.0)


def stock_filter_matches(qty: int, stock_filter: str) -> bool:
    if stock_filter == "Low Stock":
        return 0 < qty <= LOW_STOCK_THRESHOLD
    if stock_filter == "Out of Stock":
        return qty == OUT_OF_STOCK
    if stock_filter == "In Stock":
        return qty > OUT_OF_STOCK
    return True


def build_products_display_data(
    search_filters: Dict[str, str],
    sort_by: str,
    stock_filter: str
) -> List[Tuple[Any, ...]]:
    """Return list of tuples for display and sorting.
    Visible tuple layout: (items_display, part_no, origin, notes, qty, price_str)
    Hidden/raw sizes appended for sorting: id_raw, od_raw, th_raw
    """
    products = _fetch_products(search_filters)
    all_transactions = _fetch_all_transactions()
    stock_map = _compute_stock_map(all_transactions)

    display_data: List[Tuple[Any, ...]] = []
    for row in products:
        type_, id_raw, od_raw, th_raw, brand, part_no, origin, notes, price = row
        key = (type_, id_raw, od_raw, th_raw, str(brand).strip().upper())
        qty = stock_map.get(key, 0)
        if not stock_filter_matches(qty, stock_filter):
            continue
        # Build size with hyphens for the compact Items view (e.g. 4-19-10)
        size_hyphen = f"{format_display_value(id_raw)}-{format_display_value(od_raw)}-{format_display_value(th_raw)}"
        # Items column should show: TYPE SIZE BRAND  (e.g. SC 4-19-10 MOS)
        items_display = f"{type_} {size_hyphen} {brand}".strip()
        display_data.append(
            (
                items_display,
                part_no,
                origin,
                notes,
                qty,
                f"₱{float(price):.2f}",
                id_raw,
                od_raw,
                th_raw,
            )
        )

    if sort_by == "Size":
        # Sort by ID then OD then TH. For ID/OD that contain '/', treat them as
        # multi-component values (primary/secondary) instead of attempting numeric
        # conversion that would fail or be interpreted incorrectly.
        def _size_key(item):
            # display_data tuple layout: (items, part_no, origin, notes, qty, price_str, id_raw, od_raw, th_raw)
            id_raw = item[6]
            od_raw = item[7]
            th_raw = item[8]
            id_primary, id_secondary = _parse_multi_component_sort(id_raw)
            od_primary, od_secondary = _parse_multi_component_sort(od_raw)
            th_primary, th_secondary = _parse_thickness_sort(th_raw)
            return (id_primary, id_secondary, od_primary, od_secondary, th_primary, th_secondary)

        display_data.sort(key=_size_key)
    elif sort_by == "Quantity":
        # qty is at index 4 in the new tuple
        display_data.sort(key=lambda x: x[4], reverse=True)

    return display_data


def validate_admin_password(password: str) -> bool:
    """Validate admin password"""
    return password.strip() == "1"


def parse_size_string(size_str: str) -> Tuple[str, str, str]:
    """Parse size string in format 'id×od×th' or 'id-od-th' and return (id, od, th)"""
    try:
        size_clean = size_str.replace("×", "-").replace("x", "-")
        parts = size_clean.split("-")
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), parts[2].strip()
        else:
            return "", "", ""
    except Exception:
        return "", "", ""


def create_product_details(item_values: List[Any]) -> Dict[str, Any]:
    """Create product details dictionary from tree item values.
    Expects visible values: items_display, part_no, origin, notes, qty, price_str
    """
    if len(item_values) < 6:
        return {}
    # item_values[0] is now the combined Items display: "TYPE SIZE BRAND"
    items_str = str(item_values[0])
    parts = items_str.split()
    if len(parts) >= 3:
        type_val = parts[0]
        brand_val = parts[-1]
        size_part = " ".join(parts[1:-1])
    elif len(parts) == 2:
        type_val = parts[0]
        size_part = parts[1]
        brand_val = ""
    else:
        return {}

    id_, od, th = parse_size_string(size_part)

    return {
        "type": type_val,
        "id": id_,
        "od": od,
        "th": th,
        "brand": str(brand_val).strip().upper(),
        "part_no": item_values[1],
        "country_of_origin": item_values[2],
        "notes": item_values[3],
        "quantity": item_values[4],
        "price": float(str(item_values[5]).replace("₱", ""))
    }


def get_stock_tag(qty: int) -> str:
    """Get stock status tag based on quantity"""
    if qty < 0 or qty == OUT_OF_STOCK:  # Explicitly handle negative OR zero
        return "out"
    elif qty <= LOW_STOCK_THRESHOLD:
        return "low"
    else:
        return "normal"


def should_uppercase_field(field_name: str) -> bool:
    """Check if a field should be automatically uppercased"""
    return field_name in ["type", "brand", "part_no"]
