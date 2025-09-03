from typing import Any, Dict, List, Tuple
from datetime import datetime
import os
from PIL import Image
from ..database import connect_db


def get_existing_image_base(details: Dict[str, Any]) -> str:
    """Generate base filename for existing images"""
    return f"{details['type']}-{details['id']}-{details['od']}-{details['th']}"


def load_transactions_records(details: Dict[str, Any]) -> List[Tuple[Any, ...]]:
    """Load transaction records from database for a specific product"""
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
                SELECT t.date, t.name, t.quantity, t.price, t.is_restock, p.brand
                FROM transactions t
                JOIN products p ON t.type = p.type AND t.id_size = p.id AND t.od_size = p.od AND t.th_size = p.th
                WHERE t.type=? AND t.id_size=? AND t.od_size=? AND t.th_size=?
                ORDER BY t.date ASC
            """,
            (details["type"], details["id"], details["od"], details["th"]),
        )
        rows = cur.fetchall()
    return rows


def get_thresholds(details: Dict[str, Any]) -> Tuple[int, int]:
    """Get low and warning thresholds for a product"""
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT low_threshold, warn_threshold FROM products
                 WHERE type=? AND id=? AND od=? AND th=? AND brand=?""",
            (details["type"], details["id"], details["od"], details["th"], details["brand"]),
        )
        row = cur.fetchone()
    low = row[0] if row and row[0] is not None else 0
    warn = row[1] if row and row[1] is not None else 5
    return int(low), int(warn)


def get_location_and_notes(details: Dict[str, Any]) -> Tuple[str, str]:
    """Get location and notes for a product"""
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
                SELECT location, notes FROM products
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """,
            (details["type"], details["id"], details["od"], details["th"], details["part_no"]),
        )
        row = cur.fetchone()
    if not row:
        return "", ""
    return (row[0] or "", row[1] or "")


def update_location(details: Dict[str, Any], new_location: str) -> None:
    """Update product location in database"""
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
                UPDATE products SET location=?
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """,
            (new_location.strip(), details["type"], details["id"], details["od"], details["th"], details["part_no"]),
        )
        conn.commit()


def update_price(details: Dict[str, Any], new_price: float) -> None:
    """Update product price in database"""
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
                UPDATE products SET price=?
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """,
            (new_price, details["type"], details["id"], details["od"], details["th"], details["part_no"]),
        )
        conn.commit()


def update_notes(details: Dict[str, Any], new_notes: str) -> None:
    """Update product notes in database"""
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
                UPDATE products SET notes=?
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """,
            (new_notes.strip(), details["type"], details["id"], details["od"], details["th"], details["part_no"]),
        )
        conn.commit()


