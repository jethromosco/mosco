import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
from ..admin.trans_aed import TransactionLogic, center_window
import re


class TransactionFormHandler:
    """Handles all GUI-related functionality for transaction forms"""
    
    def __init__(self, parent_frame, treeview, on_refresh_callback=None):
        self.parent_frame = parent_frame
        self.tran_tree = treeview
        self.on_refresh_callback = on_refresh_callback
        self.logic = TransactionLogic()


    def add_transaction(self):
        """Open form to add a new transaction"""
        self._transaction_form("Add")


    def edit_transaction(self):
        """Open form to edit selected transaction"""
        item = self.tran_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a transaction to edit", 
                                          parent=self.parent_frame.winfo_toplevel())

        try:
            rowid = int(item)
            record = self.logic.get_record_by_id(rowid)
            if record is None:
                messagebox.showerror("Error", "Selected record not found.", 
                                     parent=self.parent_frame.winfo_toplevel())
                return
            self._transaction_form("Edit", record, rowid)
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Could not retrieve transaction details.", 
                                 parent=self.parent_frame.winfo_toplevel())


    def delete_transaction(self):
        """Delete selected transaction(s) with confirmation"""
        items = self.tran_tree.selection()
        if not items:
            return messagebox.showwarning("Select", "Select transaction(s) to delete", 
                                          parent=self.parent_frame.winfo_toplevel())

        self._show_delete_confirmation(items)


    def _show_delete_confirmation(self, items):
        """Show delete confirmation dialog"""
        parent_window = self.parent_frame.winfo_toplevel()
        confirm_window = ctk.CTkToplevel(parent_window)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x200")
        confirm_window.resizable(False, False)
        confirm_window.configure(fg_color="#000000")
        
        confirm_window.transient(parent_window)
        confirm_window.grab_set()
        
        # Center the confirmation window
        confirm_window.update_idletasks()
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        x = parent_x + (parent_width - 400) // 2
        y = parent_y + (parent_height - 200) // 2
        confirm_window.geometry(f"400x200+{x}+{y}")
        
        main_frame = ctk.CTkFrame(confirm_window, fg_color="#2b2b2b", corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        question_label = ctk.CTkLabel(
            main_frame,
            text=f"Delete selected {len(items)} transaction(s)?",
            font=("Poppins", 16, "bold"),
            text_color="#FFFFFF"
        )
        question_label.pack(pady=(30, 40))
        
        button_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_container.pack(pady=(0, 20))
        
        def confirm_delete():
            if self.logic.delete_transactions(items):
                if self.on_refresh_callback:
                    self.on_refresh_callback()
            confirm_window.destroy()
        
        def cancel_delete():
            confirm_window.destroy()
        
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
        
        confirm_window.bind('<Escape>', lambda e: cancel_delete())
        confirm_window.bind('<Return>', lambda e: confirm_delete())
        confirm_window.focus()


    def _transaction_form(self, mode, record=None, rowid=None):
        """Create and display transaction form"""
        form = ctk.CTkToplevel(self.parent_frame.winfo_toplevel())
        form.title(f"{mode} Transaction")
        
        form.withdraw()
        form.resizable(False, False)
        form.configure(fg_color="#000000")
        form.transient(self.parent_frame.winfo_toplevel())
        form.grab_set()
        form.bind("<Escape>", lambda e: form.destroy())

        # Main containers
        container = ctk.CTkFrame(form, fg_color="#2b2b2b", corner_radius=40)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        inner_container = ctk.CTkFrame(container, fg_color="transparent")
        inner_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Title
        title_label = ctk.CTkLabel(
            inner_container,
            text=f"{mode} Transaction",
            font=("Poppins", 20, "bold"),
            text_color="#D00000"
        )
        title_label.pack(pady=(0, 20))

        # Initialize variables
        vars = {key: tk.StringVar() for key in self.logic.FIELDS}
        date_var = tk.StringVar()
        transaction_type_var = tk.StringVar(value="Sale")
        qty_restock_var = tk.StringVar()
        qty_customer_var = tk.StringVar()
        stock_left_var = tk.StringVar()
        price_label_var = tk.StringVar(value="Price:")

        # Create form sections
        self._create_transaction_type_section(inner_container, transaction_type_var, price_label_var)
        entry_widgets = self._create_fields_section(inner_container, vars, date_var, form, price_label_var)
        self._create_fabrication_section(inner_container, qty_restock_var, qty_customer_var, 
                                         stock_left_var, form)
        
        # Set up transaction type behavior
        self._setup_transaction_type_behavior(transaction_type_var, entry_widgets, 
                                              qty_restock_var, qty_customer_var, 
                                              stock_left_var, form)
        
        # Populate form for editing
        if mode == "Edit" and record:
            self._populate_edit_form(vars, date_var, transaction_type_var, 
                                    qty_restock_var, qty_customer_var, record)
        
        # Create buttons
        self._create_form_buttons(inner_container, form, mode, vars, date_var, 
                                  transaction_type_var, qty_restock_var, qty_customer_var, rowid)
        
        # Show form
        form.update_idletasks()
        w = form.winfo_reqwidth()
        h = form.winfo_reqheight()
        center_window(form, w, h)
        form.deiconify()
        form.focus_force()
        form.lift()


    def _create_transaction_type_section(self, parent, transaction_type_var, price_label_var):
        """Create transaction type selection section"""
        type_section = ctk.CTkFrame(parent, fg_color="#374151", corner_radius=25)
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

        top_btn_container = ctk.CTkFrame(type_inner, fg_color="transparent")
        top_btn_container.pack(pady=(0, 10))
        
        bottom_btn_container = ctk.CTkFrame(type_inner, fg_color="transparent")
        bottom_btn_container.pack()

        # Store buttons for later access
        self.type_buttons = {}

        def select_transaction_type(value):
            transaction_type_var.set(value)
            
            # Reset all buttons
            for btn in self.type_buttons.values():
                btn.configure(fg_color="#4B5563", hover_color="#6B7280")

            # Highlight selected button and set price label
            if value == "Restock":
                self.type_buttons["restock"].configure(fg_color="#3B82F6", hover_color="#2563EB")
                price_label_var.set("Cost:")
            elif value == "Sale":
                self.type_buttons["sale"].configure(fg_color="#EF4444", hover_color="#DC2626")
                price_label_var.set("Price:")
            elif value == "Actual":
                self.type_buttons["actual"].configure(fg_color="#22C55E", hover_color="#16A34A")
                price_label_var.set("Price:")
            elif value == "Fabrication":
                self.type_buttons["fabrication"].configure(fg_color="#6B7280", hover_color="#4B5563")
                price_label_var.set("Price:")

        # Create buttons
        self.type_buttons["restock"] = ctk.CTkButton(
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
        self.type_buttons["restock"].pack(side="left", padx=(0, 10))
        
        self.type_buttons["sale"] = ctk.CTkButton(
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
        self.type_buttons["sale"].pack(side="left")
        
        self.type_buttons["actual"] = ctk.CTkButton(
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
        self.type_buttons["actual"].pack(side="left", padx=(0, 10))
        
        self.type_buttons["fabrication"] = ctk.CTkButton(
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
        self.type_buttons["fabrication"].pack(side="left")

        self.select_transaction_type = select_transaction_type


    def _create_fields_section(self, parent, vars, date_var, form, price_label_var):
        """Create main fields section"""
        fields_section = ctk.CTkFrame(parent, fg_color="transparent")
        fields_section.pack(fill="x", pady=(0, 20))

        # Date field
        self._create_date_field(fields_section, date_var)
        
        # Text fields
        fields = [
            ("Type", "Type"), ("ID", "ID"), ("OD", "OD"), ("TH", "TH"),
            ("Brand", "Brand"), ("Name", "Name")
        ]

        entry_widgets = {}
        for label_text, var_key in fields:
            entry = self._create_text_field(fields_section, label_text, vars[var_key], form)
            entry_widgets[var_key] = entry

        # Quantity, Price, Stock fields
        entry_widgets["Quantity"] = self._create_number_field(fields_section, "Quantity", 
                                                               vars["Quantity"], form, "integer")
        entry_widgets["Price"] = self._create_number_field(fields_section, "Price", 
                                                            vars["Price"], form, "float", 
                                                            label_var=price_label_var)
        entry_widgets["Stock"] = self._create_number_field(fields_section, "Stock", 
                                                            vars["Stock"], form, "integer")

        return entry_widgets


    def _create_date_field(self, parent, date_var):
        """Create date picker field"""
        date_frame = ctk.CTkFrame(parent, fg_color="transparent")
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


    def _create_text_field(self, parent, label_text, text_var, form):
        """Create text input field"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", pady=8)
        field_frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(
            field_frame,
            text=f"{label_text}:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            width=80,
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        entry = ctk.CTkEntry(
            field_frame,
            textvariable=text_var,
            font=("Poppins", 13),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563"
        )
        entry.grid(row=0, column=1, sticky="ew")
        
        # Add hover and focus effects
        self._add_entry_effects(entry)
        
        # Add uppercase conversion for text fields
        if label_text in ["Type", "Brand", "Name"]:
            def on_focus_out(event, var=text_var):
                self._force_uppercase(var)
            entry.bind("<FocusOut>", on_focus_out)
        
        return entry


    def _create_number_field(self, parent, label_text, text_var, form, field_type, label_var=None):
        """Create number input field"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", pady=8)
        field_frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(
            field_frame,
            textvariable=label_var if label_var else None,
            text=f"{label_text}:" if not label_var else None,
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF",
            width=80,
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        validate_func = self._validate_integer if field_type == "integer" else self._validate_float_price
        
        entry = ctk.CTkEntry(
            field_frame,
            textvariable=text_var,
            font=("Poppins", 13),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            validate='key',
            validatecommand=(form.register(validate_func), '%P')
        )
        entry.grid(row=0, column=1, sticky="ew")
        
        self._add_entry_effects(entry)
        return entry


    def _setup_transaction_type_behavior(self, transaction_type_var, entry_widgets, 
                                         qty_restock_var, qty_customer_var, stock_left_var, form):
        """Setup behavior for different transaction types"""
        def on_type_change(*args):
            trans_type = transaction_type_var.get()
            self.select_transaction_type(trans_type)
            
            def enable_disable(widgets, enable):
                state = "normal" if enable else "disabled"
                for w in widgets:
                    if hasattr(w, 'configure'):
                        w.configure(state=state)

            if trans_type in ["Restock", "Sale"]:
                enable_disable([entry_widgets["Quantity"]], True)
                enable_disable([entry_widgets["Price"]], True)
                enable_disable([entry_widgets["Stock"]], False)
                enable_disable([self.qty_restock_entry, self.qty_customer_entry], False)
            elif trans_type == "Actual":
                enable_disable([entry_widgets["Quantity"]], False)
                enable_disable([entry_widgets["Price"]], False)
                enable_disable([entry_widgets["Stock"]], True)
                enable_disable([self.qty_restock_entry, self.qty_customer_entry], False)
            elif trans_type == "Fabrication":
                enable_disable([entry_widgets["Quantity"]], False)
                enable_disable([entry_widgets["Price"]], True)
                enable_disable([entry_widgets["Stock"]], False)
                enable_disable([self.qty_restock_entry, self.qty_customer_entry], True)

        transaction_type_var.trace_add("write", on_type_change)
        on_type_change()  # Initial setup


    def _populate_edit_form(self, vars, date_var, transaction_type_var, 
                            qty_restock_var, qty_customer_var, record):
        """Populate form fields when editing - using the same logic as old working code"""
        # Set basic fields
        vars["Type"].set(record.type.upper())
        vars["ID"].set(record.id_size)
        vars["OD"].set(record.od_size)
        vars["TH"].set(record.th_size)
        vars["Brand"].set(record.brand.upper())
        vars["Name"].set(record.name.upper())
        
        # Set date
        date_var.set(datetime.strptime(record.date, "%Y-%m-%d").strftime("%m/%d/%y"))
        
        # Determine transaction type and set appropriate fields
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
        else:
            type_str = "Sale"
        
        transaction_type_var.set(type_str)


    def _create_form_buttons(self, parent, form, mode, vars, date_var, 
                             transaction_type_var, qty_restock_var, qty_customer_var, rowid):
        """Create form action buttons"""
        button_container = ctk.CTkFrame(parent, fg_color="transparent")
        button_container.pack(pady=10)
        
        def save_transaction(event=None):
            self._save_transaction(form, mode, vars, date_var, transaction_type_var, 
                                   qty_restock_var, qty_customer_var, rowid)
        
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
            command=save_transaction
        )
        save_btn.pack(side="right")
        
        form.bind("<Return>", save_transaction)


    def _save_transaction(self, form, mode, vars, date_var, transaction_type_var, 
                          qty_restock_var, qty_customer_var, rowid):
        """Handle transaction saving - using the same logic as old working code"""
        try:
            trans_type = transaction_type_var.get()
            
            form_data = {
                'date': date_var.get(),
                'item_type': vars["Type"].get(),
                'id_size': vars["ID"].get(),
                'od_size': vars["OD"].get(),
                'th_size': vars["TH"].get(),
                'brand': vars["Brand"].get(),
                'name': vars["Name"].get(),
                'quantity': vars["Quantity"].get(),
                'price': vars["Price"].get(),
                'stock': vars["Stock"].get(),
                'qty_restock': qty_restock_var.get(),
                'qty_customer': qty_customer_var.get()
            }
            
            # Validate form data
            errors = self.logic.validate_transaction_data(trans_type, form_data)
            if errors:
                messagebox.showerror("Invalid", "\n".join(errors), parent=form)
                return
            
            # Check product exists
            if not self.logic.validate_product_exists(
                form_data['item_type'].strip().upper(),
                form_data['id_size'].strip(),
                form_data['od_size'].strip(),
                form_data['th_size'].strip(),
                form_data['brand'].strip().upper()
            ):
                messagebox.showerror("Product Not Found", "This product does not exist. Please add it first.", parent=form)
                return
            
            # Handle Fabrication differently (same as old code)
            if trans_type == "Fabrication":
                data = self.logic.prepare_transaction_data(trans_type, form_data)
                if not data:
                    messagebox.showerror("Invalid", "Error preparing data for saving.", parent=form)
                    return
                success = self.logic.save_fabrication_transaction(data)
            else:
                # Prepare data for saving
                data = self.logic.prepare_transaction_data(trans_type, form_data)
                if not data:
                    messagebox.showerror("Invalid", "Error preparing data for saving.", parent=form)
                    return
                success = self.logic.save_transaction(mode, data, rowid)
            
            if success:
                if self.on_refresh_callback:
                    self.on_refresh_callback()
                form.destroy()
            else:
                messagebox.showerror("Error", "Failed to save transaction.", parent=form)
                
        except Exception as e:
            messagebox.showerror("Invalid", f"Check all fields\n{e}", parent=form)


    def _add_entry_effects(self, entry):
        """Add hover and focus effects to entry widget"""
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


    def _force_uppercase(self, var):
        """Force text variable to uppercase"""
        text = var.get()
        upper_text = text.upper()
        if text != upper_text:
            var.set(upper_text)


    def _validate_integer(self, new_val):
        """Validate integer input"""
        if new_val == "":
            return True
        return new_val.isdigit()


    def _validate_float_price(self, new_val):
        """Validate float input for price"""
        if new_val == "":
            return True
        try:
            float(new_val)
            if new_val.count(".") > 1:
                return False
            return True
        except ValueError:
            return False


    def _create_fabrication_section(self, parent, qty_restock_var, qty_customer_var, stock_left_var, form):
        """Create fabrication details section"""
        fab_section = ctk.CTkFrame(parent, fg_color="#374151", corner_radius=25)
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
        
        self.qty_restock_entry = ctk.CTkEntry(
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
            validatecommand=(form.register(self._validate_integer), '%P')
        )
        self.qty_restock_entry.grid(row=0, column=1, sticky="ew")

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
        
        self.qty_customer_entry = ctk.CTkEntry(
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
            validatecommand=(form.register(self._validate_integer), '%P')
        )
        self.qty_customer_entry.grid(row=0, column=1, sticky="ew")

        # Stock Left display
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
        
        self.stock_left_label = ctk.CTkLabel(
            stock_left_frame,
            textvariable=stock_left_var,
            font=("Poppins", 13),
            text_color="#FFFFFF",
            fg_color="#2b2b2b",
            corner_radius=20,
            height=35,
            anchor="w"
        )
        self.stock_left_label.grid(row=0, column=1, sticky="ew", padx=(0, 5))

        # Set up stock calculation
        def update_stock_left(*args):
            try:
                restock_qty = int(qty_restock_var.get()) if qty_restock_var.get() else 0
            except:
                restock_qty = 0
            try:
                sold_qty = int(qty_customer_var.get()) if qty_customer_var.get() else 0
            except:
                sold_qty = 0

            stock_left = restock_qty - sold_qty
            if stock_left < 0:
                stock_left_var.set("Error: Negative!")
                self.stock_left_label.configure(text_color="#EF4444")
            else:
                stock_left_var.set(str(stock_left))
                self.stock_left_label.configure(text_color="#FFFFFF")

        qty_restock_var.trace_add("write", update_stock_left)
        qty_customer_var.trace_add("write", update_stock_left)