import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
from ..database import connect_db # This path might need to be adjusted based on your project structure
# add edit delete for transaction tab

# All the utility functions are now defined here
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
    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price"]

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
        center_window(form, 250, 440)
        form.resizable(False, False)
        form.bind("<Escape>", lambda e: form.destroy())
        form.transient(self.parent_frame.winfo_toplevel())
        form.grab_set()
        form.focus_force()
        form.lift()

        vars = {key: tk.StringVar() for key in self.FIELDS}
        date_var = tk.StringVar()
        restock_var = tk.StringVar(value="Sale")
        price_label_var = tk.StringVar(value="Price:")

        if mode == "Edit" and record:
            vars["Type"].set(record.type)
            vars["ID"].set(record.id_size)
            vars["OD"].set(record.od_size)
            vars["TH"].set(record.th_size)
            vars["Brand"].set(record.brand)
            vars["Name"].set(record.name)
            vars["Quantity"].set(str(abs(record.quantity)))
            vars["Price"].set(f"{record.price:.2f}")
            date_var.set(datetime.strptime(record.date, "%Y-%m-%d").strftime("%m/%d/%y"))
            
            is_restock_str = "Restock" if record.is_restock else "Sale"
            restock_var.set(is_restock_str)
            price_label_var.set("Cost:" if is_restock_str == "Restock" else "Price:")

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
        DateEntry(date_row, textvariable=date_var, date_pattern="mm/dd/yy", width=12).pack(side=tk.LEFT)

        for key in self.FIELDS:
            row = tk.Frame(form)
            row.pack(anchor="w", padx=10, pady=(10 if key == "Type" else 5, 0))
            label_var = price_label_var if key == "Price" else tk.StringVar(value=f"{key}:")
            tk.Label(row, textvariable=label_var, width=8, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(row, textvariable=vars[key], width=20)
            entry.pack(side=tk.LEFT)
            if key in ["Type", "Name", "Brand"]:
                vars[key].trace_add("write", lambda *_, k=key: vars[k].set(vars[k].get().upper()))

        def save(event=None):
            try:
                date = parse_date(date_var.get()).strftime("%Y-%m-%d")
                type_ = vars["Type"].get().strip()
                raw_id = vars["ID"].get().strip()
                raw_od = vars["OD"].get().strip()
                raw_th = vars["TH"].get().strip()
                brand = vars["Brand"].get().strip().upper()
                name = vars["Name"].get().strip().upper()
                qty = abs(int(vars["Quantity"].get()))
                price = float(vars["Price"].get())
                if qty <= 0 or price <= 0:
                    return messagebox.showerror("Invalid", "Quantity and Price must be greater than 0.", parent=form)
                is_restock = 1 if restock_var.get() == "Restock" else 0
                qty = qty if is_restock else -qty
            except Exception as e:
                return messagebox.showerror("Invalid", f"Check all fields\n{e}", parent=form)

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
            
            self.on_refresh_callback() if self.on_refresh_callback else None
            form.destroy()

        btn_row = tk.Frame(form)
        btn_row.pack(fill=tk.X, pady=(10, 5), padx=5)
        save_btn = tk.Button(btn_row, text="\u2714", font=("Arial", 12, "bold"), width=3, command=save)
        save_btn.pack(side=tk.RIGHT, anchor="e")
        form.bind("<Return>", save)