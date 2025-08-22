import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from ..database import connect_db
from .gui_trans_aed import TransactionFormHandler


def format_currency(val):
    return f"\u20B1{val:.2f}"


def parse_date(text):
    return datetime.strptime(text, "%m/%d/%y")


def parse_date_db(text):
    return datetime.strptime(text, "%Y-%m-%d")


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


class TransactionTab:
    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price"]

    def __init__(self, notebook, main_app, controller, on_refresh_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_refresh_callback = on_refresh_callback

        # Support both ttk.Notebook and CTkFrame container
        if hasattr(notebook, "add"):
            self.frame = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(self.frame, text="Transactions")
        else:
            self.frame = notebook

        self.sort_direction = {}
        self.filtered_records = []
        self.date_filter_active = False

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

    # ─────────────── controls (search, filters, date) ───────────────
    def setup_controls(self):
        controls_section = ctk.CTkFrame(self.frame, fg_color="#374151", corner_radius=25)
        controls_section.pack(fill="x", padx=20, pady=(20, 15))

        controls_inner = ctk.CTkFrame(controls_section, fg_color="transparent")
        controls_inner.pack(fill="x", padx=20, pady=15)

        # Search row
        first_row = ctk.CTkFrame(controls_inner, fg_color="transparent")
        first_row.pack(fill="x", pady=(0, 10))

        search_frame = ctk.CTkFrame(first_row, fg_color="transparent")
        search_frame.pack(side="left", fill="x", expand=True)

        search_label = ctk.CTkLabel(search_frame, text="Search:", font=("Poppins", 14, "bold"), text_color="#FFFFFF")
        search_label.pack(side="left", padx=(0, 10))

        self.tran_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.tran_search_var,
            font=("Poppins", 13), fg_color="#2b2b2b", text_color="#FFFFFF",
            corner_radius=20, height=35, border_width=1, border_color="#4B5563",
            placeholder_text="Enter search term...", width=200
        )
        search_entry.pack(side="left", padx=(0, 20))
        self.tran_search_var.trace_add("write", lambda *args: self.refresh_transactions())

        # Restock filter
        restock_label = ctk.CTkLabel(first_row, text="Filter:", font=("Poppins", 14, "bold"), text_color="#FFFFFF")
        restock_label.pack(side="left", padx=(0, 10))

        self.restock_filter = tk.StringVar(value="All")
        restock_combo = ctk.CTkComboBox(
            first_row, variable=self.restock_filter,
            values=["All", "Restock", "Sale", "Actual", "Fabrication"],
            font=("Poppins", 13), dropdown_font=("Poppins", 12),
            fg_color="#2b2b2b", text_color="#FFFFFF",
            dropdown_fg_color="#2b2b2b", dropdown_text_color="#FFFFFF",
            button_color="#4B5563", button_hover_color="#6B7280",
            border_color="#4B5563", corner_radius=20, width=140, height=35, state="readonly"
        )
        restock_combo.pack(side="left")
        self.restock_filter.trace_add("write", lambda *args: self.refresh_transactions())

        # Second row - Date filter
        second_row = ctk.CTkFrame(controls_inner, fg_color="transparent")
        second_row.pack(fill="x")

        date_label = ctk.CTkLabel(second_row, text="Date:", font=("Poppins", 14, "bold"), text_color="#FFFFFF")
        date_label.pack(side="left", padx=(0, 10))

        self.date_var = tk.StringVar()
        date_frame = ctk.CTkFrame(second_row, fg_color="#2b2b2b", corner_radius=20, height=35)
        date_frame.pack(side="left", padx=(0, 10))
        date_frame.pack_propagate(False)

        self.date_filter = DateEntry(
            date_frame, date_pattern="mm/dd/yy", width=12,
            showweeknumbers=False, textvariable=self.date_var, state="readonly",
            background='#2b2b2b', foreground='#FFFFFF', borderwidth=0, relief='flat'
        )
        self.date_filter.pack(expand=True, padx=5, pady=2)
        self.date_var.set("")
        self.date_filter.bind('<<DateEntrySelected>>', self.on_date_selected)

        self.clear_btn = ctk.CTkButton(
            second_row, text="All Dates", font=("Poppins", 13, "bold"),
            fg_color="#6B7280", hover_color="#4B5563", text_color="#FFFFFF",
            corner_radius=20, width=100, height=35, command=self.clear_date_filter
        )
        self.clear_btn.pack(side="left")

    def on_date_selected(self, event=None):
        self.frame.after(50, self.apply_date_filter)
        self.frame.after(100, lambda: self.frame.focus_set())

    def apply_date_filter(self):
        self.date_filter_active = bool(self.date_var.get().strip())
        self.refresh_transactions()

    def clear_date_filter(self):
        self.date_var.set("")
        self.date_filter_active = False
        self.frame.focus_set()
        self.refresh_transactions()

    # ─────────────── treeview ───────────────
    def setup_treeview(self):
        table_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Transactions.Treeview",
                        background="#2b2b2b", foreground="#FFFFFF",
                        fieldbackground="#2b2b2b", font=("Poppins", 12),
                        rowheight=35)
        style.configure("Transactions.Treeview.Heading",
                        background="#000000", foreground="#D00000",
                        font=("Poppins", 12, "bold"))
        style.map("Transactions.Treeview", background=[("selected", "#374151")])

        self.tran_tree = ttk.Treeview(
            table_container,
            columns=("item", "date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings", selectmode="extended",
            style="Transactions.Treeview"
        )
        self.tran_tree.tag_configure("red", foreground="#EF4444")
        self.tran_tree.tag_configure("blue", foreground="#3B82F6")
        self.tran_tree.tag_configure("green", foreground="#22C55E")

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

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tran_tree.yview)
        self.tran_tree.configure(yscrollcommand=scrollbar.set)
        self.tran_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ─────────────── buttons (Add / Edit / Delete) ───────────────
    def setup_buttons(self):
        buttons_section = ctk.CTkFrame(self.frame, fg_color="transparent")
        buttons_section.pack(fill="x", padx=20, pady=(0, 20))

        button_container = ctk.CTkFrame(buttons_section, fg_color="transparent")
        button_container.pack(anchor="center")

        add_btn = ctk.CTkButton(
            button_container, text="Add", font=("Poppins", 16, "bold"),
            fg_color="#22C55E", hover_color="#16A34A", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.add_transaction
        )
        add_btn.pack(side="left", padx=(0, 10))

        edit_btn = ctk.CTkButton(
            button_container, text="Edit", font=("Poppins", 16, "bold"),
            fg_color="#4B5563", hover_color="#6B7280", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.edit_transaction
        )
        edit_btn.pack(side="left", padx=(0, 10))

        delete_btn = ctk.CTkButton(
            button_container, text="Delete", font=("Poppins", 16, "bold"),
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.delete_transaction
        )
        delete_btn.pack(side="left")

        root = self.frame.winfo_toplevel()
        root.bind("<Control-a>", lambda e: self.form_handler.add_transaction())
        root.bind("<Control-e>", lambda e: self.form_handler.edit_transaction())
        root.bind("<Delete>", lambda e: self.form_handler.delete_transaction())

    # ─────────────── transaction logic / refresh / rendering ───────────────
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

        # Simpler approach - check if there are matching restock/sale pairs on same date
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
        
        # Process the records chronologically to calculate running stock correctly
        records.sort(key=lambda r: (r.date, r.rowid))
        
        running_stock_map = defaultdict(int)
        all_rows = []
        for record in records:
            item_key = (record.type, record.id_size, record.od_size, record.th_size, record.brand)
            if record.is_restock == 2:
                running_stock_map[item_key] = record.quantity
            else:
                running_stock_map[item_key] += record.quantity
            all_rows.append((record, running_stock_map[item_key]))

        all_rows.sort(key=lambda x: (x[0].date, x[0].rowid), reverse=True)

        for record, stock in all_rows:
            item_str = f"{record.type} {record.id_size}-{record.od_size}-{record.th_size} {record.brand}"
            formatted_date = parse_date_db(record.date).strftime("%m/%d/%y")
            
            cost = ""
            price_str = ""
            qty_restock = ""
            qty_sale = ""
            
            tag = "gray"
            if record.is_restock == 1:
                tag = "blue"
                cost = format_currency(record.price)
                qty_restock = record.quantity
            elif record.is_restock == 0:
                tag = "red"
                price_str = format_currency(record.price)
                qty_sale = abs(record.quantity)
            elif record.is_restock == 2:
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
                return abs(record.quantity) if record.is_restock in [0, 1] else 0
            elif col == "cost" or col == "price":
                return record.price
            elif col == "name":
                return record.name.lower()
            else:
                return 0

        self.filtered_records.sort(key=sort_key, reverse=reverse)
        self.render_transactions(self.filtered_records)