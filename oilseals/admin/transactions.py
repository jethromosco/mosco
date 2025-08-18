import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from ..database import connect_db
from fractions import Fraction
from .trans_aed import TransactionFormHandler

# Utility functions
def center_window(win, width, height):
    # Calculate center position
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    
    # Set geometry with position BEFORE showing
    win.geometry(f"{width}x{height}+{x}+{y}")
    
    # Update to ensure proper positioning
    win.update_idletasks()

def format_currency(val):
    return f"\u20B1{val:.2f}"

def parse_date(text):
    return datetime.strptime(text, "%m/%d/%y")

def parse_date_db(text):
    return datetime.strptime(text, "%Y-%m-%d")

def parse_size_component(s: str) -> float:
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

# ─────────────────────────────────────────────────────────────
# TransactionTab Class Start
# ─────────────────────────────────────────────────────────────

class TransactionTab:
    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price"]

    def __init__(self, notebook, main_app, controller, on_refresh_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_refresh_callback = on_refresh_callback
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="Transactions")

        self.sort_direction = {}
        self.filtered_records = []
        self.date_filter_active = False  # Track if date filter should be active

        self.setup_controls()
        self.setup_treeview()
        
        self.form_handler = TransactionFormHandler(
            parent_frame=self.frame,
            treeview=self.tran_tree,
            on_refresh_callback=self.refresh_transactions
        )
        self.form_handler._get_record_by_id = self._get_record_by_id

        self.setup_buttons()
        self.refresh_transactions()

    def setup_controls(self):
        control_frame = tk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(control_frame, text="Search:").pack(side=tk.LEFT)
        self.tran_search_var = tk.StringVar()
        tk.Entry(control_frame, textvariable=self.tran_search_var, width=20).pack(side=tk.LEFT, padx=5)
        self.tran_search_var.trace_add("write", lambda *args: self.refresh_transactions())

        tk.Label(control_frame, text="Restock:").pack(side=tk.LEFT, padx=(20, 0))
        self.restock_filter = tk.StringVar(value="All")
        ttk.Combobox(control_frame, textvariable=self.restock_filter,
                     values=["All", "Restock", "Sale", "Actual", "Fabrication"], width=10, state="readonly").pack(side=tk.LEFT)
        self.restock_filter.trace_add("write", lambda *args: self.refresh_transactions())

        tk.Label(control_frame, text="Date:").pack(side=tk.LEFT, padx=(20, 0))
        self.date_var = tk.StringVar()
        self.date_filter = DateEntry(
            control_frame,
            date_pattern="mm/dd/yy",
            width=12,
            showweeknumbers=False,
            textvariable=self.date_var,
            state="readonly"  # Make the text field non-editable
        )
        self.date_filter.pack(side=tk.LEFT)
        self.date_var.set("")
        
        # Only bind to calendar selection since text field is readonly
        self.date_filter.bind('<<DateEntrySelected>>', self.on_date_selected)

        self.clear_btn = tk.Button(control_frame, text="All", command=self.clear_date_filter)
        self.clear_btn.pack(side=tk.LEFT, padx=(5, 0))

    def on_date_selected(self, event=None):
        """Handle when user selects a date from the calendar"""
        # Small delay to ensure the date is set properly
        self.frame.after(50, self.apply_date_filter)
        # Remove focus from date field after selection
        self.frame.after(100, lambda: self.frame.focus_set())

    def apply_date_filter(self):
        """Apply the date filter and refresh"""
        self.date_filter_active = bool(self.date_var.get().strip())
        self.refresh_transactions()

    def clear_date_filter(self):
        """Clear the date filter and remove focus from date field"""
        self.date_var.set("")
        self.date_filter_active = False
        # Remove focus from the DateEntry widget
        self.frame.focus_set()
        # Refresh after clearing
        self.refresh_transactions()

    def setup_treeview(self):
        self.tran_tree = ttk.Treeview(
            self.frame,
            columns=("item", "date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings",
            selectmode="extended"
        )
        self.tran_tree.tag_configure("red", foreground="red")
        self.tran_tree.tag_configure("blue", foreground="blue")
        self.tran_tree.tag_configure("green", foreground="green") # Added green tag

        column_config = {
            "item": {"anchor": "center", "width": 180},
            "date": {"anchor": "center", "width": 90},
            "qty_restock": {"anchor": "center", "width": 60},
            "cost": {"anchor": "center", "width": 80},
            "name": {"anchor": "w", "width": 160},
            "qty": {"anchor": "center", "width": 60},
            "price": {"anchor": "center", "width": 80},
            "stock": {"anchor": "center", "width": 80},
        }
        for col in self.tran_tree["columns"]:
            header = col.upper().replace("_", " ")
            self.tran_tree.heading(col, text=header, command=lambda c=col: self.sort_by_column(c))
            self.tran_tree.column(col, **column_config[col])

        self.tran_tree.pack(fill=tk.BOTH, expand=True, pady=10)

    def setup_buttons(self):
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack()
        
        tk.Button(btn_frame, text="Add", command=self.form_handler.add_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.form_handler.edit_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.form_handler.delete_transaction).pack(side=tk.LEFT, padx=5)

        self.frame.bind_all("<Control-a>", lambda e: self.form_handler.add_transaction())
        self.frame.bind_all("<Control-e>", lambda e: self.form_handler.edit_transaction())
        self.frame.bind_all("<Delete>", lambda e: self.form_handler.delete_transaction())

    def refresh_transactions(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.rowid, t.date, t.type, t.id_size, t.od_size, t.th_size, t.name, t.quantity, t.price, t.is_restock,
                p.brand
            FROM transactions t
            LEFT JOIN products p ON t.type = p.type AND t.id_size = p.id AND t.od_size = p.od AND t.th_size = p.th
        """)
        rows = cur.fetchall()
        conn.close()

        keyword = self.tran_search_var.get().lower()
        restock_filter = self.restock_filter.get()

        # Only apply date filter if it's been activated
        date_str = self.date_var.get().strip()
        filter_date = None
        if self.date_filter_active and date_str:
            try:
                filter_date = parse_date(date_str).date()
            except Exception:
                filter_date = None

        # Group records to identify Fabrication transactions
        fabrication_records = set()
        
        # First pass: identify Fabrication transactions by checking the transaction type in the database
        conn2 = connect_db()
        cur2 = conn2.cursor()
        cur2.execute("SELECT DISTINCT date, type, id_size, od_size, th_size, name FROM transactions WHERE type IN (SELECT DISTINCT type FROM transactions WHERE type LIKE '%fabrication%' OR type = 'Fabrication')")
        fab_rows = cur2.fetchall()
        conn2.close()
        
        # Actually, let's use a simpler approach - check if there are matching restock/sale pairs on same date
        date_item_groups = defaultdict(list)
        for row in rows:
            record = TransactionRecord(*row)
            key = (record.date, record.type, record.id_size, record.od_size, record.th_size, record.name)
            date_item_groups[key].append(record)
        
        # Identify fabrication records (same date, same item, one restock + one sale)
        for key, records in date_item_groups.items():
            if len(records) == 2:
                has_restock = any(r.is_restock == 1 for r in records)
                has_sale = any(r.is_restock == 0 for r in records)
                if has_restock and has_sale:
                    # These are fabrication records
                    for record in records:
                        fabrication_records.add(record.rowid)

        filtered = []
        for row in rows:
            record = TransactionRecord(*row)
            date_obj = parse_date_db(record.date)
            if filter_date and date_obj.date() != filter_date:
                continue
            item_tokens = f"{record.type} {record.id_size} {record.od_size} {record.th_size} {record.brand}".lower()
            name_str = record.name.lower()
            search_terms = keyword.split()
            if keyword and not all(term in item_tokens or term in name_str for term in search_terms):
                continue
            
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
        
        self.filtered_records = filtered
        self.render_transactions(self.filtered_records)
        if self.on_refresh_callback:
            self.on_refresh_callback()

    def _get_record_by_id(self, rowid):
        for record in self.filtered_records:
            if record.rowid == rowid:
                return record
        return None

    def render_transactions(self, records):
        self.tran_tree.delete(*self.tran_tree.get_children())
        
        # We need to process the records chronologically to calculate running stock correctly
        records.sort(key=lambda r: (r.date, r.rowid))
        
        running_stock_map = defaultdict(int)
        
        # Calculate running stock with special handling for "Actual" transactions
        all_rows = []
        for record in records:
            item_key = (record.type, record.id_size, record.od_size, record.th_size, record.brand)
            
            if record.is_restock == 2:  # 'Actual' transaction
                running_stock_map[item_key] = record.quantity # Reset stock to the quantity value
            else: # Restock or Sale
                running_stock_map[item_key] += record.quantity
            
            all_rows.append((record, running_stock_map[item_key]))

        # After calculating running stock for all_rows:
        all_rows.sort(key=lambda x: (x[0].date, x[0].rowid), reverse=True) # Descending date

        for record, stock in all_rows:
            item_str = f"{record.type} {record.id_size}-{record.od_size}-{record.th_size} {record.brand}"
            formatted_date = parse_date_db(record.date).strftime("%m/%d/%y")
            
            cost = ""
            price_str = ""
            qty_restock = ""
            qty_sale = ""
            
            tag = "gray"  # Default tag
            if record.is_restock == 1: # Restock
                tag = "blue"
                cost = format_currency(record.price)
                qty_restock = record.quantity
            elif record.is_restock == 0: # Sale
                tag = "red"
                price_str = format_currency(record.price)
                qty_sale = abs(record.quantity)
            elif record.is_restock == 2: # Actual
                tag = "green"
            
            self.tran_tree.insert("", tk.END, iid=record.rowid, values=(
                item_str, formatted_date, qty_restock, cost, record.name,
                qty_sale, price_str, stock
            ), tags=(tag,))

    def sort_by_column(self, col):
        if not self.filtered_records:
            return

        self.sort_direction[col] = not self.sort_direction.get(col, False)
        reverse = self.sort_direction[col]

        def sort_key(record):
            if col == "item":
                return f"{record.type} {record.id_size}-{record.od_size}-{record.th_size} {record.brand}"
            elif col == "date":
                return record.date
            elif col == "qty_restock" or col == "qty":
                return abs(record.quantity) if record.is_restock in [0, 1] else 0 # Only quantities for restock/sale
            elif col == "cost" or col == "price":
                return record.price
            elif col == "name":
                return record.name.lower()
            else:
                return 0

        self.filtered_records.sort(key=sort_key, reverse=reverse)
        self.render_transactions(self.filtered_records)