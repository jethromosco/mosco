import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from ..database import connect_db
from .transaction_window import TransactionWindow
from fractions import Fraction
from oilseals.admin.products import AdminPanel

LOW_STOCK_THRESHOLD = 5
OUT_OF_STOCK = 0

class InventoryApp(tk.Frame):
    def __init__(self, master, controller=None):
        super().__init__(master)
        self.controller = controller
        self.root = controller.root if controller else self.winfo_toplevel()

        self.root.title("Oil Seal Inventory Manager")
        self.root.attributes("-fullscreen", True)

        self.search_vars = {
            "type": tk.StringVar(),
            "id": tk.StringVar(),
            "od": tk.StringVar(),
            "th": tk.StringVar(),
            "brand": tk.StringVar(),
            "part_no": tk.StringVar()
        }

        self.sort_by = tk.StringVar(value="Size")
        self.stock_filter = tk.StringVar(value="All")
        self.search_var = tk.StringVar()

        self.create_widgets()
        self.refresh_product_list()
        self.root.bind("<Escape>", lambda e: self.clear_filters())

    def get_var(self, key):
        return self.search_vars[key].get().strip()

    def parse_number(self, val):
        try:
            return float(val)
        except Exception:
            return 0

    def format_display_value(self, value):
        """Format so fractions stay as fractions, decimals show only if needed"""
        value = str(value).strip()
        if "/" in value:  # fraction, keep as is
            return value
        try:
            num = float(value)
            if num.is_integer():
                return str(int(num))
            else:
                return str(num)
        except ValueError:
            return value

    def create_widgets(self):
        back_btn = tk.Button(self, text="← Back", anchor="w", padx=10, pady=5)
        if self.controller:
            # Go back to the page set in self.return_to
            back_btn.config(command=lambda: self.controller.go_back(self.return_to))
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
        display_names = {
            "type": "TYPE",
            "size": "SIZE",
            "brand": "BRAND",
            "part_no": "PART NO.",
            "origin": "ORIGIN",
            "notes": "NOTES",
            "qty": "QTY",
            "price": "PRICE"
        }
        # --- CREATE TREEVIEW FIRST ---
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.tag_configure("low", background="#fff8dc")
        self.tree.tag_configure("out", background="#ffe5e5")

        for col in columns:
            self.tree.heading(col, text=display_names.get(col, col.upper()))
            self.tree.column(col, anchor="center", width=100)
        # Force "PART NO." header
        self.tree.heading("part_no", text="PART NO.")

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.open_transaction_page)

        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.status_label = tk.Label(bottom_frame, text="", anchor="w")
        self.status_label.pack(side=tk.LEFT)

        admin_btn = ttk.Button(bottom_frame, text="Admin", command=self.open_admin_panel)
        admin_btn.pack(side=tk.RIGHT)

    def open_admin_panel(self):
        password = simpledialog.askstring("Admin Access", "Enter password:", show="*")
        if password == "569656":
            current_frame_name = self.controller.get_current_frame_name()
            current_frame = self.controller.frames[current_frame_name]
            # Pass the refresh function as a callback
            AdminPanel(self.controller.root, current_frame, self.controller, on_close_callback=self.refresh_product_list)
        else:
            messagebox.showerror("Access Denied", "Incorrect password.")

    def update_inch_label(self, key):
        raw_value = self.get_var(key)
        if not raw_value.strip():
            self.inch_labels[key].config(text="")
            return
        try:
            if "/" in raw_value:
                parts = raw_value.split("/")
                inch_str = []
                for part in parts:
                    mm = self.parse_number(part)
                    inch = mm * 0.0393701
                    inch_str.append(f'{inch:.3f}')
                self.inch_labels[key].config(text="/".join(inch_str) + '"', fg="black")
            else:
                mm_value = self.parse_number(raw_value)
                inches = mm_value * 0.0393701
                self.inch_labels[key].config(text=f'{inches:.3f}"', fg="black")
        except Exception:
            self.inch_labels[key].config(text="")

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

    def refresh_product_list(self, clear_filters=False):
        if clear_filters:
            for var in self.search_vars.values():
                var.set("")
            self.sort_by.set("Size")
            self.stock_filter.set("All")
            self.search_var.set("")

        self.tree.delete(*self.tree.get_children())

        with connect_db() as conn:
            cur = conn.cursor()

            query = """SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price 
                        FROM products WHERE 1=1"""
            params = []
            for key, var in self.search_vars.items():
                val = self.get_var(key)
                if val:
                    col = 'brand' if key == 'brand' else key
                    query += f" AND {col} LIKE ?"
                    params.append(f"%{val}%")

            cur.execute(query, params)
            products = cur.fetchall()

            # --- UPDATED STOCK CALCULATION LOGIC ---
            # Instead of a simple SUM, we now build a map of transactions per item
            cur.execute("""SELECT type, id_size, od_size, th_size, quantity, is_restock 
                           FROM transactions ORDER BY date ASC""")
            all_transactions = cur.fetchall()
            
            stock_map = {}
            for row in all_transactions:
                type_, id_raw, od_raw, th_raw, quantity, is_restock = row
                key = (type_, id_raw, od_raw, th_raw)
                
                # Check for an 'Actual' transaction
                if is_restock == 2:
                    stock_map[key] = quantity
                else:
                    stock_map[key] = stock_map.get(key, 0) + quantity
            # ----------------------------------------
            
        display_data = []
        for row in products:
            type_, id_raw, od_raw, th_raw, brand, part_no, origin, notes, price = row
            qty = stock_map.get((type_, id_raw, od_raw, th_raw), 0)
            if not self.stock_filter_matches(qty):
                continue

            id_num = self.parse_number(id_raw)
            od_num = self.parse_number(od_raw)
            th_num = self.parse_number(th_raw)

            size_str = f"{self.format_display_value(id_raw)}-{self.format_display_value(od_raw)}-{self.format_display_value(th_raw)}"
            display_data.append((type_, size_str, brand, part_no, origin, notes, qty, f"₱{price:.2f}", id_raw, od_raw, th_raw))

        def parse_thickness_sort(th_raw):
            th_raw = str(th_raw).strip()
            if "/" in th_raw:
                try:
                    main, sub = map(float, th_raw.split("/", 1))
                    return (main, sub)
                except Exception:
                    try:
                        return (float(th_raw.split("/")[0]), 0)
                    except ValueError:
                        return (0, 0)
            else:
                try:
                    return (float(th_raw), 0)
                except Exception:
                    return (0, 0)

        # In your refresh_product_list method, replace the sort block:
        if self.sort_by.get() == "Size":
            display_data.sort(
                key=lambda x: (
                    self.parse_number(x[8]),  # ID as float
                    self.parse_number(x[9]),  # OD as float
                    parse_thickness_sort(x[10])  # TH as tuple (main, sub)
                )
            )
        elif self.sort_by.get() == "Quantity":
            display_data.sort(key=lambda x: x[6], reverse=True)

        id_search = self.get_var("id")
        od_search = self.get_var("od")
        th_search = self.get_var("th")
        search_term = self.search_var.get().strip()

        filtered_data = []
        for item in display_data:
            # item[8] = id_raw, item[9] = od_raw, item[10] = th_raw
            id_match = (not id_search or str(item[8]).strip() == id_search)
            od_match = (not od_search or str(item[9]).strip() == od_search)
            th_match = (not th_search or str(item[10]).strip() == th_search)

            if id_match and od_match and th_match:
                filtered_data.append(item)

        for item in filtered_data:
            tag = "out" if item[6] == OUT_OF_STOCK else "low" if item[6] <= LOW_STOCK_THRESHOLD else ""
            self.tree.insert("", tk.END, values=item[:8], tags=(tag,))

        self.status_label.config(text=f"Total products: {len(filtered_data)}")

    def open_transaction_page(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])["values"]

        id_str, od_str, th_str = item[1].split("-")
        details = {
            "type": item[0],
            "id": id_str,
            "od": od_str,
            "th": th_str,
            "brand": item[2],
            "part_no": item[3],
            "country_of_origin": item[4],
            "notes": item[5],
            "quantity": item[6],
            "price": float(item[7].replace("₱", ""))
        }

        if self.controller:
            # Ensure we always return to THIS MM page, not HomePage
            for name, frame in self.controller.frames.items():
                if frame is self:
                    mm_frame_name = name
                    break
            else:
                mm_frame_name = self.controller.get_current_frame_name()  # fallback

            self.controller.show_transaction_window(details, self, return_to=mm_frame_name)
        else:
            win = tk.Toplevel(self)
            TransactionWindow(win, details, self)