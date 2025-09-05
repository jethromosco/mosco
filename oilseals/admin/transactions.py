from ..database import connect_db
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction


def format_currency(val):
    """Format currency value with Philippine peso symbol."""
    return f"\u20B1{val:.2f}"


def parse_date(text):
    """Parse date from MM/DD/YY format."""
    return datetime.strptime(text, "%m/%d/%y")


def parse_date_db(text):
    """Parse date from database YYYY-MM-DD format."""
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        # Try 'mm/dd/yy' format as fallback
        return datetime.strptime(text, "%m/%d/%y")


def parse_size_component(s: str) -> float:
    """Parse size component that might include fractions."""
    if s is None:
        raise ValueError("Size component is missing")
    s = str(s).strip()
    if not s:
        raise ValueError("Size component is empty")

    if ' ' in s and '/' in s:
        parts = s.split()
        if len(parts) == 2:
            whole, frac = parts
            return float(int(whole) + Fraction(frac))
        else:
            return float(Fraction(s.replace(' ', '')))
    if '/' in s:
        return float(Fraction(s))
    return float(s)


def format_size_value(v: float) -> str:
    """Format size value for display."""
    if v is None:
        return ""
    try:
        fv = float(v)
    except Exception:
        return str(v)
    if abs(fv - int(round(fv))) < 1e-9:
        return str(int(round(fv)))
    s = f"{fv:.4f}".rstrip('0').rstrip('.')
    return s


@dataclass
class TransactionRecord:
    """Data class representing a transaction record."""
    rowid: int
    date: str
    type: str
    id_size: str
    od_size: str
    th_size: str
    name: str
    quantity: int
    price: float
    is_restock: int
    brand: str


