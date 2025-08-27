import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from ..ui.mm import (
    convert_mm_to_inches_display,
    build_products_display_data,
    validate_admin_password,
    create_product_details,
    get_stock_tag,
    should_uppercase_field,
)
from .gui_transaction_window import TransactionWindow
from .gui_products import AdminPanel


class InventoryApp(ctk.CTkFrame):
    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="#000000")
        self.controller = controller
        self.root = controller.root if controller else self.winfo_toplevel()

        self.root.title("Oil Seal Inventory Manager")
        self.root.attributes("-fullscreen", True)

        # Initialize variables
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

        # UI components
        self.inch_labels = {}
        self.entry_widgets = {}

        # Setup UI and bindings
        self.create_widgets()
        self.refresh_product_list()
        self._setup_bindings()

    def _setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind("<Escape>", lambda e: self.clear_filters())
        self.root.bind("<Return>", lambda e: self.remove_focus())

    def on_key_press(self, event, field_type):
        """Handle key press events for uppercase fields"""
        if event.char.isalpha() and should_uppercase_field(field_type):
            event.widget.insert(tk.INSERT, event.char.upper())
            self.root.after_idle(self.refresh_product_list)
            return "break"
        return None

    def get_var(self, key):
        """Get trimmed value from search variable"""
        return self.search_vars[key].get().strip()

    def create_widgets(self):
        """Create all UI widgets"""
        self.bind("<Button-1>", self.remove_focus)
        
        # Create main sections
        self._create_header_section()
        self._create_search_section()
        self._create_table_section()
        self._create_bottom_section()

    def _create_header_section(self):
        """Create header with back button"""
        header_frame = ctk.CTkFrame(self, fg_color="#000000", height=120)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back",
            font=("Poppins", 20, "bold"),
            fg_color="#D00000",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            corner_radius=40,
            width=120,
            height=50,
            command=self._handle_back_button
        )
        back_btn.grid(row=0, column=0, sticky="w", padx=(40, 10), pady=35)

    def _handle_back_button(self):
        """Handle back button click"""
        if self.controller:
            self.controller.go_back(self.return_to)
        else:
            self.master.destroy()

    def _create_search_section(self):
        """Create search filters section"""
        search_section = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=40)
        search_section.pack(fill="x", padx=20, pady=(20, 10))

        search_inner = ctk.CTkFrame(search_section, fg_color="transparent")
        search_inner.pack(fill="both", expand=True, padx=20, pady=20)

        main_container = ctk.CTkFrame(search_inner, fg_color="transparent")
        main_container.pack(fill="x", expand=True)

        for i in range(8):
            main_container.grid_columnconfigure(i, weight=1, uniform="fields")

        self._create_search_fields(main_container)
        self._create_sort_controls(main_container)

    def _create_search_fields(self, parent):
        """Create search input fields"""
        search_fields = [
            ("TYPE", "type"),
            ("ID", "id"),
            ("OD", "od"),
            ("TH", "th"),
            ("Brand", "brand"),
            ("Part No.", "part_no")
        ]

        for idx, (display_name, key) in enumerate(search_fields):
            self._create_field_widget(parent, idx, display_name, key)

    def _create_field_widget(self, parent, idx, display_name, key):
        """Create individual field widget with label, entry, and inch conversion"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent", height=130)
        field_frame.grid(row=0, column=idx, padx=5, sticky="ew")
        field_frame.grid_propagate(False)
        field_frame.grid_columnconfigure(0, weight=1)

        # Label
        label = ctk.CTkLabel(
            field_frame, 
            text=display_name,
            font=("Poppins", 18, "bold"),
            text_color="#FFFFFF"
        )
        label.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        # Entry
        var = self.search_vars[key]
        entry = self._create_entry_widget(field_frame, var, display_name, key)
        entry.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        
        self.entry_widgets[key] = entry
        self._setup_entry_bindings(entry, key, var)

        # Inch conversion label for size fields
        if key in ["id", "od", "th"]:
            self._create_inch_label(field_frame, key, var)

    def _create_entry_widget(self, parent, var, display_name, key):
        """Create styled entry widget"""
        entry = ctk.CTkEntry(
            parent,
            textvariable=var,
            width=120,
            height=40,
            fg_color="#374151",
            text_color="#FFFFFF",
            font=("Poppins", 18),
            corner_radius=40,
            border_width=1,
            border_color="#4B5563",
            placeholder_text=f"Enter {display_name}"
        )
        return entry

    def _setup_entry_bindings(self, entry, key, var):
        """Setup entry widget event bindings"""
        # Hover and focus effects
        entry.bind("<Enter>", lambda e: self._on_entry_hover(entry, True))
        entry.bind("<Leave>", lambda e: self._on_entry_hover(entry, False))
        entry.bind("<FocusIn>", lambda e: self._on_entry_focus(entry, True))
        entry.bind("<FocusOut>", lambda e: self._on_entry_focus(entry, False))

        # Uppercase handling for specific fields
        if should_uppercase_field(key):
            entry.bind("<KeyPress>", lambda e: self.on_key_press(e, key))

        # Auto-refresh on changes
        var.trace_add("write", lambda *args: self.refresh_product_list())

    def _on_entry_hover(self, entry, is_enter):
        """Handle entry hover effects"""
        if entry.focus_get() != entry:
            if is_enter:
                entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
            else:
                entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

    def _on_entry_focus(self, entry, has_focus):
        """Handle entry focus effects"""
        if has_focus:
            entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
        else:
            entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

    def _create_inch_label(self, parent, key, var):
        """Create inch conversion label for size fields"""
        inch_label = ctk.CTkLabel(
            parent,
            text="",
            font=("Poppins", 18, "bold"),
            text_color="#FFFFFF"
        )
        inch_label.grid(row=2, column=0, pady=(6, 0), sticky="ew")
        self.inch_labels[key] = inch_label

        # Initialize and setup trace
        self._update_inch_label(key)
        var.trace_add("write", lambda *args, k=key: self._update_inch_label(k))

    def _update_inch_label(self, key: str):
        """Update inch conversion label"""
        text, is_err = convert_mm_to_inches_display(self.get_var(key))
        color = "#FF4444" if is_err else "#FFFFFF"
        self.inch_labels[key].configure(text=text, text_color=color)

    def _create_sort_controls(self, parent):
        """Create sort and filter controls"""
        # Sort control
        sort_frame = ctk.CTkFrame(parent, fg_color="transparent", height=90)
        sort_frame.grid(row=0, column=6, padx=5, sticky="ew")
        sort_frame.grid_propagate(False)
        sort_frame.grid_columnconfigure(0, weight=1)

        sort_label = ctk.CTkLabel(
            sort_frame, 
            text="Sort By",
            font=("Poppins", 18, "bold"),
            text_color="#FFFFFF"
        )
        sort_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

        sort_combo = self._create_combo_widget(
            sort_frame, 
            self.sort_by, 
            ["Size", "Quantity"]
        )
        sort_combo.grid(row=1, column=0, pady=(0, 5), sticky="ew")
        self.sort_by.trace_add("write", lambda *args: self.refresh_product_list())

        # Stock filter control
        stock_frame = ctk.CTkFrame(parent, fg_color="transparent", height=90)
        stock_frame.grid(row=0, column=7, padx=5, sticky="ew")
        stock_frame.grid_propagate(False)
        stock_frame.grid_columnconfigure(0, weight=1)

        stock_label = ctk.CTkLabel(
            stock_frame, 
            text="Stock Filter",
            font=("Poppins", 18, "bold"),
            text_color="#FFFFFF"
        )
        stock_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

        stock_combo = self._create_combo_widget(
            stock_frame, 
            self.stock_filter, 
            ["All", "In Stock", "Low Stock", "Out of Stock"]
        )
        stock_combo.grid(row=1, column=0, pady=(0, 5), sticky="ew")
        self.stock_filter.trace_add("write", lambda *args: self.refresh_product_list())

    def _create_combo_widget(self, parent, variable, values):
        """Create styled combo box widget"""
        combo = ctk.CTkComboBox(
            parent,
            variable=variable,
            values=values,
            state="readonly",
            width=120,
            height=40,
            fg_color="#374151",
            button_color="#374151",
            button_hover_color="#D00000",
            dropdown_hover_color="#4B5563",
            text_color="#FFFFFF",
            font=("Poppins", 18),
            corner_radius=40,
            border_width=1,
            border_color="#4B5563"
        )
        
        combo.bind("<Enter>", lambda e: self._on_combo_hover(combo, True))
        combo.bind("<Leave>", lambda e: self._on_combo_hover(combo, False))
        
        return combo

    def _on_combo_hover(self, combo, is_enter):
        """Handle combo box hover effects"""
        if is_enter:
            combo.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
        else:
            combo.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

    def _create_table_section(self):
        """Create data table section"""
        table_section = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=40)
        table_section.pack(fill="both", expand=True, padx=20, pady=(0, 0))

        table_inner = ctk.CTkFrame(table_section, fg_color="transparent")
        table_inner.pack(fill="both", expand=True, padx=20, pady=20)

        self._setup_treeview_style()
        self._create_treeview(table_inner)

    def _setup_treeview_style(self):
        """Configure treeview styling"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background="#2b2b2b",
                        foreground="#FFFFFF",
                        fieldbackground="#2b2b2b",
                        font=("Poppins", 18),
                        rowheight=40)
        style.configure("Custom.Treeview.Heading",
                        background="#000000",
                        foreground="#D00000",
                        font=("Poppins", 20, "bold"))
        style.map("Custom.Treeview", background=[("selected", "#2b2b2b")])
        style.map("Custom.Treeview.Heading", background=[("active", "#111111")])

    def _create_treeview(self, parent):
        """Create and configure treeview widget"""
        columns = ("type", "size", "brand", "part_no", "origin", "notes", "qty", "price")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", style="Custom.Treeview")
        
        # Configure tags for stock status
        self.tree.tag_configure("low", background="#8B4513", foreground="#FFFFFF")
        self.tree.tag_configure("out", background="#8B0000", foreground="#FFFFFF")
        self.tree.tag_configure("normal", background="#2b2b2b", foreground="#FFFFFF")

        # Configure columns
        display_names = {
            "type": "Type",
            "size": "Size",
            "brand": "Brand",
            "part_no": "Part No.",
            "origin": "Origin",
            "notes": "Notes",
            "qty": "Qty",
            "price": "Price"
        }

        for col in columns:
            self.tree.heading(col, text=display_names[col])
            self.tree.column(col, anchor="center", width=120)

        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # Setup tree bindings
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.tree.selection_remove(self.tree.selection()))
        self.tree.bind("<Double-1>", self.open_transaction_page)

    def _create_bottom_section(self):
        """Create bottom section with status and admin button"""
        bottom_frame = ctk.CTkFrame(self, fg_color="#000000", height=60)
        bottom_frame.pack(fill="x", padx=20, pady=(10, 20))
        bottom_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            bottom_frame, 
            text="",
            font=("Poppins", 18),
            text_color="#CCCCCC"
        )
        self.status_label.pack(side="left", pady=15)

        admin_btn = ctk.CTkButton(
            bottom_frame,
            text="Admin",
            font=("Poppins", 20, "bold"),
            fg_color="#D00000",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            corner_radius=40,
            width=120,
            height=50,
            command=self.open_admin_panel
        )
        admin_btn.pack(side="right", pady=15, padx=40)

    def remove_focus(self, event=None):
        """Remove focus from current widget"""
        self.focus()

    def create_password_window(self, callback=None):
        """Create password input dialog"""
        password_window = ctk.CTkToplevel(self.root)
        password_window.title("Admin Access")
        password_window.geometry("450x350")
        password_window.resizable(False, False)
        password_window.configure(fg_color="#000000")
        password_window.transient(self.root)
        password_window.grab_set()
        
        # Center the window
        self._center_window(password_window, 450, 350)

        # Create password dialog content
        self._create_password_content(password_window, callback)
        
        return password_window

    def _center_window(self, window, width, height):
        """Center window relative to parent"""
        window.update_idletasks()
        parent_x = self.root.winfo_rootx()
        parent_y = self.root.winfo_rooty()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def _create_password_content(self, window, callback):
        """Create password dialog content"""
        main_frame = ctk.CTkFrame(window, fg_color="#000000", corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        content_frame = ctk.CTkFrame(
            main_frame, 
            fg_color="#2b2b2b", 
            corner_radius=40, 
            border_width=1, 
            border_color="#4B5563"
        )
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Title and subtitle
        title_label = ctk.CTkLabel(
            content_frame, 
            text="Admin Access", 
            font=("Poppins", 28, "bold"), 
            text_color="#D00000"
        )
        title_label.pack(pady=(40, 20))
        
        subtitle_label = ctk.CTkLabel(
            content_frame, 
            text="Enter admin password to continue", 
            font=("Poppins", 16), 
            text_color="#FFFFFF"
        )
        subtitle_label.pack(pady=(0, 40))

        # Password entry section
        entry_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        entry_container.pack(pady=(0, 30))
        
        password_label = ctk.CTkLabel(
            entry_container, 
            text="Password", 
            font=("Poppins", 16, "bold"), 
            text_color="#FFFFFF"
        )
        password_label.pack(pady=(0, 10))
        
        password_entry = ctk.CTkEntry(
            entry_container, 
            width=280, 
            height=40, 
            fg_color="#374151", 
            text_color="#FFFFFF", 
            font=("Poppins", 14), 
            corner_radius=40, 
            border_width=2, 
            border_color="#4B5563", 
            placeholder_text="Enter password", 
            show="*"
        )
        password_entry.pack(pady=(0, 10))

        # Setup password entry bindings
        self._setup_password_entry_bindings(password_entry)

        error_label = ctk.CTkLabel(
            entry_container, 
            text="", 
            font=("Poppins", 12), 
            text_color="#FF4444"
        )
        error_label.pack()

        # Buttons
        self._create_password_buttons(content_frame, password_entry, error_label, window, callback)

        # Window bindings
        window.bind('<Return>', lambda e: self.check_password(password_entry, error_label, window, callback))
        window.bind('<Escape>', lambda e: self.close_password_window(window, callback, False))
        
        password_entry.focus()

    def _setup_password_entry_bindings(self, entry):
        """Setup password entry hover and focus effects"""
        def on_enter(event):
            if entry.focus_get() != entry:
                entry.configure(border_color="#D00000", fg_color="#4B5563")
        
        def on_leave(event):
            if entry.focus_get() != entry:
                entry.configure(border_color="#4B5563", fg_color="#374151")
        
        def on_focus_in(event):
            entry.configure(border_color="#D00000", fg_color="#1F2937")
        
        def on_focus_out(event):
            entry.configure(border_color="#4B5563", fg_color="#374151")
        
        entry.bind("<Enter>", on_enter)
        entry.bind("<Leave>", on_leave)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _create_password_buttons(self, parent, password_entry, error_label, window, callback):
        """Create password dialog buttons"""
        button_container = ctk.CTkFrame(parent, fg_color="transparent")
        button_container.pack(pady=(20, 30))
        
        cancel_btn = ctk.CTkButton(
            button_container, 
            text="Cancel", 
            font=("Poppins", 16, "bold"), 
            fg_color="#6B7280", 
            hover_color="#4B5563", 
            text_color="#FFFFFF", 
            corner_radius=40, 
            width=120, 
            height=45, 
            command=lambda: self.close_password_window(window, callback, False)
        )
        cancel_btn.pack(side="left", padx=(0, 20))
        
        submit_btn = ctk.CTkButton(
            button_container, 
            text="Submit", 
            font=("Poppins", 16, "bold"), 
            fg_color="#D00000", 
            hover_color="#B71C1C", 
            text_color="#FFFFFF", 
            corner_radius=40, 
            width=120, 
            height=45, 
            command=lambda: self.check_password(password_entry, error_label, window, callback)
        )
        submit_btn.pack(side="right", padx=(20, 0))

    def check_password(self, entry, error_label, window, callback):
        """Validate password and handle result"""
        password = entry.get().strip()
        if validate_admin_password(password):
            self.close_password_window(window, callback, True)
        else:
            error_label.configure(text="❌ Incorrect password. Please try again.")
            entry.delete(0, tk.END)
            entry.focus()
            window.after(3000, lambda: error_label.configure(text=""))

    def close_password_window(self, window, callback, success):
        """Close password window and execute callback"""
        window.destroy()
        if callback:
            callback(success)

    def open_admin_panel(self, return_to=None):
        """Open admin panel after password validation"""
        def on_password_result(success):
            if success:
                current_frame_name = self.controller.get_current_frame_name()
                current_frame = self.controller.frames[current_frame_name]
                AdminPanel(
                    self.controller.root, 
                    current_frame, 
                    self.controller, 
                    on_close_callback=self.refresh_product_list
                )
        
        self.create_password_window(callback=on_password_result)

    def clear_filters(self):
        """Clear all search filters and reset to defaults"""
        for var in self.search_vars.values():
            var.set("")
        self.sort_by.set("Size")
        self.stock_filter.set("All")
        self.refresh_product_list()

    def refresh_product_list(self, clear_filters=False):
        """Refresh the product display list"""
        if clear_filters:
            self.clear_filters()
            return

        # Clear existing items
        self.tree.delete(*self.tree.get_children())

        # Get filtered data
        filters = {k: v.get().strip() for k, v in self.search_vars.items()}
        display_data = build_products_display_data(filters, self.sort_by.get(), self.stock_filter.get())

        # Populate tree
        for item in display_data:
            qty = item[6]
            tag = get_stock_tag(qty)
            self.tree.insert("", tk.END, values=item[:8], tags=(tag,))

        # Update status
        self.status_label.configure(text=f"Total products: {len(display_data)}")

    def open_transaction_page(self, event):
        """Open transaction window for selected product"""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        
        self.tree.selection_set(item_id)
        item_values = self.tree.item(item_id)["values"]
        if not item_values:
            return

        # Create product details from item values
        details = create_product_details(list(item_values))
        if not details:
            return

        # Open transaction window
        if self.controller:
            self.controller.show_transaction_window(details, self)
        else:
            win = tk.Toplevel(self)
            TransactionWindow(win, details, self)