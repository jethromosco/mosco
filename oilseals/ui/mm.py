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
            # Replace brand with canonical label for searching
            canonical_label, _ = canonicalize_brand(val)
            val = canonical_label

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
    """Return list of tuples: (type, size_str, brand, part_no, origin, notes, qty, price_str, id_raw, od_raw, th_raw)
    where the last three are for sorting only and should not be displayed.
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
        size_str = f"{format_display_value(id_raw)}×{format_display_value(od_raw)}×{format_display_value(th_raw)}"
        display_data.append((
            type_,
            size_str,
            brand,
            part_no,
            origin,
            notes,
            qty,
            f"₱{float(price):.2f}",
            id_raw,
            od_raw,
            th_raw
        ))

    if sort_by == "Size":
        display_data.sort(key=lambda x: (parse_number(x[8]), parse_number(x[9]), _parse_thickness_sort(x[10])))
    elif sort_by == "Quantity":
        display_data.sort(key=lambda x: x[6], reverse=True)

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
    """Create product details dictionary from tree item values"""
    if len(item_values) < 8:
        return {}
    
    id_, od, th = parse_size_string(item_values[1])
    
    return {
        "type": item_values[0],
        "id": id_,
        "od": od,
        "th": th,
        "brand": str(item_values[2]).strip().upper(),
        "part_no": item_values[3],
        "country_of_origin": item_values[4],
        "notes": item_values[5],
        "quantity": item_values[6],
        "price": float(str(item_values[7]).replace("₱", ""))
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
