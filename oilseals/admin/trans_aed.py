import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
from ..database import connect_db


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
    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price", "Stock"]

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

            if self.on_refresh_callback:
                self.on_refresh_callback()

    def _get_record_by_id(self, rowid):
        # To be implemented/overridden as needed
        pass

    def _transaction_form(self, mode, record=None, rowid=None):
        form = tk.Toplevel(self.parent_frame)
        form.title(f"{mode} Transaction")
        # Removed fixed geometry to enable fitting based on content
        form.resizable(False, False)
        form.bind("<Escape>", lambda e: form.destroy())
        form.transient(self.parent_frame.winfo_toplevel())
        form.grab_set()

        vars = {key: tk.StringVar() for key in self.FIELDS}
        date_var = tk.StringVar()
        transaction_type_var = tk.StringVar(value="Sale")

        qty_restock_var = tk.StringVar()
        qty_customer_var = tk.StringVar()
        stock_left_var = tk.StringVar()

        def force_uppercase(var):
            text = var.get()
            upper_text = text.upper()
            if text != upper_text:
                var.set(upper_text)

        def validate_integer(new_val):
            if new_val == "":
                return True
            return new_val.isdigit()

        def validate_float_price(new_val):
            if new_val == "":
                return True
            try:
                float(new_val)
                if new_val.count(".") > 1:
                    return False
                return True
            except ValueError:
                return False

        def update_stock_left(*args):
            try:
                restock_qty = int(qty_restock_var.get()) if qty_restock_var.get() else 0
            except Exception:
                restock_qty = 0
            try:
                sold_qty = int(qty_customer_var.get()) if qty_customer_var.get() else 0
            except Exception:
                sold_qty = 0

            stock_left = restock_qty - sold_qty
            if stock_left < 0:
                stock_left_var.set("Error: Negative!")
            else:
                stock_left_var.set(str(stock_left))

        qty_restock_var.trace_add("write", update_stock_left)
        qty_customer_var.trace_add("write", update_stock_left)

        price_label_var = tk.StringVar(value="Price:")

        def select_transaction_type(value):
            transaction_type_var.set(value)
            for btn in [restock_btn, sale_btn, actual_btn, fabrication_btn]:
                btn.config(bg="SystemButtonFace")

            if value == "Restock":
                restock_btn.config(bg="blue")
                price_label_var.set("Cost:")
            elif value == "Sale":
                sale_btn.config(bg="red")
                price_label_var.set("Price:")
            elif value == "Actual":
                actual_btn.config(bg="green")
                price_label_var.set("Price:")
            elif value == "Fabrication":
                fabrication_btn.config(bg="gray")
                price_label_var.set("Price:")

            def enable_disable(widgets, enable):
                state = "normal" if enable else "disabled"
                for w in widgets:
                    w.config(state=state)

            if value in ["Restock", "Sale"]:
                enable_disable([quantity_entry], True)
                enable_disable([price_entry], True)
                enable_disable([stock_entry], False)
                enable_disable([qty_restock_entry, qty_customer_entry], False)
                stock_left_label.config(text="", fg="black")
            elif value == "Actual":
                enable_disable([quantity_entry], False)
                enable_disable([price_entry], False)
                enable_disable([stock_entry], True)
                enable_disable([qty_restock_entry, qty_customer_entry], False)
                stock_left_label.config(text="", fg="black")
            elif value == "Fabrication":
                enable_disable([quantity_entry], False)
                enable_disable([price_entry], True)
                enable_disable([stock_entry], False)
                enable_disable([qty_restock_entry, qty_customer_entry], True)
                if stock_left_var.get() == "Error: Negative!":
                    stock_left_label.config(text="Check Qty Sold vs Qty Restock!", fg="red")
                else:
                    stock_left_label.config(text="", fg="black")

        top_btn_frame = tk.Frame(form)
        top_btn_frame.pack(pady=10)
        restock_btn = tk.Button(top_btn_frame, text="Restock", width=10, command=lambda: select_transaction_type("Restock"))
        restock_btn.pack(side=tk.LEFT, padx=5)
        sale_btn = tk.Button(top_btn_frame, text="Sale", width=10, command=lambda: select_transaction_type("Sale"))
        sale_btn.pack(side=tk.LEFT, padx=5)

        bottom_btn_frame = tk.Frame(form)
        bottom_btn_frame.pack()
        actual_btn = tk.Button(bottom_btn_frame, text="Actual", width=10, command=lambda: select_transaction_type("Actual"))
        actual_btn.pack(side=tk.LEFT, padx=5, pady=5)
        fabrication_btn = tk.Button(bottom_btn_frame, text="Fabrication", width=10, command=lambda: select_transaction_type("Fabrication"))
        fabrication_btn.pack(side=tk.LEFT, padx=5, pady=5)

        date_row = tk.Frame(form)
        date_row.pack(pady=(5, 5))
        tk.Label(date_row, text="Date:").pack(side=tk.LEFT, padx=(0, 5))
        DateEntry(date_row, textvariable=date_var, date_pattern="mm/dd/yy", width=12).pack(side=tk.LEFT)

        fields = [
            ("Type", "Type"), ("ID", "ID"), ("OD", "OD"), ("TH", "TH"),
            ("Brand", "Brand"), ("Name", "Name")
        ]

        entry_widgets = {}

        for label_text, var_key in fields:
            row = tk.Frame(form)
            row.pack(anchor="w", padx=10, pady=(10 if label_text == "Type" else 5, 0))
            tk.Label(row, text=f"{label_text}:", width=8, anchor="w").pack(side=tk.LEFT)

            entry = tk.Entry(row, textvariable=vars[var_key], width=20)
            entry.pack(side=tk.LEFT)

            if var_key in ["ID", "OD", "TH"]:
                entry.config(validate='key', validatecommand=(form.register(validate_integer), '%P'))

            if var_key in ["Type", "Brand", "Name"]:
                def on_focus_out(event, var=vars[var_key]):
                    force_uppercase(var)
                entry.bind("<FocusOut>", on_focus_out)

            entry_widgets[var_key] = entry

        qty_row = tk.Frame(form)
        qty_row.pack(anchor="w", padx=10, pady=5)
        tk.Label(qty_row, text="Quantity:", width=8, anchor="w").pack(side=tk.LEFT)
        quantity_entry = tk.Entry(qty_row, textvariable=vars["Quantity"], width=20,
                                  validate='key', validatecommand=(form.register(validate_integer), '%P'))
        quantity_entry.pack(side=tk.LEFT)
        entry_widgets["Quantity"] = quantity_entry

        price_row = tk.Frame(form)
        price_row.pack(anchor="w", padx=10, pady=5)
        tk.Label(price_row, textvariable=price_label_var, width=8, anchor="w").pack(side=tk.LEFT)
        price_entry = tk.Entry(price_row, textvariable=vars["Price"], width=20,
                               validate='key', validatecommand=(form.register(validate_float_price), '%P'))
        price_entry.pack(side=tk.LEFT)
        entry_widgets["Price"] = price_entry

        stock_row = tk.Frame(form)
        stock_row.pack(anchor="w", padx=10, pady=5)
        tk.Label(stock_row, text="Stock:", width=8, anchor="w").pack(side=tk.LEFT)
        stock_entry = tk.Entry(stock_row, textvariable=vars["Stock"], width=20,
                               validate='key', validatecommand=(form.register(validate_integer), '%P'))
        stock_entry.pack(side=tk.LEFT)
        entry_widgets["Stock"] = stock_entry

        qty_restock_row = tk.Frame(form)
        qty_restock_row.pack(anchor="w", padx=10, pady=5)
        tk.Label(qty_restock_row, text="Qty Restock:", width=12, anchor="w").pack(side=tk.LEFT)
        qty_restock_entry = tk.Entry(qty_restock_row, textvariable=qty_restock_var, width=15,
                                    validate='key', validatecommand=(form.register(validate_integer), '%P'))
        qty_restock_entry.pack(side=tk.LEFT)

        qty_customer_row = tk.Frame(form)
        qty_customer_row.pack(anchor="w", padx=10, pady=5)
        tk.Label(qty_customer_row, text="Qty Sold:", width=12, anchor="w").pack(side=tk.LEFT)
        qty_customer_entry = tk.Entry(qty_customer_row, textvariable=qty_customer_var, width=15,
                                     validate='key', validatecommand=(form.register(validate_integer), '%P'))
        qty_customer_entry.pack(side=tk.LEFT)

        stock_left_row = tk.Frame(form)
        stock_left_row.pack(anchor="w", padx=10, pady=5)
        tk.Label(stock_left_row, text="Stock Left:", width=12, anchor="w").pack(side=tk.LEFT)
        stock_left_label = tk.Label(stock_left_row, textvariable=stock_left_var, width=10, relief=tk.SUNKEN, anchor="w")
        stock_left_label.pack(side=tk.LEFT)

        def on_stock_left_var_changed(*args):
            if stock_left_var.get() == "Error: Negative!":
                stock_left_label.config(fg="red")
            else:
                stock_left_label.config(fg="black")

        stock_left_var.trace_add("write", on_stock_left_var_changed)

        select_transaction_type(transaction_type_var.get())

        if mode == "Edit" and record:
            vars["Type"].set(record.type.upper())
            vars["ID"].set(record.id_size)
            vars["OD"].set(record.od_size)
            vars["TH"].set(record.th_size)
            vars["Brand"].set(record.brand.upper())
            vars["Name"].set(record.name.upper())

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
                vars["Quantity"].set("")
                qty_restock_var.set("")
                qty_customer_var.set(str(abs(record.quantity)))
                update_stock_left()
            else:
                type_str = "Sale"

            date_var.set(datetime.strptime(record.date, "%Y-%m-%d").strftime("%m/%d/%y"))
            transaction_type_var.set(type_str)
            select_transaction_type(type_str)
        else:
            transaction_type_var.set("Sale")
            select_transaction_type("Sale")
            for key in ["Quantity", "Price", "Stock", "ID", "OD", "TH", "Brand", "Name", "Type"]:
                vars[key].set("")
            qty_restock_var.set("")
            qty_customer_var.set("")
            stock_left_var.set("")

        def save(event=None):
            try:
                date = parse_date(date_var.get()).strftime("%Y-%m-%d")
                trans_type = transaction_type_var.get()
                item_type = vars["Type"].get().strip().upper()
                raw_id = vars["ID"].get().strip()
                raw_od = vars["OD"].get().strip()
                raw_th = vars["TH"].get().strip()
                brand = vars["Brand"].get().strip().upper()
                name = vars["Name"].get().strip().upper()

                qty = 0
                price = 0
                is_restock = 0

                if not all([item_type, raw_id, raw_od, raw_th, brand, name]):
                    return messagebox.showerror("Invalid", "Type, ID, OD, TH, Brand, and Name must be filled.", parent=form)

                if trans_type in ["Restock", "Sale"]:
                    qty_str = vars["Quantity"].get()
                    price_str = vars["Price"].get()
                    if not qty_str or not price_str:
                        return messagebox.showerror("Invalid", "Quantity and Price must be filled.", parent=form)
                    qty = abs(int(qty_str))
                    price = float(price_str)

                    if qty <= 0 or price <= 0:
                        return messagebox.showerror("Invalid", "Quantity and Price must be greater than 0.", parent=form)

                    is_restock = 1 if trans_type == "Restock" else 0
                    if is_restock == 0:
                        qty = -qty

                elif trans_type == "Actual":
                    stock_str = vars["Stock"].get()
                    if not stock_str:
                        return messagebox.showerror("Invalid", "Stock must be filled.", parent=form)
                    qty = int(stock_str)
                    price = 0
                    is_restock = 2

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
                                (item_type, raw_id, raw_od, raw_th))
                    if not cur.fetchone():
                        conn.close()
                        return messagebox.showerror("Product Not Found", "This product does not exist. Please add it first.", parent=form)

                    cur.execute("""INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (date, trans_type, raw_id, raw_od, raw_th, name, qty_restock_, 0, 1))
                    cur.execute("""INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (date, trans_type, raw_id, raw_od, raw_th, name, -qty_customer_, price_, 0))
                    conn.commit()
                    conn.close()

                    form.destroy()
                    if self.on_refresh_callback:
                        self.on_refresh_callback()
                    return

                else:
                    return messagebox.showerror("Invalid", "Unknown Transaction Type", parent=form)

                conn = connect_db()
                cur = conn.cursor()
                cur.execute("SELECT brand FROM products WHERE type=? AND id=? AND od=? AND th=?",
                            (item_type, raw_id, raw_od, raw_th))
                if not cur.fetchone():
                    conn.close()
                    return messagebox.showerror("Product Not Found", "This product does not exist. Please add it first.", parent=form)

                if mode == "Add":
                    cur.execute("""INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (date, trans_type, raw_id, raw_od, raw_th, name, qty, price, is_restock))
                else:
                    cur.execute("""UPDATE transactions SET date=?, type=?, id_size=?, od_size=?, th_size=?, name=?, quantity=?, price=?, is_restock=?
                                   WHERE rowid=?""",
                                (date, trans_type, raw_id, raw_od, raw_th, name, qty, price, is_restock, rowid))
                conn.commit()
                conn.close()

            except Exception as e:
                return messagebox.showerror("Invalid", f"Check all fields\n{e}", parent=form)

            if self.on_refresh_callback:
                self.on_refresh_callback()
            form.destroy()

        btn_row = tk.Frame(form)
        btn_row.pack(fill=tk.X, pady=(10, 5), padx=5)
        save_btn = tk.Button(btn_row, text="Save", font=("TkDefaultFont", 10), width=12, command=save)
        save_btn.pack(anchor="center")
        form.bind("<Return>", save)

        # Center and size window to content BEFORE focus & lift
        form.update_idletasks()
        w = form.winfo_width()
        h = form.winfo_height()
        center_window(form, w, h)

        form.focus_force()
        form.lift()
