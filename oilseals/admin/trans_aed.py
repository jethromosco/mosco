import customtkinter as ctk
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

        # Create custom confirmation dialog matching the app style
        parent_window = self.parent_frame.winfo_toplevel()
        confirm_window = ctk.CTkToplevel(parent_window)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x200")
        confirm_window.resizable(False, False)
        confirm_window.configure(fg_color="#000000")
        
        # Center the window
        confirm_window.transient(parent_window)
        confirm_window.grab_set()
        
        # Center positioning
        confirm_window.update_idletasks()
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        x = parent_x + (parent_width - 400) // 2
        y = parent_y + (parent_height - 200) // 2
        confirm_window.geometry(f"400x200+{x}+{y}")
        
        # Main container
        main_frame = ctk.CTkFrame(confirm_window, fg_color="#2b2b2b", corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Question text
        question_label = ctk.CTkLabel(
            main_frame,
            text=f"Delete selected {len(items)} transaction(s)?",
            font=("Poppins", 16, "bold"),
            text_color="#FFFFFF"
        )
        question_label.pack(pady=(30, 40))
        
        # Button container
        button_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_container.pack(pady=(0, 20))
        
        def confirm_delete():
            conn = connect_db()
            cur = conn.cursor()
            for item in items:
                cur.execute("DELETE FROM transactions WHERE rowid=?", (item,))
            conn.commit()
            conn.close()

            if self.on_refresh_callback:
                self.on_refresh_callback()
            confirm_window.destroy()
        
        def cancel_delete():
            confirm_window.destroy()
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            font=("Poppins", 14, "bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=40,
            command=cancel_delete
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # Confirm button
        confirm_btn = ctk.CTkButton(
            button_container,
            text="Delete",
            font=("Poppins", 14, "bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=40,
            command=confirm_delete
        )
        confirm_btn.pack(side="right")
        
        # Key bindings
        confirm_window.bind('<Escape>', lambda e: cancel_delete())
        confirm_window.bind('<Return>', lambda e: confirm_delete())
        
        # Focus on confirm window
        confirm_window.focus()

    def _get_record_by_id(self, rowid):
        # To be implemented/overridden as needed
        pass

    def _transaction_form(self, mode, record=None, rowid=None):
        # Create CustomTkinter form window
        form = ctk.CTkToplevel(self.parent_frame.winfo_toplevel())
        form.title(f"{mode} Transaction")
        
        # IMPORTANT FIX: Make window invisible initially to prevent flashing
        form.withdraw()
        
        form.resizable(False, False)
        form.configure(fg_color="#000000")
        form.transient(self.parent_frame.winfo_toplevel())
        form.grab_set()
        form.bind("<Escape>", lambda e: form.destroy())

        # Main container with the app's styling
        container = ctk.CTkFrame(form, fg_color="#2b2b2b", corner_radius=40)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Inner container for form content
        inner_container = ctk.CTkFrame(container, fg_color="transparent")
        inner_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Form title
        title_label = ctk.CTkLabel(
            inner_container,
            text=f"{mode} Transaction",
            font=("Poppins", 20, "bold"),
            text_color="#D00000"
        )
        title_label.pack(pady=(0, 20))

        # Form variables
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

        # Transaction type buttons section
        type_section = ctk.CTkFrame(inner_container, fg_color="#374151", corner_radius=25)
        type_section.pack(fill="x", pady=(0, 20))
        
        type_inner = ctk.CTkFrame(type_section, fg_color="transparent")
        type_inner.pack(fill="x", padx=20, pady=15)
        
        type_label = ctk.CTkLabel(
            type_inner,
            text="Transaction Type:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF"
        )
        type_label.pack(pady=(0, 10))

        # Button containers
        top_btn_container = ctk.CTkFrame(type_inner, fg_color="transparent")
        top_btn_container.pack(pady=(0, 10))
        
        bottom_btn_container = ctk.CTkFrame(type_inner, fg_color="transparent")
        bottom_btn_container.pack()

        def select_transaction_type(value):
            transaction_type_var.set(value)
            
            # Reset all button colors
            restock_btn.configure(fg_color="#4B5563", hover_color="#6B7280")
            sale_btn.configure(fg_color="#4B5563", hover_color="#6B7280")
            actual_btn.configure(fg_color="#4B5563", hover_color="#6B7280")
            fabrication_btn.configure(fg_color="#4B5563", hover_color="#6B7280")

            if value == "Restock":
                restock_btn.configure(fg_color="#3B82F6", hover_color="#2563EB")
                price_label_var.set("Cost:")
            elif value == "Sale":
                sale_btn.configure(fg_color="#EF4444", hover_color="#DC2626")
                price_label_var.set("Price:")
            elif value == "Actual":
                actual_btn.configure(fg_color="#22C55E", hover_color="#16A34A")
                price_label_var.set("Price:")
            elif value == "Fabrication":
                fabrication_btn.configure(fg_color="#6B7280", hover_color="#4B5563")
                price_label_var.set("Price:")

            def enable_disable(widgets, enable):
                state = "normal" if enable else "disabled"
                for w in widgets:
                    w.configure(state=state)

            if value in ["Restock", "Sale"]:
                enable_disable([quantity_entry], True)
                enable_disable([price_entry], True)
                enable_disable([stock_entry], False)
                enable_disable([qty_restock_entry, qty_customer_entry], False)
                stock_left_label.configure(text_color="#FFFFFF")
            elif value == "Actual":
                enable_disable([quantity_entry], False)
                enable_disable([price_entry], False)
                enable_disable([stock_entry], True)
                enable_disable([qty_restock_entry, qty_customer_entry], False)
                stock_left_label.configure(text_color="#FFFFFF")
            elif value == "Fabrication":
                enable_disable([quantity_entry], False)
                enable_disable([price_entry], True)
                enable_disable([stock_entry], False)
                enable_disable([qty_restock_entry, qty_customer_entry], True)
                if stock_left_var.get() == "Error: Negative!":
                    stock_left_label.configure(text="Check Qty Sold vs Qty Restock!", text_color="#EF4444")
                else:
                    stock_left_label.configure(text_color="#FFFFFF")

        # Create transaction type buttons
        restock_btn = ctk.CTkButton(
            top_btn_container,
            text="Restock",
            font=("Poppins", 14, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=40,
            command=lambda: select_transaction_type("Restock")
        )
        restock_btn.pack(side="left", padx=(0, 10))
        
        sale_btn = ctk.CTkButton(
            top_btn_container,
            text="Sale",
            font=("Poppins", 14, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=40,
            command=lambda: select_transaction_type("Sale")
        )
        sale_btn.pack(side="left")
        
        actual_btn = ctk.CTkButton(
            bottom_btn_container,
            text="Actual",
            font=("Poppins", 14, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=40,
            command=lambda: select_transaction_type("Actual")
        )
        actual_btn.pack(side="left", padx=(0, 10))
        
        fabrication_btn = ctk.CTkButton(
            bottom_btn_container,
            text="Fabrication",
            font=("Poppins", 14, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=40,
            command=lambda: select_transaction_type("Fabrication")
        )
        fabrication_btn.pack(side="left")

        # Form fields section
        fields_section = ctk.CTkFrame(inner_container, fg_color="transparent")
        fields_section.pack(fill="x", pady=(0, 20))

        # Date field
        date_frame = ctk.CTkFrame(fields_section, fg_color="transparent")
        date_frame.pack(fill="x", pady=8)
        date_frame.grid_columnconfigure(1, weight=1)
        
        date_label = ctk.CTkLabel(
            date_frame,
            text="Date:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            width=80,
            anchor="w"
        )
        date_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # Create a styled frame for the date picker
        date_picker_frame = ctk.CTkFrame(date_frame, fg_color="#374151", corner_radius=20, height=35)
        date_picker_frame.grid(row=0, column=1, sticky="ew")
        date_picker_frame.pack_propagate(False)
        
        date_entry = DateEntry(
            date_picker_frame,
            textvariable=date_var,
            date_pattern="mm/dd/yy",
            width=12,
            background='#374151',
            foreground='#FFFFFF',
            borderwidth=0,
            relief='flat'
        )
        date_entry.pack(expand=True, padx=5, pady=2)

        # Form input fields
        fields = [
            ("Type", "Type"), ("ID", "ID"), ("OD", "OD"), ("TH", "TH"),
            ("Brand", "Brand"), ("Name", "Name")
        ]

        entry_widgets = {}

        for label_text, var_key in fields:
            # Field container
            field_frame = ctk.CTkFrame(fields_section, fg_color="transparent")
            field_frame.pack(fill="x", pady=8)
            field_frame.grid_columnconfigure(1, weight=1)
            
            # Label
            label = ctk.CTkLabel(
                field_frame,
                text=f"{label_text}:",
                font=("Poppins", 14, "bold"),
                text_color="#FFFFFF",
                width=80,
                anchor="w"
            )
            label.grid(row=0, column=0, sticky="w", padx=(0, 15))
            
            # Entry field
            entry = ctk.CTkEntry(
                field_frame,
                textvariable=vars[var_key],
                font=("Poppins", 13),
                fg_color="#374151",
                text_color="#FFFFFF",
                corner_radius=20,
                height=35,
                border_width=1,
                border_color="#4B5563"
            )
            entry.grid(row=0, column=1, sticky="ew")
            
            # Add hover effects for entry fields
            def on_entry_enter(event, ent=entry):
                if ent.focus_get() != ent:
                    ent.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
            
            def on_entry_leave(event, ent=entry):
                if ent.focus_get() != ent:
                    ent.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
            
            def on_entry_focus_in(event, ent=entry):
                ent.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
            
            def on_entry_focus_out(event, ent=entry):
                ent.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
            
            entry.bind("<Enter>", on_entry_enter)
            entry.bind("<Leave>", on_entry_leave)
            entry.bind("<FocusIn>", on_entry_focus_in)
            entry.bind("<FocusOut>", on_entry_focus_out)

            if var_key in ["ID", "OD", "TH"]:
                entry.configure(validate='key', validatecommand=(form.register(validate_integer), '%P'))

            if var_key in ["Type", "Brand", "Name"]:
                def on_focus_out(event, var=vars[var_key]):
                    force_uppercase(var)
                entry.bind("<FocusOut>", on_focus_out)

            entry_widgets[var_key] = entry

        # Quantity field
        qty_frame = ctk.CTkFrame(fields_section, fg_color="transparent")
        qty_frame.pack(fill="x", pady=8)
        qty_frame.grid_columnconfigure(1, weight=1)
        
        qty_label = ctk.CTkLabel(
            qty_frame,
            text="Quantity:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            width=80,
            anchor="w"
        )
        qty_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        quantity_entry = ctk.CTkEntry(
            qty_frame,
            textvariable=vars["Quantity"],
            font=("Poppins", 13),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            validate='key',
            validatecommand=(form.register(validate_integer), '%P')
        )
        quantity_entry.grid(row=0, column=1, sticky="ew")
        entry_widgets["Quantity"] = quantity_entry

        # Add hover effects for quantity entry
        def on_qty_enter(event):
            if quantity_entry.focus_get() != quantity_entry:
                quantity_entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
        
        def on_qty_leave(event):
            if quantity_entry.focus_get() != quantity_entry:
                quantity_entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        def on_qty_focus_in(event):
            quantity_entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
        
        def on_qty_focus_out(event):
            quantity_entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        quantity_entry.bind("<Enter>", on_qty_enter)
        quantity_entry.bind("<Leave>", on_qty_leave)
        quantity_entry.bind("<FocusIn>", on_qty_focus_in)
        quantity_entry.bind("<FocusOut>", on_qty_focus_out)

        # Price field
        price_frame = ctk.CTkFrame(fields_section, fg_color="transparent")
        price_frame.pack(fill="x", pady=8)
        price_frame.grid_columnconfigure(1, weight=1)
        
        price_label = ctk.CTkLabel(
            price_frame,
            textvariable=price_label_var,
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            width=80,
            anchor="w"
        )
        price_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        price_entry = ctk.CTkEntry(
            price_frame,
            textvariable=vars["Price"],
            font=("Poppins", 13),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            validate='key',
            validatecommand=(form.register(validate_float_price), '%P')
        )
        price_entry.grid(row=0, column=1, sticky="ew")
        entry_widgets["Price"] = price_entry

        # Add hover effects for price entry
        def on_price_enter(event):
            if price_entry.focus_get() != price_entry:
                price_entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
        
        def on_price_leave(event):
            if price_entry.focus_get() != price_entry:
                price_entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        def on_price_focus_in(event):
            price_entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
        
        def on_price_focus_out(event):
            price_entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        price_entry.bind("<Enter>", on_price_enter)
        price_entry.bind("<Leave>", on_price_leave)
        price_entry.bind("<FocusIn>", on_price_focus_in)
        price_entry.bind("<FocusOut>", on_price_focus_out)

        # Stock field
        stock_frame = ctk.CTkFrame(fields_section, fg_color="transparent")
        stock_frame.pack(fill="x", pady=8)
        stock_frame.grid_columnconfigure(1, weight=1)
        
        stock_label = ctk.CTkLabel(
            stock_frame,
            text="Stock:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            width=80,
            anchor="w"
        )
        stock_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        stock_entry = ctk.CTkEntry(
            stock_frame,
            textvariable=vars["Stock"],
            font=("Poppins", 13),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            validate='key',
            validatecommand=(form.register(validate_integer), '%P')
        )
        stock_entry.grid(row=0, column=1, sticky="ew")
        entry_widgets["Stock"] = stock_entry

        # Add hover effects for stock entry
        def on_stock_enter(event):
            if stock_entry.focus_get() != stock_entry:
                stock_entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
        
        def on_stock_leave(event):
            if stock_entry.focus_get() != stock_entry:
                stock_entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        def on_stock_focus_in(event):
            stock_entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
        
        def on_stock_focus_out(event):
            stock_entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        stock_entry.bind("<Enter>", on_stock_enter)
        stock_entry.bind("<Leave>", on_stock_leave)
        stock_entry.bind("<FocusIn>", on_stock_focus_in)
        stock_entry.bind("<FocusOut>", on_stock_focus_out)

        # Fabrication-specific fields
        fab_section = ctk.CTkFrame(inner_container, fg_color="#374151", corner_radius=25)
        fab_section.pack(fill="x", pady=(0, 20))
        
        fab_inner = ctk.CTkFrame(fab_section, fg_color="transparent")
        fab_inner.pack(fill="x", padx=20, pady=15)
        
        fab_label = ctk.CTkLabel(
            fab_inner,
            text="Fabrication Details:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF"
        )
        fab_label.pack(pady=(0, 10))

        # Qty Restock field
        qty_restock_frame = ctk.CTkFrame(fab_inner, fg_color="transparent")
        qty_restock_frame.pack(fill="x", pady=5)
        qty_restock_frame.grid_columnconfigure(1, weight=1)
        
        qty_restock_label = ctk.CTkLabel(
            qty_restock_frame,
            text="Qty Restock:",
            font=("Poppins", 13, "bold"),
            text_color="#FFFFFF",
            width=100,
            anchor="w"
        )
        qty_restock_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        qty_restock_entry = ctk.CTkEntry(
            qty_restock_frame,
            textvariable=qty_restock_var,
            font=("Poppins", 13),
            fg_color="#2b2b2b",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            validate='key',
            validatecommand=(form.register(validate_integer), '%P')
        )
        qty_restock_entry.grid(row=0, column=1, sticky="ew")

        # Qty Customer field
        qty_customer_frame = ctk.CTkFrame(fab_inner, fg_color="transparent")
        qty_customer_frame.pack(fill="x", pady=5)
        qty_customer_frame.grid_columnconfigure(1, weight=1)
        
        qty_customer_label = ctk.CTkLabel(
            qty_customer_frame,
            text="Qty Sold:",
            font=("Poppins", 13, "bold"),
            text_color="#FFFFFF",
            width=100,
            anchor="w"
        )
        qty_customer_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        qty_customer_entry = ctk.CTkEntry(
            qty_customer_frame,
            textvariable=qty_customer_var,
            font=("Poppins", 13),
            fg_color="#2b2b2b",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            validate='key',
            validatecommand=(form.register(validate_integer), '%P')
        )
        qty_customer_entry.grid(row=0, column=1, sticky="ew")

        # Stock Left field
        stock_left_frame = ctk.CTkFrame(fab_inner, fg_color="transparent")
        stock_left_frame.pack(fill="x", pady=5)
        stock_left_frame.grid_columnconfigure(1, weight=1)
        
        stock_left_label_text = ctk.CTkLabel(
            stock_left_frame,
            text="Stock Left:",
            font=("Poppins", 13, "bold"),
            text_color="#FFFFFF",
            width=100,
            anchor="w"
        )
        stock_left_label_text.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        stock_left_label = ctk.CTkLabel(
            stock_left_frame,
            textvariable=stock_left_var,
            font=("Poppins", 13),
            text_color="#FFFFFF",
            fg_color="#2b2b2b",
            corner_radius=20,
            height=35,
            anchor="w"
        )
        stock_left_label.grid(row=0, column=1, sticky="ew", padx=(0, 5))

        def on_stock_left_var_changed(*args):
            if stock_left_var.get() == "Error: Negative!":
                stock_left_label.configure(text_color="#EF4444")
            else:
                stock_left_label.configure(text_color="#FFFFFF")

        stock_left_var.trace_add("write", on_stock_left_var_changed)

        # Initialize the form
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

        # Button container
        button_container = ctk.CTkFrame(inner_container, fg_color="transparent")
        button_container.pack(pady=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            font=("Poppins", 16, "bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=45,
            command=form.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # Save button
        save_btn = ctk.CTkButton(
            button_container,
            text="Save",
            font=("Poppins", 16, "bold"),
            fg_color="#22C55E",
            hover_color="#16A34A",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=45,
            command=save
        )
        save_btn.pack(side="right")
        
        # Key bindings
        form.bind("<Return>", save)

        # IMPORTANT FIX: Center window and show it properly to prevent flashing
        form.update_idletasks()
        w = form.winfo_reqwidth()
        h = form.winfo_reqheight()
        center_window(form, w, h)
        
        # Now make the window visible
        form.deiconify()
        
        form.focus_force()
        form.lift()