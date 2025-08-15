import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from ..database import connect_db
from fractions import Fraction
from .trans_aed import TransactionFormHandler # Import the new class

# ─────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────

def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

def format_currency(val):
    return f"\u20B1{val:.2f}"

def parse_date(text):
    return datetime.strptime(text, "%m/%d/%y")

def parse_date_db(text):
    return datetime.strptime(text, "%Y-%m-%d")

# Note: parse_size_component is not used in the form anymore, but is kept for utility purposes
def parse_size_component(s: str) -> float:
    """
    Parses a string that may be:
      - decimal: "12.5"
      - fraction: "3/4"
      - mixed number: "1 1/2"
      - integer: "12"
    Returns float.
    Raises ValueError on invalid input.
    """
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
    """
    Nicely format sizes:
      - If whole number (e.g., 12.0) -> "12"
      - Otherwise trim trailing zeros up to 4 decimal places -> e.g., "12.5", "0.75"
    """
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
        self.filtered_records = [] # Store records for sorting and editing

        self.setup_controls()
        self.setup_treeview()
        
        # Instantiate the new handler class
        self.form_handler = TransactionFormHandler(
            parent_frame=self.frame,
            treeview=self.tran_tree,
            on_refresh_callback=self.refresh_transactions
        )
        self.form_handler._get_record_by_id = self._get_record_by_id # Bind the helper method

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
                     values=["All", "Restock", "Sale"], width=10, state="readonly").pack(side=tk.LEFT)
        self.restock_filter.trace_add("write", lambda *args: self.refresh_transactions())

        tk.Label(control_frame, text="Date:").pack(side=tk.LEFT, padx=(20, 0))
        self.date_var = tk.StringVar()
        self.date_filter = DateEntry(
            control_frame,
            date_pattern="mm/dd/yy",
            width=12,
            showweeknumbers=False,
            textvariable=self.date_var
        )
        self.date_filter.pack(side=tk.LEFT)
        self.date_var.set("")
        self.date_var.trace_add("write", lambda *args: self.refresh_transactions())

        tk.Button(control_frame, text="All", command=self.clear_date_filter).pack(side=tk.LEFT, padx=(5, 0))

    def clear_date_filter(self):
        self.date_var.set("")

    def setup_treeview(self):
        self.tran_tree = ttk.Treeview(
            self.frame,
            columns=("item", "date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings",
            selectmode="extended"
        )
        self.tran_tree.tag_configure("red", foreground="red")
        self.tran_tree.tag_configure("blue", foreground="blue")

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
        
        # Use the methods from the new handler class
        tk.Button(btn_frame, text="Add", command=self.form_handler.add_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.form_handler.edit_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.form_handler.delete_transaction).pack(side=tk.LEFT, padx=5)

        self.frame.bind_all("<Control-a>", lambda e: self.form_handler.add_transaction())
        self.frame.bind_all("<Control-e>", lambda e: self.form_handler.edit_transaction())
        self.frame.bind_all("<Delete>", lambda e: self.form_handler.delete_transaction())

    def refresh_transactions(self):
        self.tran_tree.delete(*self.tran_tree.get_children())
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

        date_str = self.date_var.get().strip()
        try:
            filter_date = parse_date(date_str).date() if date_str else None
        except Exception:
            filter_date = None

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
            if restock_filter == "Restock" and not record.is_restock:
                continue
            if restock_filter == "Sale" and record.is_restock:
                continue
            filtered.append(record)

        self.filtered_records = filtered # Store the filtered records
        self.render_transactions(self.filtered_records)
        if self.on_refresh_callback:
            self.on_refresh_callback()

    def _get_record_by_id(self, rowid):
        # Helper to retrieve a full record object by its rowid
        for record in self.filtered_records:
            if record.rowid == rowid:
                return record
        return None

    def render_transactions(self, records):
        self.tran_tree.delete(*self.tran_tree.get_children())

        # Group transactions by (type, id_size, od_size, th_size, brand)
        grouped = defaultdict(list)
        for record in records:
            item_key = (record.type, record.id_size, record.od_size, record.th_size, record.brand)
            grouped[item_key].append(record)

        all_rows = []
        for item_key, item_records in grouped.items():
            # Sort by ascending date for correct running stock calculation
            item_records.sort(key=lambda r: parse_date_db(r.date))
            running_stock = 0
            for record in item_records:
                running_stock += record.quantity
                all_rows.append((record, running_stock))

        # Now sort all_rows by descending date for display
        all_rows.sort(key=lambda x: parse_date_db(x[0].date), reverse=True)

        for record, stock in all_rows:
            item_str = f"{record.type} {record.id_size}-{record.od_size}-{record.th_size} {record.brand}"
            formatted_date = parse_date_db(record.date).strftime("%m/%d/%y")
            cost = format_currency(record.price) if record.is_restock else ""
            price_str = format_currency(record.price) if not record.is_restock else ""
            tag = "blue" if record.is_restock else "red"
            qty_restock = record.quantity if record.is_restock else ""
            qty_sale = abs(record.quantity) if not record.is_restock else ""
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
                return abs(record.quantity)
            elif col == "cost" or col == "price":
                return record.price
            elif col == "name":
                return record.name.lower()
            else:
                return 0

        self.filtered_records.sort(key=sort_key, reverse=reverse)
        self.render_transactions(self.filtered_records)