class TransactionsLogic:
    """Handles all transaction-related business logic and database operations."""
    
    def __init__(self):
        pass
    
    def get_all_transactions(self):
        """Retrieve all transactions from database with product information."""
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.rowid, t.date, t.type, t.id_size, t.od_size, t.th_size, t.name, t.quantity, t.price, t.is_restock,
                t.brand
            FROM transactions t
        """)
        rows = cur.fetchall()
        conn.close()
        
        return [TransactionRecord(*row) for row in rows]
    
    def identify_fabrication_records(self, records):
        """Identify fabrication records (matching restock/sale pairs on same date)."""
        fabrication_records = set()
        
        # Group records by date, item, and brand
        date_item_groups = defaultdict(list)
        for record in records:
            key = (record.date, record.type, record.id_size, record.od_size, record.th_size, record.brand)
            date_item_groups[key].append(record)

        # Identify fabrication records (same date, same item, same brand, one restock + one sale)
        for key, group_records in date_item_groups.items():
            restocks = [r for r in group_records if r.is_restock == 1]
            sales = [r for r in group_records if r.is_restock == 0]
            # Only pair if exactly one restock and one sale for same brand
            if len(restocks) == 1 and len(sales) == 1:
                fabrication_records.add(restocks[0].rowid)
                fabrication_records.add(sales[0].rowid)

        return fabrication_records
    
    def filter_transactions(self, records, keyword="", restock_filter="All", date_filter=None, fabrication_records=None):
        """Filter transactions based on search criteria."""
        if fabrication_records is None:
            fabrication_records = self.identify_fabrication_records(records)
        
        filtered = []
        
        for record in records:
            # Date filter
            if date_filter:
                date_obj = parse_date_db(record.date)
                if date_obj.date() != date_filter:
                    continue
            
            # Keyword search
            if keyword:
                item_tokens = f"{record.type} {record.id_size} {record.od_size} {record.th_size} {record.brand or ''}".lower()
                name_str = record.name.lower()
                search_terms = keyword.lower().split()
                if not all(term in item_tokens or term in name_str for term in search_terms):
                    continue
            
            # Type filter
            is_actual = (record.is_restock == 2)
            is_restock = (record.is_restock == 1 and record.rowid not in fabrication_records)
            is_sale = (record.is_restock == 0 and record.rowid not in fabrication_records)
            is_fabrication = (record.rowid in fabrication_records)
            
            if restock_filter == "Restock" and not is_restock:
                continue
            if restock_filter == "Sale" and not is_sale:
                continue
            if restock_filter == "Actual" and not is_actual:
                continue
            if restock_filter == "Fabrication" and not is_fabrication:
                continue
            
            filtered.append(record)
        
        return filtered
    
    def calculate_running_stock(self, records):
        """Calculate running stock for each item across all transactions."""
        # Sort records chronologically for accurate stock calculation
        sorted_records = sorted(records, key=lambda r: (r.date, r.rowid))
        
        running_stock_map = defaultdict(int)
        results = []
        
        for record in sorted_records:
            item_key = (record.type, record.id_size, record.od_size, record.th_size, record.brand)
            
            if record.is_restock == 2:  # Actual stock
                running_stock_map[item_key] = record.quantity
            else:
                running_stock_map[item_key] += record.quantity
            
            results.append((record, running_stock_map[item_key]))
        
        return results
    
    def format_transaction_for_display(self, record, stock_level):
        """Format a transaction record for display in the GUI."""
        item_str = f"{record.type} {record.id_size}-{record.od_size}-{record.th_size}"
        if record.brand:
            item_str += f" {record.brand}"
        
        formatted_date = parse_date_db(record.date).strftime("%m/%d/%y")
        
        cost = ""
        price_str = ""
        qty_restock = ""
        qty_sale = ""
        
        # Determine display values and color tag
        tag = "gray"
        if record.is_restock == 1:  # Restock
            tag = "blue"
            # Hide cost for fabrication restock (restock with 0 or null price and positive quantity)
            if record.price and record.price > 0:
                cost = format_currency(record.price)
            else:
                cost = ""  # Empty for fabrication restock
            qty_restock = record.quantity
        elif record.is_restock == 0:  # Sale
            tag = "red"
            price_str = format_currency(record.price)
            qty_sale = abs(record.quantity)
        elif record.is_restock == 2:  # Actual
            tag = "green"
        
        return {
            'rowid': record.rowid,
            'values': (item_str, formatted_date, qty_restock, cost, record.name, qty_sale, price_str, stock_level),
            'tag': tag,
            'record': record
        }
    
    def sort_transactions(self, records, column, ascending=True):
        """Sort transaction records by specified column."""
        def sort_key(record):
            if column == "item":
                return f"{record.type} {record.id_size}-{record.od_size}-{record.th_size} {record.brand or ''}"
            elif column == "date":
                return record.date
            elif column in ["qty_restock", "qty"]:
                return abs(record.quantity) if record.is_restock in [0, 1] else 0
            elif column in ["cost", "price"]:
                return record.price
            elif column == "name":
                return record.name.lower()
            else:
                return 0
        
        return sorted(records, key=sort_key, reverse=not ascending)
    
    def get_transaction_by_id(self, records, rowid):
        """Get a specific transaction record by its rowid."""
        for record in records:
            if record.rowid == rowid:
                return record
        return None
    
    def add_transaction(self, transaction_data):
        """Add a new transaction to the database."""
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, transaction_data)
            conn.commit()
            conn.close()
            return True, "Transaction added successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def update_transaction(self, rowid, transaction_data):
        """Update an existing transaction in the database."""
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE transactions 
                SET date=?, type=?, id_size=?, od_size=?, th_size=?, name=?, quantity=?, price=?, is_restock=?
                WHERE rowid=?
            """, transaction_data + [rowid])
            conn.commit()
            conn.close()
            return True, "Transaction updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def delete_transaction(self, rowid):
        """Delete a transaction from the database."""
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM transactions WHERE rowid=?", (rowid,))
            conn.commit()
            conn.close()
            return True, "Transaction deleted successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"