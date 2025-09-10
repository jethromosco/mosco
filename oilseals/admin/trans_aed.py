from datetime import datetime
from ..database import connect_db
from .brand_utils import canonicalize_brand
import re
from fractions import Fraction
import os


def center_window(win, width, height):
    """Center a window on the screen"""
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def format_currency(val):
    """Format a value as currency with peso symbol"""
    if val is None:
        return ""  # Return empty string for NULL values
    return f"\u20B1{val:.2f}"


@staticmethod
def save_fabrication_transaction(data):
    """Save a fabrication transaction (creates two records)"""
    try:
        conn = connect_db()
        cur = conn.cursor()

        # Insert restock record with NULL price (no cost for fabrication restock)
        cur.execute(
            """
            INSERT INTO transactions (date, type, id_size, od_size, th_size, part_no, name, quantity, price, is_restock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data['date'], data['item_type'], data['id_size'], data['od_size'],
                data['th_size'], data['part_no'], data['name'], data['qty_restock'], None, 1  # Changed 0 to None
            ),
        )

        # Insert sale record
        cur.execute(
            """
            INSERT INTO transactions (date, type, id_size, od_size, th_size, part_no, name, quantity, price, is_restock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data['date'], data['item_type'], data['id_size'], data['od_size'],
                data['th_size'], data['part_no'], data['name'], -data['qty_customer'], data['price'], 0
            ),
        )

        conn.commit()
        conn.close()
        return True
    except Exception:
        try:
            conn = connect_db()
            cur = conn.cursor()
            # Insert restock record
            cur.execute(
                """
                INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data['date'], data['item_type'], data['id_size'], data['od_size'],
                    data['th_size'], data['brand'], data['name'], data['qty_restock'], None, 1
                ),
            )
            # Insert sale record
            cur.execute(
                """
                INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data['date'], data['item_type'], data['id_size'], data['od_size'],
                    data['th_size'], data['brand'], data['name'], -data['qty_customer'], data['price'], 0
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            try:
                conn = connect_db()
                cur = conn.cursor()

                # Insert restock record with NULL price (no cost for fabrication restock)
                cur.execute(
                    """
                    INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data['date'], data['item_type'], data['id_size'], data['od_size'],
                        data['th_size'], data['brand'], data['name'], data['qty_restock'], None, 1
                    ),
                )

                # Insert sale record
                cur.execute(
                    """
                    INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data['date'], data['item_type'], data['id_size'], data['od_size'],
                        data['th_size'], data['brand'], data['name'], -data['qty_customer'], data['price'], 0
                    ),
                )
                conn.commit()
                conn.close()
                return True
            except Exception:
                return False


def _resolve_part_no(item_type, id_size, od_size, th_size, brand):
    try:
        item_type = (item_type or "").strip().upper()
        brand = (brand or "").strip().upper()
        canonical_brand, _ = canonicalize_brand(brand)
        brand = canonical_brand
        id_val = _normalize_number_for_db(id_size)
        od_val = _normalize_number_for_db(od_size)
        th_val = _normalize_number_for_db(th_size)
        if None in (id_val, od_val, th_val):
            return ""
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT part_no FROM products
            WHERE type = ? AND id = ? AND od = ? AND th = ? AND brand = ?
            LIMIT 1
            """,
            (item_type, id_val, od_val, th_val, brand),
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row and row[0] is not None else ""
    except Exception:
        return ""


def save_fabrication_transaction(data):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data['date'], data['item_type'], data['id_size'], data['od_size'],
                data['th_size'], data['brand'], data['name'], data['qty_restock'], None, 1
            ),
        )
        cur.execute(
            """
            INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data['date'], data['item_type'], data['id_size'], data['od_size'],
                data['th_size'], data['brand'], data['name'], -data['qty_customer'], data['price'], 0
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


