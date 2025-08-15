import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from ..database import connect_db
from fractions import Fraction

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

    # Mixed number like "1 1/2"
    if ' ' in s and '/' in s:
        parts = s.split()
        if len(parts) == 2:
            whole, frac = parts
            return float(int(whole) + Fraction(frac))
        else:
            # fallback to attempt direct Fraction parse
            return float(Fraction(s.replace(' ', '')))

    # Plain fraction like "3/4"
    if '/' in s:
        return float(Fraction(s))

    # decimal or integer
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
        # fallback to string
        return str(v)
    if abs(fv - int(round(fv))) < 1e-9:
        return str(int(round(fv)))
    # format with up to 4 decimal places, strip trailing zeros
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
        # Store the callback function
        self.on_refresh_callback = on_refresh_callback
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="Transactions")

        self.sort_direction = {}

        self.setup_controls()
        self.setup_treeview()
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
        self.date_var.set("")  # Start blank

        # ONE clean binding
        self.date_var.trace_add("write", lambda *args: self.refresh_transactions())

        # Optional: Clear button
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

        tk.Button(btn_frame, text="Add", command=self.add_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.edit_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_transaction).pack(side=tk.LEFT, padx=5)

        self.frame.bind_all("<Control-a>", lambda e: self.add_transaction())
        self.frame.bind_all("<Control-e>", lambda e: self.edit_transaction())
        self.frame.bind_all("<Delete>", lambda e: self.delete_transaction())

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

        # Group transactions by (type, id_size, od_size, th_size, brand)
        grouped = defaultdict(list)
        for record in filtered:
            item_key = (record.type, record.id_size, record.od_size, record.th_size, record.brand)
            grouped[item_key].append(record)

        # Calculate running stock in ascending order, store with each transaction
        all_rows = []
        for records in grouped.values():
            # Sort by ascending date for correct running stock calculation
            records.sort(key=lambda r: parse_date_db(r.date))
            running_stock = 0
            for record in records:
                running_stock += record.quantity
                all_rows.append((record, running_stock))

        # NOW sort all_rows by descending date for display
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

        self.filtered_records = filtered

    def render_transactions(self, records):
        # You can remove this method or leave it empty
        pass

    def sort_by_column(self, col):
        if not hasattr(self, 'filtered_records'):
            return  # safety check

        # Flip sort direction
        self.sort_direction[col] = not self.sort_direction.get(col, False)
        reverse = self.sort_direction[col]

        # Define column-specific key
        def sort_key(record):
            if col == "item":
                return f"{record.type} {record.id_size}-{record.od_size}-{record.th_size} {record.brand}"
            elif col == "date":
                return record.date  # Already datetime-ish string; original logic used this
            elif col == "qty_restock" or col == "qty":
                return abs(record.quantity)
            elif col == "cost" or col == "price":
                return record.price
            elif col == "name":
                return record.name.lower()
            else:
                return 0

        # Sort the internal list
        self.filtered_records.sort(key=sort_key, reverse=reverse)

        # Re-render treeview
        self.render_transactions(self.filtered_records)

    def add_transaction(self):
        self.transaction_form("Add")

    def edit_transaction(self):
        item = self.tran_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a transaction to edit", parent=self.frame.winfo_toplevel())
        values = self.tran_tree.item(item)["values"]
        self.transaction_form("Edit", values, item)

    def delete_transaction(self):
        items = self.tran_tree.selection()
        if not items:
            return messagebox.showwarning("Select", "Select transaction(s) to delete", parent=self.frame.winfo_toplevel())
        confirm = messagebox.askyesno("Delete", f"Delete selected {len(items)} transaction(s)?", parent=self.frame.winfo_toplevel())
        if confirm:
            conn = connect_db()
            cur = conn.cursor()
            for item in items:
                cur.execute("SELECT * FROM transactions WHERE rowid=?", (item,))
                row = cur.fetchone()

                cur.execute("DELETE FROM transactions WHERE rowid=?", (item,))
            conn.commit()
            conn.close()
            self.refresh_transactions()
            # Call the callback after a successful deletion
            if self.on_refresh_callback:
                self.on_refresh_callback()

    def transaction_form(self, mode, values=None, rowid=None):
        form = tk.Toplevel(self.frame)
        form.title(f"{mode} Transaction")
        center_window(form, 250, 440)
        form.resizable(False, False)
        form.bind("<Escape>", lambda e: form.destroy())
        form.transient(self.frame.winfo_toplevel())
        form.grab_set()
        form.focus_force()
        form.lift()

        vars = {key: tk.StringVar() for key in self.FIELDS}
        date_var = tk.StringVar()
        restock_var = tk.StringVar(value="Sale")
        price_label_var = tk.StringVar(value="Price:")

        if mode == "Edit" and values:
            item = values[0]
            # item like: "TYPE 7/8-9/10-1/2 BRAND"
            try:
                type_, rest = item.split(" ", 1)
                size_part, brand_part = rest.split(" ", 1)
            except ValueError:
                parts = item.split(" ")
                type_ = parts[0]
                size_part = parts[1] if len(parts) > 1 else ""
                brand_part = " ".join(parts[2:]) if len(parts) > 2 else ""
            # Use raw strings for sizes
            try:
                id_str, od_str, th_str = size_part.split("-")[:3]
            except Exception:
                id_str = od_str = th_str = ""
            is_restock = "Restock" if "blue" in self.tran_tree.item(rowid)["tags"] else "Sale"

            vars["Type"].set(type_)
            vars["ID"].set(id_str)
            vars["OD"].set(od_str)
            vars["TH"].set(th_str)
            vars["Brand"].set(brand_part)
            vars["Name"].set(values[4])
            vars["Quantity"].set(values[2] if is_restock == "Restock" else values[5])
            vars["Price"].set(str(values[3] if is_restock == "Restock" else values[6]).replace("\u20B1", ""))
            date_var.set(values[1])
            restock_var.set(is_restock)
            price_label_var.set("Cost:" if is_restock == "Restock" else "Price:")

        def select_restock(value):
            restock_var.set(value)
            restock_btn.config(bg="blue" if value == "Restock" else "SystemButtonFace")
            sale_btn.config(bg="red" if value == "Sale" else "SystemButtonFace")
            price_label_var.set("Cost:" if value == "Restock" else "Price:")

        top_frame = tk.Frame(form)
        top_frame.pack(pady=10)
        restock_btn = tk.Button(top_frame, text="Restock", width=10, command=lambda: select_restock("Restock"))
        restock_btn.pack(side=tk.LEFT, padx=5)
        sale_btn = tk.Button(top_frame, text="Sale", width=10, command=lambda: select_restock("Sale"))
        sale_btn.pack(side=tk.LEFT, padx=5)
        select_restock(restock_var.get())

        date_row = tk.Frame(form)
        date_row.pack(pady=(5, 5))
        tk.Label(date_row, text="Date:").pack(side=tk.LEFT, padx=(0, 5))
        DateEntry(date_row, textvariable=date_var, date_pattern="mm/dd/yy", width=12).pack(side=tk.LEFT)

        for key in self.FIELDS:
            row = tk.Frame(form)
            row.pack(anchor="w", padx=10, pady=(10 if key == "Type" else 5, 0))
            label_var = price_label_var if key == "Price" else tk.StringVar(value=f"{key}:")
            tk.Label(row, textvariable=label_var, width=8, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=vars[key], width=20)
            entry.pack(side=tk.LEFT)
            if key in ["Type", "Name", "Brand"]:
                vars[key].trace_add("write", lambda *_, k=key: vars[k].set(vars[k].get().upper()))

        def save(event=None):
            try:
                date = parse_date(date_var.get()).strftime("%Y-%m-%d")
                type_ = vars["Type"].get().strip()
                raw_id = vars["ID"].get().strip()
                raw_od = vars["OD"].get().strip()
                raw_th = vars["TH"].get().strip()
                # The parse_size_component calls have been removed from here.
                brand = vars["Brand"].get().strip().upper()
                name = vars["Name"].get().strip().upper()
                qty = abs(int(vars["Quantity"].get()))
                price = float(vars["Price"].get())
                if qty <= 0 or price <= 0:
                    return messagebox.showerror("Invalid", "Quantity and Price must be greater than 0.", parent=form)
                is_restock = 1 if restock_var.get() == "Restock" else 0
                qty = qty if is_restock else -qty
            except Exception as e:
                return messagebox.showerror("Invalid", f"Check all fields\n{e}", parent=form)

            conn = connect_db()
            cur = conn.cursor()
            # Use raw string values for lookup and insert
            cur.execute("SELECT brand FROM products WHERE type=? AND id=? AND od=? AND th=?",
                         (type_, raw_id, raw_od, raw_th))
            if not cur.fetchone():
                conn.close()
                return messagebox.showerror("Product Not Found", "This product does not exist. Please add it first.", parent=form)

            if mode == "Add":
                cur.execute("""INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                 (date, type_, raw_id, raw_od, raw_th, name, qty, price, is_restock))

            else:
                old_data = self.tran_tree.item(rowid)["values"]
                cur.execute("""UPDATE transactions SET date=?, type=?, id_size=?, od_size=?, th_size=?, name=?, quantity=?, price=?, is_restock=?
                                     WHERE rowid=?""",
                                 (date, type_, raw_id, raw_od, raw_th, name, qty, price, is_restock, rowid))
            conn.commit()
            conn.close()
            self.refresh_transactions()
            # Call the callback after a successful save
            if self.on_refresh_callback:
                self.on_refresh_callback()
            form.destroy()

        btn_row = tk.Frame(form)
        btn_row.pack(fill=tk.X, pady=(10, 5), padx=5)
        save_btn = tk.Button(btn_row, text="\u2714", font=("Arial", 12, "bold"), width=3, command=save)
        save_btn.pack(side=tk.RIGHT, anchor="e")
        form.bind("<Return>", save)

    def render_transactions(self, records):
        self.tran_tree.delete(*self.tran_tree.get_children())

        running_stock_map = defaultdict(int)
        all_rows = []

        for record in records:
            item_key = (record.type, record.id_size, record.od_size, record.th_size, record.brand)
            qty = abs(record.quantity)
            running_stock_map[item_key] += qty if record.is_restock else -qty
            all_rows.append((record, running_stock_map[item_key]))

        # After calculating running stock for all_rows:
        all_rows.sort(key=lambda x: parse_date_db(x[0].date), reverse=True)  # Descending date

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