import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from theme import theme
from ..admin.trans_aed import TransactionLogic, center_window
from ..database import connect_db


class TransactionFormHandler:
    """Handles all GUI-related functionality for transaction forms"""

    def __init__(self, parent_frame, treeview, on_refresh_callback=None, controller=None):
        self.parent_frame = parent_frame
        self.tran_tree = treeview
        self.on_refresh_callback = on_refresh_callback
        self.controller = controller
        self.logic = TransactionLogic()
        self.last_transaction_keys = None  # Store keys for prefill

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
            # If this rowid is in fabrication_records (provided by parent tab), open combined edit form
            parent_tab = getattr(self.parent_frame, '_transaction_tab_ref', None)
            fabrication_set = set()
            if parent_tab is not None:
                fabrication_set = getattr(parent_tab, 'fabrication_records', set())

            if rowid in fabrication_set and parent_tab is not None:
                # Try to locate the paired records from the parent tab's pairs map
                pairs = getattr(parent_tab, 'fabrication_pairs', {}) or {}
                pair = pairs.get(rowid)
                if pair:
                    restock_rec, sale_rec = pair
                    # Pass both records to the form for editing; rowid argument will be a tuple of both
                    self._transaction_form("Edit", record=None, rowid=(restock_rec.rowid, sale_rec.rowid), fabrication_pair=(restock_rec, sale_rec))
                    return
                # Fall back to single-record edit if pair not found

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
        # Update main window title to reflect the action being performed
        if self.controller:
            self.controller.set_window_title(action="DELETE TRANSACTION")
        
        parent_window = self.parent_frame.winfo_toplevel()
        confirm_window = ctk.CTkToplevel(parent_window)
        confirm_window.title("MOS Inventory")
        confirm_window.geometry("400x200")
        confirm_window.resizable(False, False)
        confirm_window.configure(fg_color=theme.get("bg"))

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

        main_frame = ctk.CTkFrame(confirm_window, fg_color=theme.get("card"), corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        question_label = ctk.CTkLabel(
            main_frame,
            text=f"Delete selected {len(items)} transaction(s)?",
            font=("Poppins", 16, "bold"),
            text_color=theme.get("text")
        )
        question_label.pack(pady=(30, 40))

        button_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_container.pack(pady=(0, 20))

        def confirm_delete():
            # Expand selected items to include fabrication partners if present
            expanded = set()
            parent_tab = getattr(self.parent_frame, '_transaction_tab_ref', None)
            pairs = getattr(parent_tab, 'fabrication_pairs', {}) if parent_tab is not None else {}
            for it in items:
                try:
                    rid = int(it)
                except Exception:
                    try:
                        rid = int(str(it))
                    except Exception:
                        rid = it
                expanded.add(rid)
                partner = pairs.get(rid)
                if partner:
                    # partner can be tuple of records
                    try:
                        a, b = partner
                        expanded.add(a.rowid)
                        expanded.add(b.rowid)
                    except Exception:
                        pass
            if self.logic.delete_transactions(list(expanded)):
                if self.on_refresh_callback:
                    self.on_refresh_callback()
            confirm_window.destroy()

        def cancel_delete():
            confirm_window.destroy()

        cancel_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            font=("Poppins", 14, "bold"),
            fg_color=theme.get("accent_hover"),
            hover_color=theme.get("accent"),
            text_color=theme.get("text"),
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
            text_color=theme.get("text"),
            corner_radius=25,
            width=100,
            height=40,
            command=confirm_delete
        )
        confirm_btn.pack(side="right")

        confirm_window.bind('<Escape>', lambda e: cancel_delete())
        confirm_window.bind('<Return>', lambda e: confirm_delete())
        confirm_window.focus()

    def setup_auto_uppercase(self, text_var):
        """Attach a trace to text_var to auto convert input to uppercase in real time."""
        def on_change(*args):
            value = text_var.get()
            upper_val = value.upper()
            if value != upper_val:
                text_var.set(upper_val)
        text_var.trace_add('write', on_change)

    def _transaction_form(self, mode, record=None, rowid=None, fabrication_pair=None):
        """Create and display transaction form"""
        form = ctk.CTkToplevel(self.parent_frame.winfo_toplevel())
        form.title("MOS Inventory")
        
        # Update main window title to reflect the action being performed
        if self.controller:
            if mode == "add":
                self.controller.set_window_title(action="ADD TRANSACTION")
            elif mode == "edit":
                self.controller.set_window_title(action="EDIT TRANSACTION")

        form.withdraw()
        form.resizable(False, False)
        form.configure(fg_color=theme.get("bg"))
        form.transient(self.parent_frame.winfo_toplevel())
        form.grab_set()

        # Reset per-form widget references for conditional show/hide
        self.field_frames = {}
        self.fab_section = None
        self.first_entry = None  # Initialize first entry reference

        # Main containers
        container = ctk.CTkFrame(form, fg_color=theme.get("card"), corner_radius=40)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        inner_container = ctk.CTkFrame(container, fg_color="transparent")
        inner_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Title
        title_label = ctk.CTkLabel(
            inner_container,
            text=f"{mode} Transaction",
            font=("Poppins", 20, "bold"),
            text_color=theme.get("heading_fg")
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

        # Prefill unique product keys if adding and we have saved keys
        if mode == "Add" and self.last_transaction_keys:
            for key in ["Type", "ID", "OD", "TH", "Brand"]:
                if key in self.last_transaction_keys:
                    vars[key].set(self.last_transaction_keys[key])

        # Set up Escape key to close the form
        def on_escape_press(event=None):
            form.destroy()
            
        form.bind("<Escape>", on_escape_press)

        # Set up Ctrl+Tab for cycling through transaction types
        def cycle_transaction_type(event=None):
            current_type = transaction_type_var.get()
            type_order = ["Sale", "Actual", "Fabrication", "Restock"]
            
            try:
                current_index = type_order.index(current_type)
                next_index = (current_index + 1) % len(type_order)
                next_type = type_order[next_index]
                self.select_transaction_type(next_type)
            except ValueError:
                # If current type is not found, default to first type
                self.select_transaction_type("Sale")
            
            # Prevent default Tab behavior
            return "break"
        
        # Bind Ctrl+Tab to cycle transaction types
        form.bind("<Control-Tab>", cycle_transaction_type)
        
        # Also bind Ctrl+Shift+Tab for reverse cycling (optional)
        def reverse_cycle_transaction_type(event=None):
            current_type = transaction_type_var.get()
            type_order = ["Sale", "Actual", "Fabrication", "Restock"]
            
            try:
                current_index = type_order.index(current_type)
                prev_index = (current_index - 1) % len(type_order)
                prev_type = type_order[prev_index]
                self.select_transaction_type(prev_type)
            except ValueError:
                # If current type is not found, default to last type
                self.select_transaction_type("Restock")
            
            # Prevent default Tab behavior
            return "break"
        
        form.bind("<Control-Shift-Tab>", reverse_cycle_transaction_type)

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
        if mode == "Edit":
            if fabrication_pair and isinstance(fabrication_pair, tuple):
                # fabrication_pair is (restock_rec, sale_rec)
                restock_rec, sale_rec = fabrication_pair
                # Populate base fields from restock
                vars["Type"].set(restock_rec.type.upper())
                vars["ID"].set(restock_rec.id_size)
                vars["OD"].set(restock_rec.od_size)
                vars["TH"].set(restock_rec.th_size)
                vars["Brand"].set((restock_rec.brand or "").upper())
                vars["Name"].set((restock_rec.name or "").upper())
                # Date (use restock date)
                try:
                    date_var.set(datetime.strptime(restock_rec.date, "%Y-%m-%d").strftime("%m/%d/%y"))
                except Exception:
                    date_var.set(restock_rec.date)
                # Set fabrication fields
                transaction_type_var.set("Fabrication")
                qty_restock_var.set(str(restock_rec.quantity))
                qty_customer_var.set(str(abs(sale_rec.quantity)))
                vars["Price"].set(f"{sale_rec.price:.2f}" if sale_rec.price is not None else "")
            elif record:
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
        
        # Auto-focus on the first entry field (date field) after everything is set up
        def _safe_focus(w):
            try:
                if w and getattr(w, 'winfo_exists', lambda: False)() and w.winfo_exists():
                    w.focus_set()
            except Exception:
                pass

        # Primary attempt shortly after showing the form
        form.after(50, lambda: _safe_focus(self.first_entry) if self.first_entry else None)
        # Secondary attempt after idle in case the window activation from other dialogs
        # prevented immediate focus; this covers cases where we open this form from
        # another dialog that was just destroyed.
        form.after_idle(lambda: _safe_focus(self.first_entry) if self.first_entry else None)

        form.focus_force()
        form.lift()

    def _create_transaction_type_section(self, parent, transaction_type_var, price_label_var):
        """Create transaction type selection section"""
        type_section = ctk.CTkFrame(parent, fg_color=theme.get("input"), corner_radius=25)
        type_section.pack(fill="x", pady=(0, 20))

        type_inner = ctk.CTkFrame(type_section, fg_color="transparent")
        type_inner.pack(fill="x", padx=20, pady=15)

        type_label = ctk.CTkLabel(
            type_inner,
            text="Transaction Type:",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        type_label.pack(pady=(0, 10))

        # Single horizontal container for all type buttons
        btn_container = ctk.CTkFrame(type_inner, fg_color="transparent")
        btn_container.pack()

        # Store buttons for later access
        self.type_buttons = {}

        def select_transaction_type(value):
            transaction_type_var.set(value)

            # Reset all buttons
            for btn in self.type_buttons.values():
                btn.configure(fg_color=theme.get("accent"), hover_color=theme.get("accent_hover"))

            # Highlight selected button and set price label
            if value == "Restock":
                self.type_buttons["restock"].configure(fg_color="#3B82F6", hover_color="#2563EB")
                price_label_var.set("Cost:")
            elif value == "Sale":
                self.type_buttons["sale"].configure(fg_color="#EF4444", hover_color="#DC2626")
                price_label_var.set("Price:")
            elif value == "Actual":
                self.type_buttons["actual"].configure(fg_color="#22C55E", hover_color="#16A34A")
                price_label_var.set("Cost:")
            elif value == "Fabrication":
                self.type_buttons["fabrication"].configure(fg_color=theme.get("accent_hover"), hover_color=theme.get("accent"))
                price_label_var.set("Price:")

        # Create buttons
        self.type_buttons["restock"] = ctk.CTkButton(
            btn_container,
            text="Restock",
            font=("Poppins", 14, "bold"),
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            corner_radius=25,
            width=120,
            height=40,
            command=lambda: select_transaction_type("Restock")
        )
        self.type_buttons["restock"].pack(side="left", padx=(0, 10))

        self.type_buttons["sale"] = ctk.CTkButton(
            btn_container,
            text="Sale",
            font=("Poppins", 14, "bold"),
            fg_color="#EF4444",  # Start with Sale selected
            hover_color="#DC2626",
            text_color=theme.get("text"),
            corner_radius=25,
            width=120,
            height=40,
            command=lambda: select_transaction_type("Sale")
        )
        self.type_buttons["sale"].pack(side="left", padx=(0, 10))

        self.type_buttons["actual"] = ctk.CTkButton(
            btn_container,
            text="Actual",
            font=("Poppins", 14, "bold"),
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            corner_radius=25,
            width=120,
            height=40,
            command=lambda: select_transaction_type("Actual")
        )
        self.type_buttons["actual"].pack(side="left", padx=(0, 10))

        self.type_buttons["fabrication"] = ctk.CTkButton(
            btn_container,
            text="Fabrication",
            font=("Poppins", 14, "bold"),
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
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

        # Text fields (create Type first)
        entry_widgets = {}
        text_fields = [
            ("Type", "Type")
        ]

        for label_text, var_key in text_fields:
            entry = self._create_text_field(fields_section, label_text, vars[var_key], form)
            entry_widgets[var_key] = entry

            # Auto uppercase for Type
            if label_text in ["Type"]:
                self.setup_auto_uppercase(vars[var_key])

        # Number fields for ID, OD, TH
        number_fields = [
            ("ID", "ID"), ("OD", "OD"), ("TH", "TH")
        ]

        for label_text, var_key in number_fields:
            entry = self._create_number_field(fields_section, label_text, vars[var_key], form, "measurement")
            entry_widgets[var_key] = entry

        # Brand field (after TH)
        brand_entry = self._create_text_field(fields_section, "Brand", vars["Brand"], form)
        entry_widgets["Brand"] = brand_entry
        # Auto uppercase for Brand
        self.setup_auto_uppercase(vars["Brand"])

        # Place Date field after TH so it's the next field users type into
        # and set it as the first_entry so the form will focus it immediately.
        self.first_entry = self._create_date_field(fields_section, date_var)

        # Now create the Name field (after Date)
        entry = self._create_text_field(fields_section, "Name", vars["Name"], form)
        entry_widgets["Name"] = entry
        # Auto uppercase for Name
        self.setup_auto_uppercase(vars["Name"])

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
        """Create date picker field with manual entry capability and no default date"""
        date_frame = ctk.CTkFrame(parent, fg_color="transparent")
        date_frame.pack(fill="x", pady=8)
        date_frame.grid_columnconfigure(1, weight=1)
        
        date_label = ctk.CTkLabel(
            date_frame,
            text="Date:",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text"),
            width=80,
            anchor="w"
        )
        date_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # Use a regular CTkEntry instead of DateEntry for better typing experience
        date_entry = ctk.CTkEntry(
            date_frame,
            textvariable=date_var,
            font=("Poppins", 13),
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=35,
            border_width=1,
            border_color=theme.get("border"),
            placeholder_text="mm/dd/yy"
        )
        date_entry.grid(row=0, column=1, sticky="ew")
        
        # Add hover and focus effects
        self._add_entry_effects(date_entry)
        
        # Validate date format as user types
        def validate_date_format(new_val):
            if new_val == "":
                return True
            # Allow partial typing: 1, 12, 12/, 12/3, 12/31, 12/31/, 12/31/2, 12/31/23
            if re.match(r'^\d{0,2}(/\d{0,2}(/\d{0,2})?)?$', new_val):
                return True
            return False
        
        vcmd = (parent.register(validate_date_format), '%P')
        date_entry.configure(validate='key', validatecommand=vcmd)
        
        return date_entry

    def _create_text_field(self, parent, label_text, text_var, form):
        """Create text input field"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", pady=8)
        field_frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(
            field_frame,
            text=f"{label_text}:",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text"),
            width=80,
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        entry = ctk.CTkEntry(
            field_frame,
            textvariable=text_var,
            font=("Poppins", 13),
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=35,
            border_width=1,
            border_color=theme.get("border")
        )
        
        # Add validation for Type and Brand to prevent spaces
        if label_text in ["Type", "Brand"]:
            def validate_no_spaces(new_val):
                return ' ' not in new_val
            
            vcmd = (parent.register(validate_no_spaces), '%P')
            entry.configure(validate='key', validatecommand=vcmd)
        
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
            text_color=theme.get("text"),
            width=80,
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        validate_func = self._validate_integer if field_type == "integer" else (self._validate_measurement if field_type == "measurement" else self._validate_float_price)
        
        entry = ctk.CTkEntry(
            field_frame,
            textvariable=text_var,
            font=("Poppins", 13),
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=35,
            border_width=1,
            border_color=theme.get("border"),
            validate='key',
            validatecommand=(form.register(validate_func), '%P')
        )
        entry.grid(row=0, column=1, sticky="ew")
        
        self._add_entry_effects(entry)
        # Register this field frame for conditional show/hide
        try:
            if not hasattr(self, 'field_frames'):
                self.field_frames = {}
            self.field_frames[label_text] = field_frame
        except Exception:
            pass
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

            # Helpers to show/hide field rows without leaving gaps
            def hide_field_row(name):
                frame = self.field_frames.get(name)
                if frame is not None:
                    try:
                        frame.pack_forget()
                    except Exception:
                        pass

            def show_field_row(name):
                frame = self.field_frames.get(name)
                if frame is not None and frame.winfo_manager() == "":
                    try:
                        frame.pack(fill="x", pady=8)
                    except Exception:
                        pass

            def hide_fabrication_section():
                if getattr(self, 'fab_section', None) is not None:
                    try:
                        self.fab_section.pack_forget()
                    except Exception:
                        pass

            def show_fabrication_section():
                if getattr(self, 'fab_section', None) is not None and self.fab_section.winfo_manager() == "":
                    try:
                        self.fab_section.pack(fill="x", pady=(0, 20))
                    except Exception:
                        pass

            if trans_type in ["Restock", "Sale"]:
                enable_disable([entry_widgets["Quantity"]], True)
                enable_disable([entry_widgets["Price"]], True)
                enable_disable([entry_widgets["Stock"]], False)
                enable_disable([self.qty_restock_entry, self.qty_customer_entry], False)

                # Show only Quantity and Price; hide Stock and Fabrication
                hide_field_row("Stock")
                hide_fabrication_section()
                show_field_row("Quantity")
                show_field_row("Price")
            elif trans_type == "Actual":
                enable_disable([entry_widgets["Quantity"]], False)
                enable_disable([entry_widgets["Price"]], True)
                enable_disable([entry_widgets["Stock"]], True)
                enable_disable([self.qty_restock_entry, self.qty_customer_entry], False)

                # Show only Stock; hide Quantity, Price and Fabrication
                hide_field_row("Quantity")
                show_field_row("Price")
                hide_fabrication_section()
                show_field_row("Stock")
            elif trans_type == "Fabrication":
                enable_disable([entry_widgets["Quantity"]], False)
                enable_disable([entry_widgets["Price"]], True)
                enable_disable([entry_widgets["Stock"]], False)
                enable_disable([self.qty_restock_entry, self.qty_customer_entry], True)

                # Show Price and Fabrication section; hide Quantity and Stock
                hide_field_row("Quantity")
                hide_field_row("Stock")
                show_field_row("Price")
                show_fabrication_section()

            # Auto-resize and re-center the window to fit visible content
            try:
                form.update_idletasks()
                w = form.winfo_reqwidth()
                h = form.winfo_reqheight()
                center_window(form, w, h)
            except Exception:
                pass

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
            try:
                vars["Price"].set(f"{float(record.price):.2f}" if record.price is not None else "")
            except Exception:
                vars["Price"].set("")
        elif record.is_restock == 0 and record.quantity < 0:
            type_str = "Sale"
            vars["Quantity"].set(str(abs(record.quantity)))
            try:
                vars["Price"].set(f"{float(record.price):.2f}" if record.price is not None else "")
            except Exception:
                vars["Price"].set("")
        elif record.is_restock == 2:
            type_str = "Actual"
            vars["Stock"].set(str(record.quantity))
            try:
                if record.price is not None:
                    vars["Price"].set(f"{float(record.price):.2f}")
                else:
                    vars["Price"].set("")
            except Exception:
                vars["Price"].set("")
        elif record.is_restock == 3:
                # This shouldn't happen in normal editing since fabrication creates two separate records
                # But if it does, handle it gracefully
                type_str = "Fabrication"
                vars["Price"].set("")  # Always start empty for fabrication editing
                vars["Quantity"].set("")
                qty_restock_var.set("")
                qty_customer_var.set("")
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
            fg_color=theme.get("accent_hover"),
            hover_color=theme.get("accent"),
            text_color=theme.get("text"),
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
            text_color=theme.get("text"),
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
            
            # Validate date format first
            try:
                date_str = date_var.get()
                datetime.strptime(date_str, "%m/%d/%y")
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter a valid date in MM/DD/YY format", parent=form)
                return

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
            
            # CRITICAL FIX: Detect if THIS IS A TYPE CONVERSION
            # If editing and transaction type changed, we need to handle properly
            is_type_conversion = False
            was_fabrication = isinstance(rowid, (list, tuple)) and len(rowid) == 2 if mode == "Edit" else False
            is_becoming_fabrication = trans_type == "Fabrication"
            
            # Handle all transaction type scenarios
            if trans_type == "Fabrication":
                data = self.logic.prepare_transaction_data(trans_type, form_data)
                if not data:
                    messagebox.showerror("Invalid", "Error preparing data for saving.", parent=form)
                    return
                
                if mode == "Add":
                    # Adding new fabrication: create two records
                    success = self.logic.save_fabrication_transaction(data)
                elif was_fabrication:
                    # CASE: Staying Fabrication (already a pair) - update both
                    try:
                        restock_rid, sale_rid = rowid
                        try:
                            norm_date = datetime.strptime(form_data['date'], "%m/%d/%y").strftime("%Y-%m-%d")
                        except Exception:
                            norm_date = form_data['date']
                        restock_payload = {
                            'date': norm_date,
                            'item_type': form_data['item_type'],
                            'id_size': form_data['id_size'],
                            'od_size': form_data['od_size'],
                            'th_size': form_data['th_size'],
                            'brand': form_data['brand'],
                            'name': form_data['name'],
                            'quantity': int(form_data['qty_restock']),
                            'price': None,
                            'is_restock': 1
                        }
                        sale_payload = {
                            'date': norm_date,
                            'item_type': form_data['item_type'],
                            'id_size': form_data['id_size'],
                            'od_size': form_data['od_size'],
                            'th_size': form_data['th_size'],
                            'brand': form_data['brand'],
                            'name': form_data['name'],
                            'quantity': -int(form_data['qty_customer']),
                            'price': float(form_data['price']),
                            'is_restock': 0
                        }
                        ok1 = self.logic.save_transaction("Edit", restock_payload, restock_rid)
                        ok2 = self.logic.save_transaction("Edit", sale_payload, sale_rid)
                        success = bool(ok1 and ok2)
                    except Exception:
                        success = False
                else:
                    # CASE: Converting FROM non-Fabrication TO Fabrication
                    # Delete old single record and create new fabrication pair
                    try:
                        if isinstance(rowid, int):
                            # Delete the old non-fabrication record
                            conn = connect_db()
                            cur = conn.cursor()
                            cur.execute("DELETE FROM transactions WHERE rowid=?", (rowid,))
                            conn.commit()
                            conn.close()
                        # Create new fabrication pair
                        success = self.logic.save_fabrication_transaction(data)
                    except Exception:
                        success = False
            else:
                # Non-Fabrication type (Sale, Restock, or Actual)
                data = self.logic.prepare_transaction_data(trans_type, form_data)
                if not data:
                    messagebox.showerror("Invalid", "Error preparing data for saving.", parent=form)
                    return
                
                if was_fabrication:
                    # CASE: Converting FROM Fabrication TO non-Fabrication
                    # Keep the restock record (first in pair), delete the sale record (second)
                    # Update the kept record with new data
                    try:
                        restock_rid, sale_rid = rowid
                        # Delete the sale record
                        conn = connect_db()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM transactions WHERE rowid=?", (sale_rid,))
                        conn.commit()
                        conn.close()
                        # Update the restock record with new transaction data
                        success = self.logic.save_transaction("Edit", data, restock_rid)
                    except Exception:
                        success = False
                else:
                    # CASE: Staying non-Fabrication - just update normally
                    success = self.logic.save_transaction(mode, data, rowid)
            
            if success:
                # Save last keys for prefill (only on successful save)
                self.last_transaction_keys = {
                    'Type': form_data['item_type'].strip().upper(),
                    'ID': form_data['id_size'].strip(),
                    'OD': form_data['od_size'].strip(),
                    'TH': form_data['th_size'].strip(),
                    'Brand': form_data['brand'].strip().upper(),
                    'Name': form_data['name'].strip().upper(),
                }
                
                if self.on_refresh_callback:
                    self.on_refresh_callback()
                # After successful save, open the Transaction Window for the affected product
                try:
                    # Build basic details from form data
                    # IMPORTANT: Use canonicalized brand (what's in DB) not form input
                    from ..admin.brand_utils import canonicalize_brand
                    canonical_brand, _ = canonicalize_brand(form_data['brand'].strip().upper())
                    
                    details = {
                        'type': form_data['item_type'].strip().upper(),
                        'id': form_data['id_size'].strip(),
                        'od': form_data['od_size'].strip(),
                        'th': form_data['th_size'].strip(),
                        'brand': canonical_brand,  # Use canonicalized brand for lookup
                        'price': 0.0,
                        'part_no': '',
                        'country_of_origin': '',
                        'notes': ''
                    }
                    # Try to fetch product metadata from products table
                    try:
                        conn = connect_db()
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT part_no, country_of_origin, notes, price FROM products WHERE type=? AND id=? AND od=? AND th=? AND brand=? LIMIT 1",
                            (details['type'], details['id'], details['od'], details['th'], details['brand'])
                        )
                        row = cur.fetchone()
                        conn.close()
                        if row:
                            details['part_no'] = row[0] or ''
                            details['country_of_origin'] = row[1] or ''
                            details['notes'] = row[2] or ''
                            try:
                                details['price'] = float(row[3]) if row[3] is not None else 0.0
                            except Exception:
                                details['price'] = 0.0
                    except Exception:
                        pass

                    # Obtain controller and main_app from parent_frame reference if available
                    controller = None
                    main_app = None
                    try:
                        tab_ref = getattr(self.parent_frame, '_transaction_tab_ref', None)
                        if tab_ref:
                            controller = getattr(tab_ref, 'controller', None)
                            main_app = getattr(tab_ref, 'main_app', None)
                    except Exception:
                        controller = None

                    if controller:
                        controller.show_transaction_window(details, main_app)
                except Exception:
                    # Fallback: just close the form
                    pass
                try:
                    form.destroy()
                except Exception:
                    pass
            else:
                messagebox.showerror("Error", "Failed to save transaction.", parent=form)
                
        except Exception as e:
            messagebox.showerror("Invalid", f"Check all fields\n{e}", parent=form)

    def _add_entry_effects(self, entry):
        """Add hover and focus effects to entry widget"""
        def on_entry_enter(event, ent=entry):
            if ent.focus_get() != ent:
                ent.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("accent"))
        
        def on_entry_leave(event, ent=entry):
            if ent.focus_get() != ent:
                ent.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))
        
        def on_entry_focus_in(event, ent=entry):
            ent.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("input_focus"))
        
        def on_entry_focus_out(event, ent=entry):
            ent.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))
        
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

    def _validate_measurement(self, new_val):
        """Validate measurement input (numbers, decimals, slashes)"""
        if new_val == "":
            return True
        # Allow digits, dots, slashes
        if all(c in '0123456789./' for c in new_val):
            # Check structure: parts separated by / should be valid numbers
            parts = new_val.split('/')
            for part in parts:
                if part and not self._is_valid_number(part):
                    return False
            return True
        return False

    def _is_valid_number(self, s):
        """Check if string is a valid number (int or float)"""
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _validate_integer(self, new_val):
        """Validate integer input"""
        if new_val == "":
            return True
        return new_val.isdigit()

    def _validate_float_price(self, new_val):
        """Validate float input for price"""
        if new_val == "":
            return True
        # Reject spaces
        if ' ' in new_val:
            return False
        try:
            float(new_val)
            if new_val.count(".") > 1:
                return False
            return True
        except ValueError:
            return False

    def _create_fabrication_section(self, parent, qty_restock_var, qty_customer_var, stock_left_var, form):
        """Create fabrication details section"""
        fab_section = ctk.CTkFrame(parent, fg_color=theme.get("input"), corner_radius=25)
        fab_section.pack(fill="x", pady=(0, 20))
        
        fab_inner = ctk.CTkFrame(fab_section, fg_color="transparent")
        fab_inner.pack(fill="x", padx=20, pady=15)
        
        fab_label = ctk.CTkLabel(
            fab_inner,
            text="Fabrication Details:",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
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
            text_color=theme.get("text"),
            width=100,
            anchor="w"
        )
        qty_restock_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        self.qty_restock_entry = ctk.CTkEntry(
            qty_restock_frame,
            textvariable=qty_restock_var,
            font=("Poppins", 13),
            fg_color=theme.get("card"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=35,
            border_width=1,
            border_color=theme.get("border"),
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
            text_color=theme.get("text"),
            width=100,
            anchor="w"
        )
        qty_customer_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        self.qty_customer_entry = ctk.CTkEntry(
            qty_customer_frame,
            textvariable=qty_customer_var,
            font=("Poppins", 13),
            fg_color=theme.get("card"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=35,
            border_width=1,
            border_color=theme.get("border"),
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
            text_color=theme.get("text"),
            width=100,
            anchor="w"
        )
        stock_left_label_text.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        self.stock_left_label = ctk.CTkLabel(
            stock_left_frame,
            textvariable=stock_left_var,
            font=("Poppins", 13),
            text_color=theme.get("text"),
            fg_color=theme.get("card"),
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
                self.stock_left_label.configure(text_color=theme.get("text"))

        qty_restock_var.trace_add("write", update_stock_left)
        qty_customer_var.trace_add("write", update_stock_left)

        # Register fabrication section for conditional show/hide
        self.fab_section = fab_section