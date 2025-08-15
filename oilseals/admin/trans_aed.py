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
    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price", "Stock"] # Added Stock field

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
        type_var = tk.StringVar(value="Sale") # New variable for transaction type
        
        # Hide/Show fields based on transaction type
        def select_type(value):
            type_var.set(value)
            
            # Reset button colors
            for btn in [restock_btn, sale_btn, actual_btn, fabrication_btn]:
                btn.config(bg="SystemButtonFace")
            
            # Set selected button color
            if value == "Restock":
                restock_btn.config(bg="blue")
            elif value == "Sale":
                sale_btn.config(bg="red")
            elif value == "Actual":
                actual_btn.config(bg="green")
            elif value == "Fabrication":
                fabrication_btn.config(bg="gray")
            
            # Show/hide fields
            if value in ["Restock", "Sale"]:
                qty_row.pack(anchor="w", padx=10, pady=5)
                price_row.pack(anchor="w", padx=10, pady=5)
                stock_row.pack_forget()
                price_label_var.set("Cost:" if value == "Restock" else "Price:")
                form.geometry("250x440")
            elif value == "Actual":
                qty_row.pack_forget()
                price_row.pack_forget()
                stock_row.pack(anchor="w", padx=10, pady=5)
                form.geometry("250x380")
            elif value == "Fabrication":
                # Fabrication logic will be added here later
                qty_row.pack(anchor="w", padx=10, pady=5)
                price_row.pack(anchor="w", padx=10, pady=5)
                stock_row.pack_forget()
                price_label_var.set("Cost:") # Or a different label
                form.geometry("250x440")
            
            # Update Price label
            price_label_var.set("Cost:" if value == "Restock" else "Price:")

        top_frame = tk.Frame(form)
        top_frame.pack(pady=10)
        restock_btn = tk.Button(top_frame, text="Restock", width=10, command=lambda: select_type("Restock"))
        restock_btn.pack(side=tk.LEFT, padx=5)
        sale_btn = tk.Button(top_frame, text="Sale", width=10, command=lambda: select_type("Sale"))
        sale_btn.pack(side=tk.LEFT, padx=5)
        actual_btn = tk.Button(top_frame, text="Actual", width=10, command=lambda: select_type("Actual"))
        actual_btn.pack(side=tk.LEFT, padx=5)
        fabrication_btn = tk.Button(top_frame, text="Fabrication", width=10, command=lambda: select_type("Fabrication"))
        fabrication_btn.pack(side=tk.LEFT, padx=5)

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

        # Quantity Row
        qty_row = tk.Frame(form)
        tk.Label(qty_row, text="Quantity:", width=8, anchor="w").pack(side=tk.LEFT)
        tk.Entry(qty_row, textvariable=vars["Quantity"], width=20).pack(side=tk.LEFT)

        # Price/Cost Row
        price_row = tk.Frame(form)
        tk.Label(price_row, textvariable=price_label_var, width=8, anchor="w").pack(side=tk.LEFT)
        tk.Entry(price_row, textvariable=vars["Price"], width=20).pack(side=tk.LEFT)
        
        # Stock Row (for Actual)
        stock_row = tk.Frame(form)
        tk.Label(stock_row, text="Stock:", width=8, anchor="w").pack(side=tk.LEFT)
        tk.Entry(stock_row, textvariable=vars["Stock"], width=20).pack(side=tk.LEFT)
        
        # Trace for number validation
        def validate_numbers(*_):
            for var_key in ["Quantity", "Price", "Stock"]:
                val = ''.join(c for c in vars[var_key].get() if c in '0123456789.')
                vars[var_key].set(val)

        vars["Quantity"].trace_add("write", validate_numbers)
        vars["Price"].trace_add("write", validate_numbers)
        vars["Stock"].trace_add("write", validate_numbers)

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
            else:
                # Assuming is_restock == 2 for Actual transaction
                type_str = "Actual"
                vars["Stock"].set(str(record.quantity)) # Actual stock is the quantity
                
            date_var.set(datetime.strptime(record.date, "%Y-%m-%d").strftime("%m/%d/%y"))
            select_type(type_str)
        else:
            select_type("Sale") # Default to Sale

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
                elif trans_type == "Actual":
                    stock_str = vars["Stock"].get()
                    if not stock_str:
                        return messagebox.showerror("Invalid", "Stock must be filled.", parent=form)
                    qty = int(stock_str)
                    price = 0
                    is_restock = 2 # 2 will represent Actual transaction
                elif trans_type == "Fabrication":
                    # Placeholder for Fabrication logic
                    qty_str = vars["Quantity"].get()
                    price_str = vars["Price"].get()
                    if not qty_str or not price_str:
                        return messagebox.showerror("Invalid", "Quantity and Price must be filled.", parent=form)
                    qty = int(qty_str)
                    price = float(price_str)
                    is_restock = 3 # 3 will represent Fabrication
                    
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