def update_thresholds(details: Dict[str, Any], low: int, warn: int) -> None:
    """Update stock thresholds in database"""
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
                UPDATE products SET low_threshold=?, warn_threshold=?
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """,
            (low, warn, details["type"], details["id"], details["od"], details["th"], details["part_no"]),
        )
        conn.commit()


def summarize_running_stock(rows: List[Tuple[Any, ...]]) -> List[Tuple[str, Any, Any, Any, Any, Any, int]]:
    """Return list of tuples for display, computing running stock with reset on Actual (is_restock==2)."""
    running_stock = 0
    result = []
    for row in rows:
        date, name, qty, price, is_restock, brand = row
        if is_restock == 2:
            running_stock = int(qty)
        else:
            running_stock += int(qty)
        date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%y")
        qty_restock = ""
        cost = ""
        price_str = ""
        display_qty = ""
        if is_restock == 1:
            # Only show cost if price > 0
            cost_value = float(price)
            cost = f"₱{cost_value:.2f}" if cost_value > 0 else ""
            qty_restock = qty
        elif is_restock == 0:
            display_qty = abs(int(qty))
            price_str = f"₱{float(price):.2f}"
        result.append((date_str, qty_restock, cost, name, display_qty, price_str, running_stock))
    return list(reversed(result))


def calculate_current_stock(rows: List[Tuple[Any, ...]]) -> int:
    """Calculate current stock from transaction history"""
    if not rows:
        return 0
    summary = summarize_running_stock(rows)
    return summary[0][6] if summary else 0


def get_stock_color(stock: int, low_threshold: int, warn_threshold: int) -> str:
    """Get color code based on stock level and thresholds"""
    if stock <= low_threshold:
        return "#EF4444"  # Red
    elif stock <= warn_threshold:
        return "#F59E0B"  # Orange/Yellow
    else:
        return "#22C55E"  # Green


def format_price_display(price: float) -> str:
    """Format price for display"""
    return f"₱{price:.2f}"


def parse_price_input(price_str: str) -> float:
    """Parse price input string to float"""
    cleaned = price_str.replace("₱", "").strip()
    return float(cleaned)


def validate_price_input(price_str: str) -> bool:
    """Validate if price input is valid"""
    try:
        parse_price_input(price_str)
        return True
    except (ValueError, TypeError):
        return False


def create_header_text(details: Dict[str, Any]) -> str:
    """Create main header text for product"""
    return f"{details['type']} {details['id']}-{details['od']}-{details['th']} {details['brand']}"


def create_subtitle_text(details: Dict[str, Any]) -> str:
    """Create subtitle text for product"""
    part = str(details['part_no']).strip()
    country = details['country_of_origin'].strip()
    return f"{part} | {country}" if part else country


def get_transaction_tag(qty_restock: str, price_str: str) -> str:
    """Get tag for transaction row coloring"""
    if qty_restock == "" and price_str == "":
        return "green"  # Stock adjustment
    elif qty_restock != "":
        return "blue"   # Restock
    else:
        return "red"    # Sale


def is_photo_upload_allowed(details: Dict[str, Any]) -> bool:
    """Check if photo upload is allowed for this product"""
    return details["brand"].upper() == "MOS"


def get_photos_directory() -> str:
    """Get the photos directory path"""
    return os.path.join(os.path.dirname(__file__), "..", "photos")


def get_photo_path_by_type(details: Dict[str, Any]) -> str:
    """Get photo path based on product type and brand"""
    photos_dir = get_photos_directory()
    
    if details["brand"].upper() == "MOS":
        if 'brand' not in details:
            return ""
        safe_th = details['th'].replace('/', 'x')
        safe_brand = details['brand'].replace('/', 'x').replace(' ', '_')
        for ext in [".jpg", ".jpeg", ".png"]:
            path = os.path.join(photos_dir, f"{details['type']}-{details['id']}-{details['od']}-{safe_th}-{safe_brand}{ext}")
            if os.path.exists(path):
                return path
        return ""
    else:
        for ext in [".jpg", ".png"]:
            path = os.path.join(photos_dir, f"{details['type'].lower()}{ext}")
            if os.path.exists(path):
                return path
        placeholder = os.path.join(photos_dir, "placeholder.png")
        return placeholder if os.path.exists(placeholder) else ""


def validate_image_file(file_path: str) -> bool:
    """Validate if file is a supported image format"""
    if not file_path:
        return False
    ext = os.path.splitext(file_path)[1].lower()
    return ext in [".jpg", ".jpeg", ".png"]


def create_safe_filename(details: Dict[str, Any], extension: str) -> str:
    """Create safe filename for photo storage"""
    safe_th = details['th'].replace('/', 'x')
    safe_brand = details['brand'].replace('/', 'x').replace(' ', '_')
    return f"{details['type']}-{details['id']}-{details['od']}-{safe_th}-{safe_brand}{extension}"


def compress_and_save_image(source_path: str, target_path: str, max_size_mb: int = 5) -> bool:
    """Compress and save image with size limit"""
    try:
        img = Image.open(source_path).convert("RGB")
        quality = 95
        max_size_bytes = max_size_mb * 1024 * 1024
        
        while True:
            img.save(target_path, format="JPEG", quality=quality)
            if os.path.getsize(target_path) <= max_size_bytes or quality <= 60:
                break
            quality -= 5
        return True
    except Exception:
        return False


def delete_old_images(details: Dict[str, Any]) -> None:
    """Delete old image files for a product"""
    photos_dir = get_photos_directory()
    base_old = get_existing_image_base(details)
    for old_ext in [".jpg", ".jpeg", ".png"]:
        old_path = os.path.join(photos_dir, base_old + old_ext)
        if os.path.exists(old_path):
            os.remove(old_path)


def calculate_image_display_size(image_path: str, max_width: int, max_height: int) -> Tuple[int, int]:
    """Scale image to fill given box, maintaining aspect ratio.
       Resize both up or down as needed to fill the box.
    """
    try:
        img = Image.open(image_path)
        orig_width, orig_height = img.size

        width_ratio = max_width / orig_width
        height_ratio = max_height / orig_height
        scale_factor = max(width_ratio, height_ratio)  # Use max to fill window

        new_width = int(orig_width * scale_factor)
        new_height = int(orig_height * scale_factor)
        return new_width, new_height
    except Exception:
        return max_width, max_height


def create_thumbnail_size(image_path: str, max_size: int = 80) -> Tuple[int, int]:
    """Create thumbnail size for image"""
    try:
        img = Image.open(image_path)
        img.thumbnail((max_size, max_size))
        return img.size
    except Exception:
        return max_size, max_size