class TransactionLogic:
    @staticmethod
    def save_fabrication_transaction(data):
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data['date'], data['item_type'], data['id_size'], data['od_size'],
                    data['th_size'], data['brand'], data['name'], data['qty_restock'], None, 1
                ),
            )
            cur.execute(
                """
                INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data['date'], data['item_type'], data['id_size'], data['od_size'],
                    data['th_size'], data['brand'], data['name'], -data['qty_customer'], data['price'], 0
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    @staticmethod
    def prepare_transaction_data(trans_type, form_data):
        """Prepare transaction data for saving."""
        try:
            # Accept date in 'mm/dd/yy' format and convert to '%Y-%m-%d'
            date_str = form_data['date']
            try:
                date = datetime.strptime(date_str, "%m/%d/%y").strftime("%Y-%m-%d")
            except Exception:
                date = date_str  # fallback, may error later if not valid
            item_type = form_data['item_type'].strip().upper()
            id_size = form_data['id_size'].strip()
            od_size = form_data['od_size'].strip()
            th_size = form_data['th_size'].strip()
            brand = form_data['brand'].strip().upper()
            name = form_data['name'].strip().upper()
            data = {
                'date': date,
                'item_type': item_type,
                'id_size': id_size,
                'od_size': od_size,
                'th_size': th_size,
                'brand': brand,
                'name': name
            }
            if trans_type in ["Restock", "Sale"]:
                qty = abs(int(form_data['quantity']))
                price = float(form_data['price'])
                is_restock = 1 if trans_type == "Restock" else 0
                if is_restock == 0:
                    qty = -qty
                data.update({
                    'quantity': qty,
                    'price': price,
                    'is_restock': is_restock
                })
            elif trans_type == "Actual":
                qty = int(form_data['stock'])
                data.update({
                    'quantity': qty,
                    'price': 0,
                    'is_restock': 2
                })
            elif trans_type == "Fabrication":
                qty_restock = int(form_data['qty_restock'])
                qty_customer = int(form_data['qty_customer'])
                price = float(form_data['price'])
                data.update({
                    'qty_restock': qty_restock,
                    'qty_customer': qty_customer,
                    'price': price
                })
            return data
        except Exception:
            return None
    @staticmethod
    def validate_transaction_data(trans_type, form_data):
        """Validate transaction data based on transaction type."""
        errors = []
        # Helper to treat empty strings as missing
        def missing(val):
            return val is None or str(val).strip() == ""

        # Common validation for required fields
        required_fields = ['item_type', 'id_size', 'od_size', 'th_size', 'brand', 'name']
        for field in required_fields:
            if missing(form_data.get(field)):
                errors.append(f"{field.replace('_', ' ').title()} is required.")

        if trans_type in ["Restock", "Sale"]:
            if missing(form_data.get('quantity')) or missing(form_data.get('price')):
                errors.append("Quantity and Price must be filled.")
            else:
                try:
                    qty = int(form_data['quantity'])
                    price = float(form_data['price'])
                    if qty <= 0 or price <= 0:
                        errors.append("Quantity and Price must be greater than 0.")
                except (ValueError, TypeError):
                    errors.append("Quantity must be a valid integer and Price must be a valid number.")
        elif trans_type == "Actual":
            if missing(form_data.get('stock')):
                errors.append("Stock must be filled.")
            else:
                try:
                    int(form_data['stock'])
                except (ValueError, TypeError):
                    errors.append("Stock must be a valid integer.")
        elif trans_type == "Fabrication":
            if missing(form_data.get('qty_restock')) or missing(form_data.get('qty_customer')) or missing(form_data.get('price')):
                errors.append("All Fabrication fields must be filled.")
            else:
                try:
                    qty_restock = int(form_data['qty_restock'])
                    qty_customer = int(form_data['qty_customer'])
                    price = float(form_data['price'])
                    if qty_customer > qty_restock:
                        errors.append("Qty Sold cannot exceed Qty Restock.")
                    if qty_restock <= 0 or qty_customer < 0:
                        errors.append("Quantities must be positive.")
                    # Allow price to be zero for fabrication
                    if price < 0:
                        errors.append("Price must not be negative.")
                except (ValueError, TypeError):
                    errors.append("Fabrication quantities must be valid integers and price must be a valid number.")
        return errors
    @staticmethod
    def delete_transactions(rowids):
        """Delete multiple transactions by their row IDs."""
        try:
            conn = connect_db()
            cur = conn.cursor()
            for rowid in rowids:
                cur.execute("DELETE FROM transactions WHERE rowid=?", (rowid,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price", "Stock"]

    @staticmethod
    def get_record_by_id(rowid):
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT t.rowid, t.date, t.type, t.id_size, t.od_size, t.th_size,
                       t.brand, t.name, t.quantity, t.price, t.is_restock
                FROM transactions t
                WHERE t.rowid = ?
                """,
                (rowid,)
            )
            record = cur.fetchone()
            conn.close()
            if record:
                class RecordObj:
                    def __init__(self, data):
                        self.rowid = data[0]
                        self.date = data[1]
                        self.type = data[2]
                        self.id_size = data[3]
                        self.od_size = data[4]
                        self.th_size = data[5]
                        self.brand = data[6] or ""
                        self.name = data[7]
                        self.quantity = data[8]
                        self.price = data[9]
                        self.is_restock = data[10]
                return RecordObj(record)
            return None
        except Exception:
            return None

    @staticmethod
    def validate_product_exists(item_type, id_size, od_size, th_size, brand):
        try:
            item_type = (item_type or "").strip().upper()
            brand = (brand or "").strip().upper()
            canonical_brand, _ = canonicalize_brand(brand)
            brand = canonical_brand
            id_val = (id_size or "").strip()
            od_val = (od_size or "").strip()
            th_val = (th_size or "").strip()
            if None in (id_val, od_val, th_val):
                return False
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM products
                WHERE type = ? AND id = ? AND od = ? AND th = ? AND brand = ?
                LIMIT 1
                """,
                (item_type, id_val, od_val, th_val, brand),
            )
            res = cur.fetchone()
            conn.close()
            return res is not None
        except Exception:
            return False

    @staticmethod
    def save_transaction(mode, data, rowid=None):
        try:
            conn = connect_db()
            cur = conn.cursor()

            # Normalize the brand using canonicalize_brand
            canonical_brand, _ = canonicalize_brand(data['brand'])
            data['brand'] = canonical_brand

            if mode == "Add":
                cur.execute(
                    """
                    INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, name, quantity, price, is_restock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data['date'], data['item_type'], data['id_size'], data['od_size'],
                        data['th_size'], data['brand'], data['name'], data['quantity'], data['price'], data['is_restock']
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE transactions SET date=?, type=?, id_size=?, od_size=?, th_size=?, brand=?, name=?, quantity=?, price=?, is_restock=?
                    WHERE rowid=?
                    """,
                    (
                        data['date'], data['item_type'], data['id_size'], data['od_size'],
                        data['th_size'], data['brand'], data['name'], data['quantity'], data['price'], data['is_restock'], rowid
                    ),
                )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
def sanitize_dimension_for_filename(value):
    """
    Replace slashes in dimension values (e.g., ID, OD, TH) with 'x' for safe filenames.
    Handles complex cases like '1/2 - 2 - 3/4'.
    """
    if value is None:
        return ""
    # Replace all slashes with 'x'
    return str(value).replace("/", "x")


def _normalize_number_for_db(val):
    """
    Normalize a number or fraction string for DB comparison.
    Handles complex cases like '1/2 - 2 - 3/4'.
    """
    if val is None:
        return None
    val = str(val).strip()
    try:
        # Split the value by delimiters like '-' and normalize each part
        parts = [part.strip() for part in re.split(r'[-]', val)]
        normalized_parts = []
        for part in parts:
            if ' ' in part and '/' in part:  # Handle mixed fractions like '8 1/2'
                whole, frac = part.split(' ')
                normalized_parts.append(str(float(whole) + float(Fraction(frac))))
            elif '/' in part:  # Handle simple fractions like '1/2'
                normalized_parts.append(str(float(Fraction(part))))
            else:  # Handle whole numbers or decimals
                normalized_parts.append(str(float(part)))
        return " - ".join(normalized_parts)  # Rejoin the normalized parts
    except Exception:
        return val  # fallback: return as-is if can't parse


def save_photo_with_dimensions(id_size, od_size, th_size, photo_path):
    """
    Save a photo with sanitized dimensions in the filename.
    """
    try:
        sanitized_id = sanitize_dimension_for_filename(id_size)
        sanitized_od = sanitize_dimension_for_filename(od_size)
        sanitized_th = sanitize_dimension_for_filename(th_size)

        # Construct the filename using sanitized dimensions
        filename = f"photo_{sanitized_id}_{sanitized_od}_{sanitized_th}.jpg"
        # Save the photo (pseudo-code, replace with actual saving logic)
        save_path = os.path.join(photo_path, filename)
        # ... logic to save the photo to save_path ...
        return save_path
    except Exception as e:
        print(f"Error saving photo: {e}")
        return None
