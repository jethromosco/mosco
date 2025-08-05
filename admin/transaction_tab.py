import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from database import connect_db

# Helper to center a window on the screen
def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

class TransactionTab:
    def __init__(self, notebook, main_app):
        self.main_app = main_app
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="Transactions")

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

        tk.Label(control_frame, text="Sort by:").pack(side=tk.LEFT, padx=(20, 0))
        self.sort_tran_by = tk.StringVar(value="Date")
        ttk.Combobox(control_frame, textvariable=self.sort_tran_by,
                     values=["Date", "Quantity", "Price"], width=10, state="readonly").pack(side=tk.LEFT)
        self.sort_tran_by.trace_add("write", lambda *args: self.refresh_transactions())

    def setup_treeview(self):
        self.tran_tree = ttk.Treeview(
            self.frame,
            columns=("item", "date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings"
        )
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
            self.tran_tree.heading(col, text=header)
            self.tran_tree.column(col, **column_config[col])

        self.tran_tree.tag_configure("red", foreground="red")
        self.tran_tree.tag_configure("blue", foreground="blue")
        self.tran_tree.pack(fill=tk.BOTH, expand=True, pady=10)

    def setup_buttons(self):
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Add", command=self.add_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.edit_transaction).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_transaction).pack(side=tk.LEFT, padx=5)

    def refresh_transactions(self):
        self.tran_tree.delete(*self.tran_tree.get_children())
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.date, t.type, t.id_size, t.od_size, t.th_size, t.name, t.quantity, t.price, t.is_restock, 
                   p.brand
            FROM transactions t
            LEFT JOIN products p ON t.type = p.type AND t.id_size = p.id AND t.od_size = p.od AND t.th_size = p.th
        """)
        rows = cur.fetchall()
        conn.close()

        keyword = self.tran_search_var.get().lower()
        restock_filter = self.restock_filter.get()
        sort_key = self.sort_tran_by.get()

        filtered = []
        for row in rows:
            date, type_, id_, od, th, name, qty, price, is_restock, brand = row
            brand = brand or ""
            item_str = f"{type_} {id_}-{od}-{th} {brand}"
            if keyword not in f"{date} {item_str} {name}".lower():
                continue
            if restock_filter == "Restock" and not is_restock:
                continue
            if restock_filter == "Sale" and is_restock:
                continue
            filtered.append(row)

        if sort_key == "Date":
            filtered.sort(key=lambda x: x[0])
        elif sort_key == "Quantity":
            filtered.sort(key=lambda x: abs(x[6]))
        elif sort_key == "Price":
            filtered.sort(key=lambda x: x[7])

        from collections import defaultdict
        grouped = defaultdict(list)
        for row in filtered:
            type_, id_, od, th, brand = row[1], row[2], row[3], row[4], row[9]
            item_key = (type_, id_, od, th, brand)
            grouped[item_key].append(row)

        all_rows = []
        for item_rows in grouped.values():
            item_rows.sort(key=lambda x: x[0])
            running_stock = 0
            for row in item_rows:
                qty = abs(row[6])
                is_restock = row[8]
                running_stock += qty if is_restock else -qty
                all_rows.append((row, running_stock))

        for row, stock in reversed(all_rows):
            date, type_, id_, od, th, name, qty, price, is_restock, brand = row
            item_str = f"{type_} {id_}-{od}-{th} {brand}"
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%y")
            cost = f"\u20B1{price:.2f}" if is_restock else ""
            price_str = f"\u20B1{price:.2f}" if not is_restock else ""
            tag = "blue" if is_restock else "red"
            qty_restock = abs(qty) if is_restock else ""
            qty_sale = abs(qty) if not is_restock else ""

            self.tran_tree.insert("", tk.END, values=(
                item_str, formatted_date, qty_restock, cost, name, qty_sale, price_str, abs(stock)
            ), tags=(tag,))

    def add_transaction(self):
        self.transaction_form("Add")

    def edit_transaction(self):
        item = self.tran_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a transaction to edit")
        values = self.tran_tree.item(item)["values"]
        self.transaction_form("Edit", values)

    def transaction_form(self, mode, values=None):
        form = tk.Toplevel(self.frame)
        form.title(f"{mode} Transaction")
        center_window(form, 250, 440)  # <- Centered form window
        form.resizable(False, False)

        field_order = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price"]
        vars = {key: tk.StringVar() for key in field_order}
        date_var = tk.StringVar()
        restock_var = tk.StringVar(value="Sale")
        price_label_var = tk.StringVar(value="Price:")

        if mode == "Edit" and values:
            item = values[0]
            type_, size, brand = item.split(" ", 2)
            id_, od, th = map(int, size.split("-"))
            is_restock = "Restock" if "blue" in self.tran_tree.item(self.tran_tree.focus())["tags"] else "Sale"

            vars["Type"].set(type_)
            vars["ID"].set(id_)
            vars["OD"].set(od)
            vars["TH"].set(th)
            vars["Brand"].set(brand)
            vars["Name"].set(values[4])
            vars["Quantity"].set(values[2] if is_restock == "Restock" else values[5])
            vars["Price"].set(str(values[3] if is_restock == "Restock" else values[6]).replace("\u20B1", ""))
            date_var.set(datetime.strptime(values[1], "%m/%d/%y").strftime("%m/%d/%y"))
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
        date_entry = DateEntry(date_row, textvariable=date_var, date_pattern="mm/dd/yy", width=12)
        date_entry.pack(side=tk.LEFT)

        for key in field_order:
            row = tk.Frame(form)
            row.pack(anchor="w", padx=10, pady=(10 if key == "Type" else 5, 0))
            label_var = price_label_var if key == "Price" else tk.StringVar(value=f"{key}:")
            tk.Label(row, textvariable=label_var, width=8, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=vars[key], width=20)
            entry.pack(side=tk.LEFT)
            if key in ["Type", "Name", "Brand"]:
                vars[key].trace_add("write", lambda *a, k=key: vars[k].set(vars[k].get().upper()))

        def save(event=None):
            try:
                date = datetime.strptime(date_var.get(), "%m/%d/%y").strftime("%Y-%m-%d")
                type_ = vars["Type"].get()
                id_, od, th = int(vars["ID"].get()), int(vars["OD"].get()), int(vars["TH"].get())
                brand = vars["Brand"].get().strip().upper()
                name = vars["Name"].get().strip().upper()
                qty = abs(int(vars["Quantity"].get()))
                price = float(vars["Price"].get())
                is_restock = 1 if restock_var.get() == "Restock" else 0
                qty = qty if is_restock else -qty
            except Exception as e:
                return messagebox.showerror("Invalid", f"Check all fields\n{e}")

            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT brand FROM products WHERE type=? AND id=? AND od=? AND th=?",
                        (type_, id_, od, th))
            product = cur.fetchone()
            if not product:
                conn.close()
                return messagebox.showerror("Product Not Found", "This product does not exist in the products table. Please add it first.")

            if mode == "Add":
                cur.execute("""INSERT INTO transactions (date, type, id_size, od_size, th_size, name, quantity, price, is_restock)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (date, type_, id_, od, th, name, qty, price, is_restock))
            else:
                selected = self.tran_tree.item(self.tran_tree.focus())["values"]
                old_date = datetime.strptime(selected[1], "%m/%d/%y").strftime("%Y-%m-%d")
                cur.execute("""UPDATE transactions SET date=?, type=?, id_size=?, od_size=?, th_size=?, name=?, quantity=?, price=?, is_restock=?
                               WHERE date=? AND name=?""",
                            (date, type_, id_, od, th, name, qty, price, is_restock, old_date, selected[4]))
            conn.commit()
            conn.close()
            self.refresh_transactions()
            self.main_app.refresh_product_list()
            form.destroy()

        btn_row = tk.Frame(form)
        btn_row.pack(fill=tk.X, pady=(10, 5), padx=5)
        save_btn = tk.Button(btn_row, text="\u2714", font=("Arial", 12, "bold"), width=3, command=save)
        save_btn.pack(side=tk.RIGHT, anchor="e")
        form.bind("<Return>", save)

    def delete_transaction(self):
        item = self.tran_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a transaction to delete")
        values = self.tran_tree.item(item)["values"]
        confirm = messagebox.askyesno("Delete", f"Delete transaction on {values[1]}?")
        if confirm:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""DELETE FROM transactions
                           WHERE date=? AND type=? AND id_size=? AND od_size=? AND th_size=? AND name=? AND quantity=?""",
                        (datetime.strptime(values[1], "%m/%d/%y").strftime("%Y-%m-%d"),
                         *values[0].split(" ")[0:1],
                         *map(int, values[0].split(" ")[1].split("-")),
                         values[4],
                         int(values[5]) if values[5] else int(values[2])))
            conn.commit()
            conn.close()
            self.refresh_transactions()
            self.main_app.refresh_product_list()
