import tkinter as tk
from tkinter import ttk, messagebox
from admin.transaction_tab import TransactionTab
from database import connect_db

class AdminPanel:
    def __init__(self, parent, main_app):
        self.main_app = main_app
        self.win = tk.Toplevel(parent)
        self.win.title("Manage Database")
        self.win.geometry("950x500")

        self.tabs = ttk.Notebook(self.win)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.create_products_tab()
        TransactionTab(self.tabs, self.main_app)

    def create_products_tab(self):
        frame = tk.Frame(self.tabs)
        self.tabs.add(frame, text="Products")

        search_frame = tk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(search_frame, text="Search ITEM:").pack(side=tk.LEFT)
        self.prod_search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.prod_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.prod_search_var.trace_add("write", lambda *args: self.refresh_products())

        self.prod_tree = ttk.Treeview(frame, columns=("item", "brand", "part_no", "origin", "notes", "price"), show="headings")
        headers = ["ITEM", "BRAND", "PART_NO", "ORIGIN", "NOTES", "PRICE"]
        for col, header in zip(self.prod_tree["columns"], headers):
            self.prod_tree.heading(col, text=header)
            self.prod_tree.column(col, width=120, anchor="center")
        self.prod_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self.refresh_products()

        btn_frame = tk.Frame(frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Add", command=self.add_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.edit_product).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_product).pack(side=tk.LEFT, padx=5)

    def refresh_products(self):
        for row in self.prod_tree.get_children():
            self.prod_tree.delete(row)
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price FROM products ORDER BY type ASC, id ASC, od ASC, th ASC")
        rows = cur.fetchall()
        conn.close()

        keyword = self.prod_search_var.get().lower()
        for row in rows:
            type_, id_, od, th, brand, part_no, origin, notes, price = row
            item_str = f"{type_.upper()} {id_}-{od}-{th}"
            combined = f"{type_} {id_} {od} {th}".lower()
            if keyword in combined:
                self.prod_tree.insert("", tk.END, values=(item_str, brand, part_no, origin, notes, f"₱{price:.2f}"))

    def add_product(self):
        self.product_form("Add Product")

    def edit_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to edit")
        item_str, brand, part_no, origin, notes, price = self.prod_tree.item(item)["values"]
        type_, size = item_str.split(" ")
        id_, od, th = map(int, size.split("-"))
        values = (type_, id_, od, th, brand, part_no, origin, notes, price.replace("₱", ""))
        self.product_form("Edit Product", values)

    def delete_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to delete")
        values = self.prod_tree.item(item)["values"]
        type_, size = values[0].split(" ")
        id_, od, th = map(int, size.split("-"))
        part_no = values[2]
        confirm = messagebox.askyesno("Delete", f"Delete {part_no}?")
        if confirm:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM products WHERE type=? AND id=? AND od=? AND th=? AND part_no=?", (type_, id_, od, th, part_no))
            conn.commit()
            conn.close()
            self.refresh_products()
            self.main_app.refresh_product_list()

    def product_form(self, title, values=None):
        form = tk.Toplevel(self.win)
        form.title(title)
        labels = ["type", "id", "od", "th", "brand", "part_no", "country_of_origin", "notes", "price"]
        vars = [tk.StringVar(value=str(v) if values else "") for v in (values or [""]*9)]

        def update_case(*args):
            vars[0].set(vars[0].get().upper())
            vars[4].set(vars[4].get().upper())
            vars[5].set(vars[5].get().upper())
            if vars[6].get():
                val = vars[6].get()
                vars[6].set(val[0].upper() + val[1:].lower() if len(val) > 1 else val.upper())

        for i, label in enumerate(labels):
            tk.Label(form, text=label.upper()).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = tk.Entry(form, textvariable=vars[i])
            entry.grid(row=i, column=1, padx=5, pady=2)
            vars[i].trace_add("write", update_case)

        def save():
            data = [v.get().strip() for v in vars]
            if not all(data[:5]):
                return messagebox.showerror("Missing", "Fill all required fields")
            try:
                data[1] = int(data[1])
                data[2] = int(data[2])
                data[3] = int(data[3])
                data[8] = float(data[8])
            except ValueError:
                return messagebox.showerror("Invalid", "Check numeric fields")

            conn = connect_db()
            cur = conn.cursor()
            if title.startswith("Add"):
                cur.execute("""INSERT INTO products (type, id, od, th, brand, part_no, country_of_origin, notes, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
            else:
                cur.execute("""UPDATE products SET type=?, id=?, od=?, th=?, brand=?, country_of_origin=?, notes=?, price=? WHERE part_no=?""", data[:5]+data[6:9]+[data[5]])
            conn.commit()
            conn.close()
            self.refresh_products()
            self.main_app.refresh_product_list()
            form.destroy()

        tk.Button(form, text="Save", command=save).grid(row=len(labels), column=0, columnspan=2, pady=10)
