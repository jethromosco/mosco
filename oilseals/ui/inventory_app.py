import tkinter as tk
from tkinter import ttk
from database import connect_db
from admin.admin_panel import AdminPanel
from .transaction_window import TransactionWindow

class InventoryApp(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.root = controller.root if controller else self.winfo_toplevel()

        self.root.title("Oil Seal Inventory Manager")
        self.root.attributes("-fullscreen", True)

        self.search_vars = {
            "type": tk.StringVar(),
            "id": tk.StringVar(),
            "od": tk.StringVar(),
            "th": tk.StringVar(),
            "part_no": tk.StringVar(),
            "country": tk.StringVar()
        }

        self.sort_by = tk.StringVar(value="Size")
        self.stock_filter = tk.StringVar(value="All")

        self.create_widgets()
        self.refresh_product_list()

    def create_widgets(self):
        # Top bar with Back button
        topbar = tk.Frame(self)
        topbar.pack(fill=tk.X)
        if self.controller:
            tk.Button(topbar, text="← Back", command=self.controller.go_back).pack(side=tk.LEFT, padx=10, pady=5)
        else:
            tk.Button(topbar, text="← Back", command=self.master.destroy).pack(side=tk.LEFT, padx=10, pady=5)


        search_frame = tk.Frame(self)
        search_frame.pack(pady=5)

        self.inch_labels = {}

        for idx, (key, var) in enumerate(self.search_vars.items()):
            tk.Label(search_frame, text=key.upper()).grid(row=0, column=idx * 2)
            entry = tk.Entry(search_frame, textvariable=var, width=10)
            entry.grid(row=0, column=idx * 2 + 1)
            var.trace_add("write", lambda *args: self.refresh_product_list())

            if key in ["id", "od", "th"]:
                label = tk.Label(search_frame, text="", fg="gray", font=("Arial", 8))
                label.grid(row=1, column=idx * 2 + 1)
                self.inch_labels[key] = label
                var.trace_add("write", lambda *args, k=key: self.update_inch_label(k))

        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=5)

        tk.Label(filter_frame, text="Sort by:").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.sort_by, values=["Size", "Quantity"], state="readonly", width=10).pack(side=tk.LEFT, padx=5)
        self.sort_by.trace_add("write", lambda *args: self.refresh_product_list())

        tk.Label(filter_frame, text="Stock:").pack(side=tk.LEFT)
        ttk.Combobox(filter_frame, textvariable=self.stock_filter, values=["All", "In Stock", "Low Stock", "Out of Stock"], state="readonly", width=12).pack(side=tk.LEFT, padx=5)
        self.stock_filter.trace_add("write", lambda *args: self.refresh_product_list())

        columns = ("type", "size", "brand", "part_no", "origin", "notes", "qty", "price")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, anchor="center", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.open_transaction_page)

    def update_inch_label(self, key):
        try:
            mm_value = float(self.search_vars[key].get())
            inches = mm_value * 0.0393701
            self.inch_labels[key].config(text=f'{inches:.3f}"', fg="black")
        except ValueError:
            self.inch_labels[key].config(text="")

    def open_admin_panel(self):
        AdminPanel(self.root, self)

    def refresh_product_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = connect_db()
        cur = conn.cursor()

        query = """SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price FROM products WHERE 1=1"""
        params = []
        for key, var in self.search_vars.items():
            val = var.get().strip()
            if val:
                col = 'country_of_origin' if key == 'country' else key
                if key in ["id", "od", "th"] and val.isdigit():
                    query += f" AND {col} = ?"
                    params.append(int(val))
                else:
                    query += f" AND {col} LIKE ?"
                    params.append(f"%{val}%")

        cur.execute(query, params)
        products = cur.fetchall()

        cur.execute("SELECT type, id_size, od_size, th_size, SUM(quantity) FROM transactions GROUP BY type, id_size, od_size, th_size")
        stock_map = {(r[0], r[1], r[2], r[3]): r[4] for r in cur.fetchall()}

        display_data = []
        for row in products:
            type_, id_, od, th, brand, part_no, origin, notes, price = row
            qty = stock_map.get((type_, id_, od, th), 0)
            size_str = f"{id_}-{od}-{th}"
            if self.stock_filter.get() == "In Stock" and qty <= 5:
                continue
            if self.stock_filter.get() == "Low Stock" and (qty > 5 or qty <= 0):
                continue
            if self.stock_filter.get() == "Out of Stock" and qty != 0:
                continue
            display_data.append((type_, size_str, brand, part_no, origin, notes, qty, f"₱{price:.2f}", id_, od, th))

        if self.sort_by.get() == "Size":
            display_data.sort(key=lambda x: (x[8], x[9], x[10]))
        elif self.sort_by.get() == "Quantity":
            display_data.sort(key=lambda x: x[6], reverse=True)

        for item in display_data:
            self.tree.insert("", tk.END, values=item[:8])

        conn.close()

    def open_transaction_page(self, event):
        item = self.tree.item(self.tree.selection())["values"]
        if not item:
            return
        id_, od, th = map(int, item[1].split("-"))
        details = {
            "type": item[0],
            "id": id_,
            "od": od,
            "th": th,
            "brand": item[2],
            "part_no": item[3],
            "country_of_origin": item[4],
            "notes": item[5],
            "quantity": item[6],
            "price": float(item[7].replace("₱", ""))
        }

        if self.controller:
            self.controller.show_transaction_window(details, self)
        else:
            # fallback to old method if no controller
            win = tk.Toplevel(self)
            TransactionWindow(win, details, self)

    def go_home(self):
        if self.controller:
            self.controller.show_home()
        else:
            self.root.destroy()
