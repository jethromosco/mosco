import tkinter as tk
from tkinter import ttk, messagebox
from oilseals.admin.transaction_tab import TransactionTab
from ..database import connect_db
from fractions import Fraction

# Helper to center any window
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
        TransactionTab(self.tabs, main_app, self.controller, on_refresh_callback=self.on_closing)
        
        # Add a protocol to call the callback when the window is closed
        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Callback function to handle window closing and trigger refresh in the main app."""
        if self.on_close_callback:
            self.on_close_callback()
        self.win.destroy()

    def create_products_tab(self):
        frame = tk.Frame(self.tabs)
        self.tabs.add(frame, text="Products")

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

        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Add", width=10, command=self.add_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", width=10, command=self.edit_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", width=10, command=self.delete_product).pack(side=tk.LEFT, padx=5)

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

    def add_product(self):
        self.product_form("Add Product")

    def edit_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to edit", parent=self.win)
        item_str, brand, part_no, origin, notes, price = self.prod_tree.item(item)["values"]
        type_, size = item_str.split(" ")
        id_str, od_str, th_str = size.split("-")
        values = (type_, id_str, od_str, th_str, brand, part_no, origin, notes, price.replace("₱", ""))
        self.product_form("Edit Product", values)

    def delete_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to delete", parent=self.win)
        values = self.prod_tree.item(item)["values"]
        type_, size = values[0].split(" ")
        id_str, od_str, th_str = size.split("-")
        brand = values[1]
        confirm = messagebox.askyesno("Confirm Delete", f"Delete {type_} {size} {brand}?", parent=self.win)
        if confirm:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM products WHERE type=? AND id=? AND od=? AND th=? AND brand=?
            """, (type_, id_str, od_str, th_str, brand))
            conn.commit()
            conn.close()
            self.refresh_products()
            # Call the callback after a successful deletion
            if self.on_close_callback:
                self.on_close_callback()

    def product_form(self, title, values=None):
        form = tk.Toplevel(self.win)
        form.title(title)
        form.resizable(False, False)
        form.grab_set()

        container = tk.Frame(form, padx=16, pady=14)
        container.pack()

        if title.startswith("Edit") and values:
            item_str = f"{values[0]} {values[1]}-{values[2]}-{values[3]}"
            tk.Label(container, text=item_str, font=("TkDefaultFont", 10, "bold")).pack(pady=(0, 6))

        fields = [
            ("TYPE", 0),
            ("ID (mm)", 1),
            ("OD (mm)", 2),
            ("TH (mm)", 3),
            ("BRAND", 4),
            ("PART_NO", 5),
            ("ORIGIN", 6),
            ("NOTES", 7),
            ("PRICE (₱)", 8),
        ]

        vars = [tk.StringVar(value=str(values[i]) if values else "") for i in range(9)]

        def validate_characters(*_):
            vars[0].set(''.join(filter(str.isalpha, vars[0].get())).upper())
            vars[4].set(''.join(filter(str.isalpha, vars[4].get())).upper())
            vars[6].set(vars[6].get().capitalize())

        def validate_numbers(*_):
            for i in [1, 2, 3]:
                val = vars[i].get().strip()
                allowed_chars = "0123456789./"
                vars[i].set(''.join(c for c in val if c in allowed_chars))
            val = ''.join(c for c in vars[8].get() if c in '0123456789.')
            vars[8].set(val)

        for i, (label, idx) in enumerate(fields):
            row = tk.Frame(container)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, width=12, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=vars[idx]).pack(side="left", fill="x", expand=True)

        for i in [0, 4, 6]:
            vars[i].trace_add("write", validate_characters)
        for i in [1, 2, 3, 8]:
            vars[i].trace_add("write", validate_numbers)

        def save():
            data = [v.get().strip() for v in vars]
            if not all(data[i] for i in [0, 1, 2, 3, 4]):
                return messagebox.showerror("Missing", "Fill all required fields")
            try:
                data[8] = float(data[8])
            except ValueError as e:
                return messagebox.showerror("Invalid", str(e))

            conn = connect_db()
            cur = conn.cursor()
            if title.startswith("Add"):
                cur.execute("""
                    INSERT INTO products (type, id, od, th, brand, part_no, country_of_origin, notes, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
            else:
                cur.execute("""
                    UPDATE products
                    SET type=?, id=?, od=?, th=?, brand=?, part_no=?, country_of_origin=?, notes=?, price=?
                    WHERE type=? AND id=? AND od=? AND th=? AND brand=?
                """, data + [values[0], values[1], values[2], values[3], values[4]])
            conn.commit()
            conn.close()
            self.refresh_products()
            # Call the callback after a successful save
            if self.on_close_callback:
                self.on_close_callback()
            form.destroy()

        btn_frame = tk.Frame(container, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="Save", width=12, command=save).pack()

        form.update_idletasks()
        w = form.winfo_width()
        h = form.winfo_height()
        center_window(form, w, h)