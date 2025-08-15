import tkinter as tk
from tkinter import messagebox
from ..database import connect_db
from datetime import datetime
from tkcalendar import DateEntry


# Utility functions needed by the form
def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def format_currency(val):
    return f"\u20B1{val:.2f}"


def parse_date(text):
    return datetime.strptime(text, "%m/%d/%y")


class TransactionFormHandler:
    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price", "Stock"]  # Added Stock field

    def __init__(self, parent_frame, treeview, on_refresh_callback=None):
        self.parent_frame = parent_frame
        self.tran_tree = treeview
        self.on_refresh_callback = on_refresh_callback

    def add_transaction(self):
        self._transaction_form("Add")

    def edit_transaction(self):
        item = self.tran_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a transaction to edit", parent=self.parent_frame.winfo_toplevel())

        try:
            rowid = int(item)
            record_to_edit = self._get_record_by_id(rowid)
            if record_to_edit is None:
                messagebox.showerror("Error", "Selected record not found.", parent=self.parent_frame.winfo_toplevel())
                return
            self._transaction_form("Edit", record_to_edit, rowid)
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Could not retrieve transaction details.", parent=self.parent_frame.winfo_toplevel())

    def delete_transaction(self):
        items = self.tran_tree.selection()
        if not items:
            return messagebox.showwarning("Select", "Select transaction(s) to delete", parent=self.parent_frame.winfo_toplevel())

        confirm = messagebox.askyesno("Delete", f"Delete selected {len(items)} transaction(s)?", parent=self.parent_frame.winfo_toplevel())
        if confirm:
            conn = connect_db()
            cur = conn.cursor()
            for item in items:
                cur.execute("DELETE FROM transactions WHERE rowid=?", (item,))
            conn.commit()
            conn.close()

            self.on_refresh_callback() if self.on_refresh_callback else None

    def _get_record_by_id(self, rowid):
        # This will be overridden by the main class, so it's a placeholder.
        pass

    def _transaction_form(self, mode, record=None, rowid=None):
        form = tk.Toplevel(self.parent_frame)
        form.title(f"{mode} Transaction")
        center_window(form, 250, 520)
        form.resizable(False, False)
        form.bind("<Escape>", lambda e: form.destroy())
        form.transient(self.parent_frame.winfo_toplevel())
        form.grab_set()
        form.focus_force()
        form.lift()

        vars = {key: tk.StringVar() for key in self.FIELDS}
        date_var = tk.StringVar()
        type_var = tk.StringVar(value="Sale")  # New variable for transaction type

        # Additional vars for Fabrication
        qty_restock_var = tk.StringVar()
        qty_customer_var = tk.StringVar()
        stock_left_var = tk.StringVar()

        def update_stock_left(*args):
            try:
                restock_qty = int(qty_restock_var.get())
            except Exception:
                restock_qty = 0
            try:
                sold_qty = int(qty_customer_var.get())
            except Exception:
                sold_qty = 0

            stock_left = restock_qty - sold_qty
            if stock_left < 0:
                stock_left_var.set("Error: Neg")
            else:
                stock_left_var.set(str(stock_left))

        qty_restock_var.trace_add("write", update_stock_left)
        qty_customer_var.trace_add("write", update_stock_left)

        def select_type(value):
            type_var.set(value)

            for btn in [restock_btn, sale_btn, actual_btn, fabrication_btn]:
                btn.config(bg="SystemButtonFace")

            if value == "Restock":
                restock_btn.config(bg="blue")
            elif value == "Sale":
                sale_btn.config(bg="red")
            elif value == "Actual":
                actual_btn.config(bg="green")
            elif value == "Fabrication":
                fabrication_btn.config(bg="gray")

            if value in ["Restock", "Sale"]:
                qty_row.pack(anchor="w", padx=10, pady=5)
                price_row.pack(anchor="w", padx=10, pady=5)
                stock_row.pack_forget()
                qty_restock_row.pack_forget()
                qty_customer_row.pack_forget()
                stock_left_row.pack_forget()
                price_label_var.set("Cost:" if value == "Restock" else "Price:")
                form.geometry("250x440")
            elif value == "Actual":
                qty_row.pack_forget()
                price_row.pack_forget()
                stock_row.pack(anchor="w", padx=10, pady=5)
                qty_restock_row.pack_forget()
                qty_customer_row.pack_forget()
                stock_left_row.pack_forget()
                form.geometry("250x380")
            elif value == "Fabrication":
                qty_row.pack_forget()
                stock_row.pack_forget()
                price_row.pack(anchor="w", padx=10, pady=5)
                qty_restock_row.pack(anchor="w", padx=10, pady=5)
                qty_customer_row.pack(anchor="w", padx=10, pady=5)
                stock_left_row.pack(anchor="w", padx=10, pady=5)
                price_label_var.set("Price:")
                form.geometry("250x520")

            if value in ["Restock", "Sale"]:
                price_label_var.set("Cost:" if value == "Restock" else "Price:")

        top_btn_frame = tk.Frame(form)
        top_btn_frame.pack(pady=10)
        restock_btn = tk.Button(top_btn_frame, text="Restock", width=10, command=lambda: select_type("Restock"))
        restock_btn.pack(side=tk.LEFT, padx=5)
        sale_btn = tk.Button(top_btn_frame, text="Sale", width=10, command=lambda: select_type("Sale"))
        sale_btn.pack(side=tk.LEFT, padx=5)

        bottom_btn_frame = tk.Frame(form)
        bottom_btn_frame.pack()
        actual_btn = tk.Button(bottom_btn_frame, text="Actual", width=10, command=lambda: select_type("Actual"))
        actual_btn.pack(side=tk.LEFT, padx=5, pady=5)
        fabrication_btn = tk.Button(bottom_btn_frame, text="Fabrication", width=10, command=lambda: select_type("Fabrication"))
        fabrication_btn.pack(side=tk.LEFT, padx=5, pady=5)

        date_row = tk.Frame(form)
        date_row.pack(pady=(5, 5))
        tk.Label(date_row, text="Date:").pack(side=tk.LEFT, padx=(0, 5))
        DateEntry(date_row, textvariable=date_var, date_pattern="mm/dd/yy", width=12).pack(side=tk.LEFT)

        fields = [
            ("Type", "Type"), ("ID", "ID"), ("OD", "OD"), ("TH", "TH"),
            ("Brand", "Brand"), ("Name", "Name")
        ]

        price_label_var = tk.StringVar(value="Price:")

        for label_text, var_key in fields:
            row = tk.Frame(form)
            row.pack(anchor="w", padx=10, pady=(10 if label_text == "Type" else 5, 0))
            tk.Label(row, text=f"{label_text}:", width=8, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=vars[var_key], width=20)
            entry.pack(side=tk.LEFT)
            if var_key in ["Type", "Name", "Brand"]:
                vars[var_key].trace_add("write", lambda *_, k=var_key: vars[k].set(vars[k].get().upper()))

        qty_row = tk.Frame(form)
        tk.Label(qty_row, text="Quantity:", width=8, anchor="w").pack(side=tk.LEFT)
        tk.Entry(qty_row, textvariable=vars["Quantity"], width=20).pack(side=tk.LEFT)

        price_row = tk.Frame(form)
        tk.Label(price_row, textvariable=price_label_var, width=8, anchor="w").pack(side=tk.LEFT)
        tk.Entry(price_row, textvariable=vars["Price"], width=20).pack(side=tk.LEFT)

        stock_row = tk.Frame(form)
        tk.Label(stock_row, text="Stock:", width=8, anchor="w").pack(side=tk.LEFT)
        tk.Entry(stock_row, textvariable=vars["Stock"], width=20).pack(side=tk.LEFT)

        qty_restock_row = tk.Frame(form)
        tk.Label(qty_restock_row, text="Qty Restock:", width=12, anchor="w").pack(side=tk.LEFT)
        tk.Entry(qty_restock_row, textvariable=qty_restock_var, width=15).pack(side=tk.LEFT)

        qty_customer_row = tk.Frame(form)
        tk.Label(qty_customer_row, text="Qty Sold:", width=12, anchor="w").pack(side=tk.LEFT)
        tk.Entry(qty_customer_row, textvariable=qty_customer_var, width=15).pack(side=tk.LEFT)

        stock_left_row = tk.Frame(form)
        tk.Label(stock_left_row, text="Stock Left:", width=12, anchor="w").pack(side=tk.LEFT)
        tk.Label(stock_left_row, textvariable=stock_left_var, width=15, relief=tk.SUNKEN, anchor="w").pack(side=tk.LEFT)

        def validate_numbers(*_):
            for var_key in ["Quantity", "Price", "Stock"]:
                val = ''.join(c for c in vars[var_key].get() if c in '0123456789.')
                vars[var_key].set(val)

            def sanitize(var):
                val = ''.join(c for c in var.get() if c in '0123456789')
                var.set(val)

            sanitize(qty_restock_var)
            sanitize(qty_customer_var)

        vars["Quantity"].trace_add("write", validate_numbers)
        vars["Price"].trace_add("write", validate_numbers)
        vars["Stock"].trace_add("write", validate_numbers)
        qty_restock_var.trace_add("write", validate_numbers)
        qty_customer_var.trace_add("write", validate_numbers)

        if mode == "Edit" and record:
            vars["Type"].set(record.type)
            vars["ID"].set(record.id_size)
            vars["OD"].set(record.od_size)
            vars["TH"].set(record.th_size)
            vars["Brand"].set(record.brand)
            vars["Name"].set(record.name)

            if record.is_restock == 1:
                type_str = "Restock"
                vars["Quantity"].set(str(abs(record.quantity)))
                vars["Price"].set(f"{record.price:.2f}")
            elif record.is_restock == 0 and record.quantity < 0:
                type_str = "Sale"
                vars["Quantity"].set(str(abs(record.quantity)))
                vars["Price"].set(f"{record.price:.2f}")
            elif record.is_restock == 2:
                type_str = "Actual"
                vars["Stock"].set(str(record.quantity))
            elif record.is_restock == 3:
                type_str = "Fabrication"
                vars["Price"].set(f"{record.price:.2f}")
                vars["Quantity"].set(str(abs(record.quantity)))
                qty_restock_var.set("")
                qty_customer_var.set(str(abs(record.quantity)))
                update_stock_left()
            else:
                type_str = "Sale"

            date_var.set(datetime.strptime(record.date, "%Y-%m-%d").strftime("%m/%d/%y"))
            select_type(type_str)
        else:
            select_type("Sale")
            qty_restock_var.set("")
            qty_customer_var.set("")
            stock_left_var.set("")

        def save(event=None):
            try:
                date = parse_date(date_var.get()).strftime("%Y-%m-%d")
                type_ = vars["Type"].get().strip()
                raw_id = vars["ID"].get().strip()
                raw_od = vars["OD"].get().strip()
                raw_th = vars["TH"].get().strip()
                brand = vars["Brand"].get().strip().upper()
                name = vars["Name"].get().strip().upper()

                trans_type = type_var.get()
                qty = 0
                price = 0
                is_restock = 0

                if trans_type in ["Restock", "Sale"]:
                    qty_str = vars["Quantity"].get()
                    price_str = vars["Price"].get()
                    if not qty_str or not price_str:
                        return messagebox.showerror("Invalid", "Quantity and Price must be filled.", parent=form)
                    qty = abs(int(qty_str))
                    price = float(price_str)

                    if qty <= 0 or price <= 0:
                        return messagebox.showerror("Invalid", "Quantity and Price must be greater than 0.", parent=form)

                    if trans_type == "Restock":
                        is_restock = 1
                    else:
                        is_restock = 0
                        qty = -qty

                    conn = connect_db()
                    cur = conn.cursor()
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
                        cur.execute("""UPDATE transactions SET date=?, type=?, id_size=?, od_size=?, th_size=?, name=?, quantity=?, price=?, is_restock=?
                                        WHERE rowid=?""",
                                    (date, type_, raw_id, raw_od, raw_th, name, qty, price, is_restock, rowid))
                    conn.commit()
                    conn.close()

                elif trans_type == "Actual":
                    stock_str = vars["Stock"].get()
                    if not stock_str:
                        return messagebox.showerror("Invalid", "Stock must be filled.", parent=form)
                    qty = int(stock_str)
                    price = 0
                    is_restock = 2

                    conn = connect_db()
                    cur = conn.cursor()
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
                        cur.execute("""UPDATE transactions SET date=?, type=?, id_size=?, od_size=?, th_size=?, name=?, quantity=?, price=?, is_restock=?
                                        WHERE rowid=?""",
                                    (date, type_, raw_id, raw_od, raw_th, name, qty, price, is_restock, rowid))
                    conn.commit()
                    conn.close()

                elif trans_type == "Fabrication":
                    qty_restock_str = qty_restock_var.get()
                    qty_customer_str = qty_customer_var.get()
                    price_str = vars["Price"].get()
                    if not qty_restock_str or not qty_customer_str or not price_str:
                        return messagebox.showerror("Invalid", "All Fabrication fields must be filled.", parent=form)
                    qty_restock_ = int(qty_restock_str)
                    qty_customer_ = int(qty_customer_str)
                    price_ = float(price_str)
                    if qty_customer_ > qty_restock_:
                        return messagebox.showerror("Invalid", "Qty Sold cannot exceed Qty Restock.", parent=form)

                    conn = connect_db()
                    cur = conn.cursor()
                    cur.execute("SELECT brand FROM products WHERE type=? AND id=? AND od=? AND th=?",
                                (type_, raw_id, raw_od, raw_th))
                    if not cur.fetchone():
                        conn.close()
                        return messagebox.showerror("Product Not Found", "This product does not exist. Please add it first.", parent=form)

                    # Insert fabricated quantity as Restock transaction (positive qty, price=0)
                    cur.execute("""INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (date, type_, raw_id, raw_od, raw_th, name, qty_restock_, 0, 1))

                    # Insert sold quantity as Sale transaction (negative qty, price)
                    cur.execute("""INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (date, type_, raw_id, raw_od, raw_th, name, -qty_customer_, price_, 0))

                    conn.commit()
                    conn.close()

                    form.destroy()
                    self.on_refresh_callback() if self.on_refresh_callback else None
                    return

                else:
                    return messagebox.showerror("Invalid", "Unknown Transaction Type", parent=form)

            except Exception as e:
                return messagebox.showerror("Invalid", f"Check all fields\n{e}", parent=form)

            self.on_refresh_callback() if self.on_refresh_callback else None
            form.destroy()

        btn_row = tk.Frame(form)
        btn_row.pack(fill=tk.X, pady=(10, 5), padx=5)
        save_btn = tk.Button(btn_row, text="\u2714", font=("Arial", 12, "bold"), width=3, command=save)
        save_btn.pack(side=tk.RIGHT, anchor="e")
        form.bind("<Return>", save)
