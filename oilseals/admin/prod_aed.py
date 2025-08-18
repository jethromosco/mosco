import tkinter as tk
from tkinter import messagebox
from ..database import connect_db
from fractions import Fraction
from datetime import datetime
import ast


def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def parse_measurement(value):
    """Convert a string (fraction or decimal) to float for validation."""
    try:
        if "/" in value:
            return float(Fraction(value))
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid measurement: {value}")


def safe_str_extract(value):
    """Safely convert lists or stringified lists to simple comma-separated string."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return ", ".join(str(v) for v in parsed)
    except Exception:
        pass
    return str(value)


class ProductFormHandler:
    FIELDS = ["TYPE", "ID", "OD", "TH", "BRAND", "PART_NO", "ORIGIN", "NOTES", "PRICE"]

    def __init__(self, parent_window, treeview, on_refresh_callback=None):
        self.parent_window = parent_window
        self.prod_tree = treeview
        self.on_refresh_callback = on_refresh_callback

    def add_product(self):
        self._product_form("Add Product")

    def edit_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to edit", parent=self.parent_window)

        values = self.prod_tree.item(item)["values"]

        # Defensive unpacking with fallback
        try:
            item_str = values[0]
        except IndexError:
            messagebox.showerror("Error", "Invalid selection data.", parent=self.parent_window)
            return

        try:
            type_, size = item_str.split(" ", 1)
            id_str, od_str, th_str = size.split("-")
        except ValueError:
            type_, id_str, od_str, th_str = "", "", "", ""

        brand = values[1] if len(values) > 1 else ""
        part_no = values[2] if len(values) > 2 else ""
        origin = safe_str_extract(values[3]) if len(values) > 3 else ""
        notes = safe_str_extract(values[4]) if len(values) > 4 else ""
        price = values[5] if len(values) > 5 else "0"

        edit_values = (type_, id_str, od_str, th_str, brand, part_no, origin, notes, price.replace("₱", ""))

        self._product_form("Edit Product", edit_values)

    def delete_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to delete", parent=self.parent_window)

        values = self.prod_tree.item(item)["values"]
        try:
            item_str = values[0]
            brand = values[1]
        except IndexError:
            messagebox.showerror("Error", "Invalid selection data.", parent=self.parent_window)
            return

        try:
            type_, size = item_str.split(" ", 1)
            id_str, od_str, th_str = size.split("-")
        except ValueError:
            type_, id_str, od_str, th_str = "", "", "", ""

        confirm = messagebox.askyesno("Confirm Delete", f"Delete {type_} {size} {brand}?", parent=self.parent_window)
        if confirm:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM products WHERE type=? AND id=? AND od=? AND th=? AND brand=?",
                (type_, id_str, od_str, th_str, brand)
            )
            conn.commit()
            conn.close()
            if self.on_refresh_callback:
                self.on_refresh_callback()

    def _product_form(self, title, values=None):
        form = tk.Toplevel(self.parent_window)
        form.title(title)
        form.resizable(False, False)
        form.transient(self.parent_window)
        form.grab_set()
        form.bind("<Escape>", lambda e: form.destroy())

        container = tk.Frame(form, padx=16, pady=14)
        container.pack()

        vars = {field: tk.StringVar(value=(str(values[idx]) if values else "")) for idx, field in enumerate(self.FIELDS)}

        if title.startswith("Edit") and values:
            item_str = f"{values[0]} {values[1]}-{values[2]}-{values[3]}"
            tk.Label(container, text=item_str, font=("TkDefaultFont", 10, "bold")).pack(pady=(0, 6))

        def force_uppercase(*args):
            vars["TYPE"].set(''.join(filter(str.isalpha, vars["TYPE"].get())).upper())
            vars["BRAND"].set(''.join(filter(str.isalpha, vars["BRAND"].get())).upper())
            origin_txt = vars["ORIGIN"].get()
            vars["ORIGIN"].set(origin_txt.capitalize())

        def validate_numbers(*args):
            for key in ["ID", "OD", "TH"]:
                val = vars[key].get().strip()
                allowed_chars = "0123456789./"
                vars[key].set(''.join(c for c in val if c in allowed_chars))
            price_val = ''.join(c for c in vars["PRICE"].get() if c in '0123456789.')
            vars["PRICE"].set(price_val)

        for field in self.FIELDS:
            row = tk.Frame(container)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{field.replace('_', ' ')}:", width=12, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=vars[field]).pack(side="left", fill="x", expand=True)

        # Attach validation trace
        vars["TYPE"].trace_add("write", force_uppercase)
        vars["BRAND"].trace_add("write", force_uppercase)
        vars["ORIGIN"].trace_add("write", force_uppercase)
        for key in ["ID", "OD", "TH", "PRICE"]:
            vars[key].trace_add("write", validate_numbers)

        def save(event=None):
            try:
                data = [vars[field].get().strip() for field in self.FIELDS]

                # Validate required fields: TYPE, ID, OD, TH, BRAND
                if not all(data[i] for i in range(5)):
                    return messagebox.showerror("Missing", "Fill all required fields", parent=form)

                # Validate measurements
                for field in ["ID", "OD", "TH"]:
                    parse_measurement(data[self.FIELDS.index(field)])

                # Validate price
                data[self.FIELDS.index("PRICE")] = float(data[self.FIELDS.index("PRICE")])

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

            except ValueError as ve:
                messagebox.showerror("Invalid Input", str(ve), parent=form)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred:\n{e}", parent=form)

        btn_row = tk.Frame(container, pady=10)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Save", width=12, command=save).pack()
        form.bind("<Return>", save)

        form.update_idletasks()
        w, h = form.winfo_width(), form.winfo_height()
        center_window(form, w, h)
        form.focus_force()
        form.lift()
