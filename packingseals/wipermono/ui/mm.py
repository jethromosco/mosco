from typing import Dict, List, Tuple, Any

from ..database import connect_db
from utils.search_helpers import search_products_with_closest

LOW_STOCK_THRESHOLD = 5
OUT_OF_STOCK = 0
UNKNOWN_STOCK = None  # Special marker for unknown/insufficient stock

# Module-level flag to track if last search used closest alternatives
_last_search_was_closest = False
_last_search_status_label = None

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
    """Fetch products with automatic fallback to closest sizes.
    
    Returns exact matches first. If none found and search is size-only,
    returns closest alternatives (±1 margin).
    
    Sets module-level flags:
    - _last_search_was_closest: True if showing closest alternatives
    - _last_search_status_label: Custom label for closest results
    """
    global _last_search_was_closest, _last_search_status_label
    
    # Reset flags
    _last_search_was_closest = False
    _last_search_status_label = None
    
    # Get exact match products
    query, params = _build_query_and_params(search_filters)
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        exact_rows = cur.fetchall()
        
        # Use shared search logic to check for closest alternatives
        brand_filter = (search_filters.get("brand") or "").strip() or None
        results, is_closest, label = search_products_with_closest(
            conn,
            search_filters,
            exact_rows,
            brand_filter
        )
    
    # Update module flags for the GUI to use
    if is_closest:
        _last_search_was_closest = True
        _last_search_status_label = label
        print(f"[MM-SEARCH] Using closest size alternatives")
    
    return results


def get_last_search_status_label() -> Tuple[bool, str]:
    """Get the status label override for last search.
    
    Returns:
        Tuple of (was_closest_search, status_label_override)
        - was_closest_search: True if showing closest alternatives
        - status_label_override: Override text for status label ("Exact size not available...") or empty string
    """
    return _last_search_was_closest, _last_search_status_label or ""


def _fetch_all_transactions() -> List[Tuple[Any, ...]]:
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT type, id_size, od_size, th_size, brand, quantity, is_restock FROM transactions ORDER BY date ASC"""
        )
        rows = cur.fetchall()
    return rows


def apply_stock_transaction(current_stock: Any, transaction_qty: int, is_restock: bool) -> Any:
    """Apply a transaction to current stock following the unknown stock rules.
    
    Rules:
    - If current stock would go negative from a sale, set to None (unknown)
    - If current stock is unknown (None) and it's a sale, keep as None
    - If current stock is unknown (None) and it's a restock, apply the restock amount
    - Otherwise, apply the transaction normally
    
    Args:
        current_stock: Current stock value (int or None)
        transaction_qty: Quantity to add/subtract (positive for restock, negative for sale)
        is_restock: True if this is a restock transaction, False if sale
    
    Returns:
        Updated stock value (int or None)
    """
    # If current stock is unknown
    if current_stock is None:
        if is_restock and transaction_qty > 0:
            # Restock: apply the amount
            return int(transaction_qty)
        else:
            # Sale or invalid restock: keep as unknown
            return None
    
    # Current stock is known
    new_stock = int(current_stock) + int(transaction_qty)
    
    # If sale would make stock negative, mark as unknown
    if not is_restock and new_stock < 0:
        return None
    
    # Otherwise apply normally
    return max(0, new_stock)  # Ensure non-negative for valid calculations


def _compute_stock_map(all_transactions: List[Tuple[Any, ...]]) -> Dict[Tuple[str, str, str, str], Any]:
    """Compute stock map from transactions, handling unknown stock.
    Returns dict mapping product key to stock value (int or None).
    """
    stock_map: Dict[Tuple[str, str, str, str, str], Any] = {}
    for row in all_transactions:
        # Expect: type, id, od, th, brand, quantity, is_restock
        type_, id_raw, od_raw, th_raw, brand, quantity, is_restock = row
        key = (type_, id_raw, od_raw, th_raw, str(brand).strip().upper())
        
        if is_restock == 2:
            # Actual count: reset stock
            stock_map[key] = int(quantity)
        else:
            # Apply transaction (restock=1 or sale=0)
            current = stock_map.get(key, 0)
            is_restock_tx = (is_restock == 1)
            stock_map[key] = apply_stock_transaction(current, int(quantity), is_restock_tx)
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


def stock_filter_matches(qty: Any, stock_filter: str) -> bool:
    """Check if stock quantity matches the given filter.
    qty can be int or None (unknown stock).
    """
    # Unknown stock (None) matching logic
    if qty is None:
        return stock_filter in ("All", "Unknown Stock")
    
    qty_int = int(qty)
    if stock_filter == "Low Stock":
        return 0 < qty_int <= LOW_STOCK_THRESHOLD
    if stock_filter == "Out of Stock":
        return qty_int == OUT_OF_STOCK
    if stock_filter == "In Stock":
        return qty_int > OUT_OF_STOCK
    if stock_filter == "Unknown Stock":
        return False  # qty is not None, so not unknown
    return True  # "All" filter


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
        # Sort quantities in descending order, with unknown stock (None) appearing at the end
        def qty_sort_key(item):
            qty = item[4]
            if qty is None:
                return (0, 1)  # Unknown stock sorts to end
            else:
                return (qty, 0)  # Known quantities sort by value
        display_data.sort(key=qty_sort_key, reverse=True)

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


def get_stock_tag(qty: Any) -> str:
    """Get stock status tag based on quantity.
    qty can be int or None (unknown stock).
    """
    if is_unknown_stock(qty):
        return "unknown"
    qty_int = int(qty)
    if qty_int < 0 or qty_int == OUT_OF_STOCK:
        return "out"
    elif qty_int <= LOW_STOCK_THRESHOLD:
        return "low"
    else:
        return "normal"


def should_uppercase_field(field_name: str) -> bool:
    """Check if a field should be automatically uppercased"""
    return field_name in ["type", "brand", "part_no"]


def is_unknown_stock(qty: Any) -> bool:
    """Check if stock value represents unknown/insufficient stock (displayed as ?)"""
    return qty is None


def format_stock_display(qty: Any) -> str:
    """Format stock quantity for display, showing ? for unknown stock"""
    if is_unknown_stock(qty):
        return "?"
    try:
        return str(int(qty))
    except (ValueError, TypeError):
        return "?"
