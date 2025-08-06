import tkinter as tk
from tkinter import ttk
from database import connect_db
from admin.admin_panel import AdminPanel
from .transaction_window import TransactionWindow

LOW_STOCK_THRESHOLD = 5
OUT_OF_STOCK = 0

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
        self.root.bind("<Escape>", lambda e: self.clear_filters())

    def get_var(self, key):
        return self.search_vars[key].get().strip()

    def create_widgets(self):
        back_btn = tk.Button(self, text="← Back", anchor="w", padx=10, pady=5)
        if self.controller:
            back_btn.config(command=self.controller.go_back)
        else:
            back_btn.config(command=self.master.destroy)
        back_btn.pack(anchor="nw", padx=10, pady=(10, 0))

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
        self.tree.tag_configure("low", background="#fff8dc")  # light yellow
        self.tree.tag_configure("out", background="#ffe5e5")  # light red

        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, anchor="center", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.open_transaction_page)

        self.status_label = tk.Label(self, text="", anchor="w")
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 5))

    def update_inch_label(self, key):
        try:
            mm_value = float(self.get_var(key))
            inches = mm_value * 0.0393701
            self.inch_labels[key].config(text=f'{inches:.3f}\"', fg="black")
        except ValueError:
            self.inch_labels[key].config(text="")

    def open_admin_panel(self):
        AdminPanel(self.root, self)

    def clear_filters(self):
        for var in self.search_vars.values():
            var.set("")

    def stock_filter_matches(self, qty):
        filter_type = self.stock_filter.get()
        if filter_type == "Low Stock":
            return 0 < qty <= LOW_STOCK_THRESHOLD
        if filter_type == "Out of Stock":
            return qty == OUT_OF_STOCK
        if filter_type == "In Stock":
            return qty > OUT_OF_STOCK
        return True

    def refresh_product_list(self):
        self.tree.delete(*self.tree.get_children())

        with connect_db() as conn:
            cur = conn.cursor()

            query = """SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price FROM products WHERE 1=1"""
            params = []
            for key, var in self.search_vars.items():
                val = self.get_var(key)
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

            cur.execute("""SELECT type, id_size, od_size, th_size, SUM(quantity)
                           FROM transactions GROUP BY type, id_size, od_size, th_size""")
            stock_map = {(r[0], r[1], r[2], r[3]): r[4] for r in cur.fetchall()}

        display_data = []
        for row in products:
            type_, id_, od, th, brand, part_no, origin, notes, price = row
            qty = stock_map.get((type_, id_, od, th), 0)
            if not self.stock_filter_matches(qty):
                continue
            size_str = f"{id_}-{od}-{th}"
            display_data.append((type_, size_str, brand, part_no, origin, notes, qty, f"₱{price:.2f}", id_, od, th))

        if self.sort_by.get() == "Size":
            display_data.sort(key=lambda x: (x[8], x[9], x[10]))
        elif self.sort_by.get() == "Quantity":
            display_data.sort(key=lambda x: x[6], reverse=True)

        for item in display_data:
            tag = "out" if item[6] == OUT_OF_STOCK else "low" if item[6] <= LOW_STOCK_THRESHOLD else ""
            self.tree.insert("", tk.END, values=item[:8], tags=(tag,))

        self.status_label.config(text=f"Total products: {len(display_data)}")

    def open_transaction_page(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])["values"]
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
            win = tk.Toplevel(self)
            TransactionWindow(win, details, self)
