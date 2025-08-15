import tkinter as tk
from tkinter import messagebox
from ..database import connect_db
from fractions import Fraction
from datetime import datetime

# Utility functions needed by the form are defined here to avoid circular imports.
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

class ProductFormHandler:
    def __init__(self, parent_window, treeview, on_refresh_callback=None):
        self.parent_window = parent_window
        self.prod_tree = treeview
        self.on_refresh_callback = on_refresh_callback

    def add_product(self):
        self.product_form("Add Product")

    def edit_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to edit", parent=self.parent_window)
        
        item_str, brand, part_no, origin, notes, price = self.prod_tree.item(item)["values"]
        type_, size = item_str.split(" ", 1)
        try:
            id_str, od_str, th_str = size.split("-")
        except ValueError:
            # Handle cases where size string might be malformed
            id_str, od_str, th_str = "", "", ""
        
        values = (type_, id_str, od_str, th_str, brand, part_no, origin, notes, price.replace("₱", ""))
        self.product_form("Edit Product", values)

    def delete_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to delete", parent=self.parent_window)
        
        values = self.prod_tree.item(item)["values"]
        item_str, brand = values[0], values[1]
        try:
            type_, size = item_str.split(" ", 1)
            id_str, od_str, th_str = size.split("-")
        except ValueError:
            type_, id_str, od_str, th_str = "", "", "", ""
        
        confirm = messagebox.askyesno("Confirm Delete", f"Delete {type_} {size} {brand}?", parent=self.parent_window)
        if confirm:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM products WHERE type=? AND id=? AND od=? AND th=? AND brand=?
            """, (type_, id_str, od_str, th_str, brand))
            conn.commit()
            conn.close()
            
            if self.on_refresh_callback:
                self.on_refresh_callback()

    def product_form(self, title, values=None):
        form = tk.Toplevel(self.parent_window)
        form.title(title)
        form.resizable(False, False)
        form.grab_set()
        
        container = tk.Frame(form, padx=16, pady=14)
        container.pack()

        if title.startswith("Edit") and values:
            item_str = f"{values[0]} {values[1]}-{values[2]}-{values[3]}"
            tk.Label(container, text=item_str, font=("TkDefaultFont", 10, "bold")).pack(pady=(0, 6))

        fields = [
            ("TYPE", 0), ("ID (mm)", 1), ("OD (mm)", 2), ("TH (mm)", 3), ("BRAND", 4),
            ("PART_NO", 5), ("ORIGIN", 6), ("NOTES", 7), ("PRICE (₱)", 8)
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
            
            if self.on_refresh_callback:
                self.on_refresh_callback()
            form.destroy()

        btn_frame = tk.Frame(container, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="Save", width=12, command=save).pack()

        form.update_idletasks()
        w = form.winfo_width()
        h = form.winfo_height()
        center_window(form, w, h)