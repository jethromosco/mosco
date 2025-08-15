import tkinter as tk
from tkinter import ttk, messagebox
from oilseals.admin.transactions import TransactionTab
from ..database import connect_db
from fractions import Fraction
from .prod_aed import ProductFormHandler # Import the new handler class

# Only the utility functions needed by this file remain here
def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

def parse_measurement(value):
    """Convert a string (fraction or decimal) to float for sorting, keep original for display."""
    try:
        if "/" in value:
            return float(Fraction(value))
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid measurement: {value}")


class AdminPanel:
    def __init__(self, parent, main_app, controller, on_close_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_close_callback = on_close_callback
        self.win = tk.Toplevel(parent)
        self.win.title("Manage Database")
        center_window(self.win, 950, 500)

        self.tabs = ttk.Notebook(self.win)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.create_products_tab()
        # Pass the controller AND the callback to TransactionTab
        TransactionTab(self.tabs, main_app, self.controller, on_refresh_callback=self.refresh_all_tabs)
        
        # Add a protocol to call the callback when the window is closed
        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def refresh_all_tabs(self):
        """Refresh products tab + main app without closing AdminPanel."""
        self.refresh_products()
        if self.on_close_callback:
            self.on_close_callback()

    def on_closing(self):
        """Callback function to handle window closing and trigger refresh in the main app."""
        if self.on_close_callback:
            self.on_close_callback()
        self.win.destroy()

    def create_products_tab(self):
        frame = tk.Frame(self.tabs)
        self.tabs.add(frame, text="Products")

        # Instantiate the new handler class, passing the necessary arguments
        self.prod_form_handler = ProductFormHandler(self.win, None, self.refresh_products)

        # Search bar
        search_frame = tk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(search_frame, text="Search ITEM:").pack(side=tk.LEFT)
        self.prod_search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.prod_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.prod_search_var.trace_add("write", lambda *args: self.refresh_products())

        # Treeview
        columns = ("item", "brand", "part_no", "origin", "notes", "price")
        self.headers = ["ITEM", "BRAND", "PART_NO", "ORIGIN", "NOTES", "PRICE"]
        self.sort_direction = {col: None for col in columns}
        self.prod_tree = ttk.Treeview(frame, columns=columns, show="headings")

        for col, header in zip(columns, self.headers):
            self.prod_tree.heading(col, text=header, command=lambda c=col: self.sort_column(c))
            self.prod_tree.column(col, width=120, anchor="center")

        self.prod_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Now pass the actual treeview to the handler
        self.prod_form_handler.prod_tree = self.prod_tree

        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack()
        # Call the methods from the new handler class
        tk.Button(btn_frame, text="Add", width=10, command=self.prod_form_handler.add_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", width=10, command=self.prod_form_handler.edit_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", width=10, command=self.prod_form_handler.delete_product).pack(side=tk.LEFT, padx=5)

        self.refresh_products()

    def refresh_products(self):
        self.prod_tree.delete(*self.prod_tree.get_children())

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price
            FROM products
            ORDER BY type ASC, id ASC, od ASC, th ASC
        """)
        rows = cur.fetchall()
        conn.close()

        keyword = self.prod_search_var.get().lower()
        for row in rows:
            type_, id_, od, th, brand, part_no, origin, notes, price = row

            def fmt(val):
                return str(val) if isinstance(val, str) else (str(int(val)) if float(val).is_integer() else str(val))

            id_str = fmt(id_)
            od_str = fmt(od)
            th_str = fmt(th)

            item_str = f"{type_.upper()} {id_str}-{od_str}-{th_str}"
            combined = f"{type_} {id_str} {od_str} {th_str}".lower()

            if keyword in combined:
                self.prod_tree.insert("", tk.END,
                    values=(item_str, brand, part_no, origin, notes, f"₱{price:.2f}")
                )

    def sort_column(self, col):
        if col in ("part_no", "notes"):
            return

        ascending = self.sort_direction[col] != "asc"
        self.sort_direction[col] = "asc" if ascending else "desc"

        data = [(self.prod_tree.set(child, col), child) for child in self.prod_tree.get_children()]

        if col == "item":
            def size_key(val):
                try:
                    size_str = val[0].split(" ")[1]
                    parts = size_str.split("-")
                    return tuple(parse_measurement(p) for p in parts)
                except:
                    return (0, 0, 0)
            data.sort(key=lambda x: size_key(x), reverse=not ascending)
        elif col == "price":
            data.sort(key=lambda x: float(x[0].replace("₱", "").replace(",", "")), reverse=not ascending)
        else:
            data.sort(key=lambda x: x[0].lower(), reverse=not ascending)

        for index, (_, child) in enumerate(data):
            self.prod_tree.move(child, '', index)

        for c, h in zip(self.prod_tree["columns"], self.headers):
            arrow = " ↑" if c == col and ascending else " ↓" if c == col else ""
            self.prod_tree.heading(c, text=h + arrow)