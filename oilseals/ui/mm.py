import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from ..database import connect_db
from .transaction_window import TransactionWindow
from ..admin.products import AdminPanel

LOW_STOCK_THRESHOLD = 5
OUT_OF_STOCK = 0


class InventoryApp(ctk.CTkFrame):
    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="#000000")
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

        self.inch_labels = {}  # ID/OD/TH inch conversion labels
        self.entry_widgets = {}  # Store entry widgets for key binding

        self.create_widgets()
        self.refresh_product_list()
        self.root.bind("<Escape>", lambda e: self.clear_filters())
        self.root.bind("<Return>", lambda e: self.remove_focus())

    # --- Auto-capitalize key event handler ---
    def on_key_press(self, event, field_type):
        """Handle key press events for auto-capitalization"""
        if event.char.isalpha():
            # Convert to uppercase
            event.widget.insert(tk.INSERT, event.char.upper())
            # Trigger refresh for search
            self.root.after_idle(self.refresh_product_list)
            return "break"  # Prevent default behavior
        return None  # Allow default behavior for non-alphabetic keys

    # --- Utility ---
    def get_var(self, key):
        return self.search_vars[key].get().strip()

    def parse_number(self, val):
        try:
            return float(val)
        except Exception:
            return 0

    def format_display_value(self, value):
        value = str(value).strip()
        if "/" in value:
            return value
        try:
            num = float(value)
            return str(int(num)) if num.is_integer() else str(num)
        except ValueError:
            return value

    # --- UI Creation ---
    def create_widgets(self):
        self.bind("<Button-1>", self.remove_focus)

        # === Header ===
        header_frame = ctk.CTkFrame(self, fg_color="#000000", height=120)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)

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
            command=lambda: self.controller.go_back(self.return_to) if self.controller else self.master.destroy()
        )
        back_btn.pack(side="left", anchor="w", pady=35, padx=40)

        # === Search Section ===
        search_frame = ctk.CTkFrame(self, fg_color="transparent", height=140)
        search_frame.pack(fill="x", padx=40, pady=(20, 10))
        search_frame.pack_propagate(False)

        entries_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        entries_container.pack(expand=True, pady=20)

        search_fields = [
            ("TYPE", "type"),
            ("ID", "id"),
            ("OD", "od"),
            ("TH", "th"),
            ("Brand", "brand"),
            ("Part No.", "part_no")
        ]

        # FIXED: Shared hover/focus handlers with RED outline on hover
        def on_entry_enter(event, entry):
            if entry.focus_get() != entry:
                # RED outline on hover (not focused)
                entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")

        def on_entry_leave(event, entry):
            if entry.focus_get() != entry:
                # Back to normal when not hovered and not focused
                entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

        def on_entry_focus_in(event, entry):
            # RED outline when focused (clicked)
            entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")

        def on_entry_focus_out(event, entry):
            # Back to normal when focus is lost
            entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

        for idx, (display_name, key) in enumerate(search_fields):
            field_frame = ctk.CTkFrame(entries_container, fg_color="transparent", height=90)
            field_frame.grid(row=0, column=idx, padx=20, sticky="nsew")
            entries_container.grid_columnconfigure(idx, weight=1)
            field_frame.grid_propagate(False)

            # Label
            label = ctk.CTkLabel(field_frame, text=display_name,
                                 font=("Poppins", 16, "bold"),
                                 text_color="#FFFFFF")
            label.grid(row=0, column=0, pady=(0, 5), sticky="w")

            # Entry
            var = self.search_vars[key]
            entry = ctk.CTkEntry(
                field_frame,
                textvariable=var,
                width=140,
                height=32,
                fg_color="#374151",
                text_color="#FFFFFF",
                font=("Poppins", 12),
                corner_radius=40,
                border_width=1,
                border_color="#4B5563",
                placeholder_text=f"Enter {display_name}"
            )
            entry.grid(row=1, column=0, pady=(0, 5), sticky="we")

            entry.bind("<Enter>", lambda e, ent=entry: on_entry_enter(e, ent))
            entry.bind("<Leave>", lambda e, ent=entry: on_entry_leave(e, ent))
            entry.bind("<FocusIn>", lambda e, ent=entry: on_entry_focus_in(e, ent))
            entry.bind("<FocusOut>", lambda e, ent=entry: on_entry_focus_out(e, ent))
            
            # Store entry widget and bind key events for auto-capitalization
            self.entry_widgets[key] = entry
            
            # Bind key events for auto-capitalization (only for type, brand, part_no)
            if key in ["type", "brand", "part_no"]:
                entry.bind("<KeyPress>", lambda e, field=key: self.on_key_press(e, field))
            
            # Bind change events for search refresh (all fields)
            var.trace_add("write", lambda *args: self.refresh_product_list())

            # Inch conversion label
            if key in ["id", "od", "th"]:
                inch_label = ctk.CTkLabel(
                    field_frame,
                    text="",   # start empty
                    font=("Poppins", 11),
                    text_color="#FFFFFF"
                )
                inch_label.grid(row=2, column=0, pady=(2, 0), sticky="w")
                self.inch_labels[key] = inch_label

                self.update_inch_label(key)
                var.trace_add("write", lambda *args, k=key: self.update_inch_label(k))

        # === Sort / Filter Section ===
        search_filter_frame = ctk.CTkFrame(self, fg_color="transparent", height=70)
        search_filter_frame.pack(fill="x", padx=40, pady=(10, 20))
        search_filter_frame.pack_propagate(False)

        search_filter_container = ctk.CTkFrame(search_filter_frame, fg_color="transparent")
        search_filter_container.pack(expand=True, pady=15)

        sort_label = ctk.CTkLabel(search_filter_container, text="Sort by",
                                  font=("Poppins", 14, "bold"),
                                  text_color="#FFFFFF")
        sort_label.pack(side="left", padx=(0, 10))

        sort_combo = ctk.CTkComboBox(
            search_filter_container,
            variable=self.sort_by,
            values=["Size", "Quantity"],
            state="readonly",
            width=120,
            height=32,
            fg_color="#374151",
            button_color="#374151",
            button_hover_color="#4B5563",
            text_color="#FFFFFF",
            font=("Poppins", 12),
            corner_radius=40
        )
        sort_combo.pack(side="left", padx=10)
        self.sort_by.trace_add("write", lambda *args: self.refresh_product_list())

        stock_label = ctk.CTkLabel(search_filter_container, text="Stock Filter",
                                   font=("Poppins", 14, "bold"),
                                   text_color="#FFFFFF")
        stock_label.pack(side="left", padx=(40, 10))

        stock_combo = ctk.CTkComboBox(
            search_filter_container,
            variable=self.stock_filter,
            values=["All", "In Stock", "Low Stock", "Out of Stock"],
            state="readonly",
            width=120,
            height=32,
            fg_color="#374151",
            button_color="#374151",
            button_hover_color="#4B5563",
            text_color="#FFFFFF",
            font=("Poppins", 12),
            corner_radius=40
        )
        stock_combo.pack(side="left", padx=10)
        self.stock_filter.trace_add("write", lambda *args: self.refresh_product_list())

        # === Table ===
        table_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=40)
        table_container.pack(fill="both", expand=True, padx=20, pady=0)

        table_inner = ctk.CTkFrame(table_container, fg_color="#2b2b2b", corner_radius=40)
        table_inner.pack(fill="both", expand=True, padx=0, pady=0)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background="#2b2b2b",
                        foreground="#FFFFFF",
                        fieldbackground="#2b2b2b",
                        font=("Poppins", 11),
                        rowheight=40)
        style.configure("Custom.Treeview.Heading",
                        background="#000000",
                        foreground="#D00000",
                        font=("Poppins", 11, "bold"))
        style.map("Custom.Treeview", background=[("selected", "#2b2b2b")])
        style.map("Custom.Treeview.Heading", background=[("active", "#111111")])

        columns = ("type", "size", "brand", "part_no", "origin", "notes", "qty", "price")
        self.tree = ttk.Treeview(table_inner, columns=columns, show="headings", style="Custom.Treeview")

        self.tree.tag_configure("low", background="#8B4513", foreground="#FFFFFF")
        self.tree.tag_configure("out", background="#8B0000", foreground="#FFFFFF")
        self.tree.tag_configure("normal", background="#2b2b2b", foreground="#FFFFFF")

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

        tree_scrollbar = ttk.Scrollbar(table_inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        tree_scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.tree.bind("<<TreeviewSelect>>", lambda e: self.tree.selection_remove(self.tree.selection()))
        self.tree.bind("<Double-1>", self.open_transaction_page)

        # === Bottom Bar ===
        bottom_frame = ctk.CTkFrame(self, fg_color="#000000", height=60)
        bottom_frame.pack(fill="x", padx=20, pady=(10, 20))
        bottom_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(bottom_frame, text="",
                                         font=("Poppins", 14),
                                         text_color="#CCCCCC")
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

    # --- Helpers ---
    def remove_focus(self, event=None):
        self.focus()

    def update_inch_label(self, key):
        raw_value = self.get_var(key).replace("mm", "").strip()
        if not raw_value:
            self.inch_labels[key].configure(text="", text_color="#FFFFFF")
            return

        def mm_to_inches(mm):
            return mm * 0.0393701

        try:
            parts = raw_value.split("/")
            inches_list = []
            for part in parts:
                if not part.strip():
                    continue
                mm = float(part.strip())
                inches = mm_to_inches(mm)
                inches_list.append(f"{inches:.3f}")
            converted = "/".join(inches_list)
            self.inch_labels[key].configure(text=f'{converted}"', text_color="#FFFFFF")
        except ValueError:
            self.inch_labels[key].configure(text="⚠ Invalid input", text_color="#FF4444")

    def create_password_window(self, callback=None):
        """Create a custom password window that matches the app's design"""
        # Create the password window
        password_window = ctk.CTkToplevel(self.root)
        password_window.title("Admin Access")
        password_window.geometry("450x350")
        password_window.resizable(False, False)
        password_window.configure(fg_color="#000000")
        
        # Center the window on parent
        password_window.transient(self.root)
        password_window.grab_set()
        
        # Center positioning
        password_window.update_idletasks()
        parent_x = self.root.winfo_rootx()
        parent_y = self.root.winfo_rooty()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        x = parent_x + (parent_width - 450) // 2
        y = parent_y + (parent_height - 350) // 2
        password_window.geometry(f"450x350+{x}+{y}")
        
        # Main container frame - matching your app's style
        main_frame = ctk.CTkFrame(
            password_window, 
            fg_color="#000000",
            corner_radius=0
        )
        main_frame.pack(fill="both", expand=True)
        
        # Content frame with rounded corners like your search section
        content_frame = ctk.CTkFrame(
            main_frame,
            fg_color="#2b2b2b",
            corner_radius=40,
            border_width=1,
            border_color="#4B5563"
        )
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title - matching your header style
        title_label = ctk.CTkLabel(
            content_frame,
            text="Admin Access",
            font=("Poppins", 28, "bold"),
            text_color="#D00000"
        )
        title_label.pack(pady=(40, 20))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            content_frame,
            text="Enter admin password to continue",
            font=("Poppins", 16),
            text_color="#FFFFFF"
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Password entry container - matching your search field style
        entry_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        entry_container.pack(pady=(0, 30))
        
        # Password label
        password_label = ctk.CTkLabel(
            entry_container,
            text="Password",
            font=("Poppins", 16, "bold"),
            text_color="#FFFFFF"
        )
        password_label.pack(pady=(0, 10))
        
        # Password entry - matching your search entry style
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
        
        # FIXED: Entry hover/focus effects with RED outline on hover
        def on_entry_enter(event):
            if password_entry.focus_get() != password_entry:
                password_entry.configure(border_color="#D00000", fg_color="#4B5563")
        
        def on_entry_leave(event):
            if password_entry.focus_get() != password_entry:
                password_entry.configure(border_color="#4B5563", fg_color="#374151")
        
        def on_entry_focus_in(event):
            password_entry.configure(border_color="#D00000", fg_color="#1F2937")
        
        def on_entry_focus_out(event):
            password_entry.configure(border_color="#4B5563", fg_color="#374151")
        
        password_entry.bind("<Enter>", on_entry_enter)
        password_entry.bind("<Leave>", on_entry_leave)
        password_entry.bind("<FocusIn>", on_entry_focus_in)
        password_entry.bind("<FocusOut>", on_entry_focus_out)
        
        # Error label
        error_label = ctk.CTkLabel(
            entry_container,
            text="",
            font=("Poppins", 12),
            text_color="#FF4444"
        )
        error_label.pack()
        
        # Button container
        button_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_container.pack(pady=(20, 30))
        
        # Cancel button - matching your back button style but gray
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
            command=lambda: self.close_password_window(password_window, callback, False)
        )
        cancel_btn.pack(side="left", padx=(0, 20))
        
        # Submit button - matching your admin button style
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
            command=lambda: self.check_password(password_entry, error_label, password_window, callback)
        )
        submit_btn.pack(side="right", padx=(20, 0))
        
        # Key bindings
        password_window.bind('<Return>', lambda e: self.check_password(password_entry, error_label, password_window, callback))
        password_window.bind('<Escape>', lambda e: self.close_password_window(password_window, callback, False))
        
        # Focus on password entry
        password_entry.focus()
        
        return password_window
    
    def check_password(self, entry, error_label, window, callback):
        """Check if the entered password is correct"""
        password = entry.get().strip()
        
        if password == "1":  # Your current password
            self.close_password_window(window, callback, True)
        else:
            # Show error message
            error_label.configure(text="❌ Incorrect password. Please try again.")
            entry.delete(0, tk.END)
            entry.focus()
            
            # Clear error message after 3 seconds
            window.after(3000, lambda: error_label.configure(text=""))
    
    def close_password_window(self, window, callback, success):
        """Close the password window and execute callback"""
        window.destroy()
        if callback:
            callback(success)

    def open_admin_panel(self, return_to=None):
        """Open admin panel with custom password window"""
        def on_password_result(success):
            if success:
                current_frame_name = self.controller.get_current_frame_name()
                current_frame = self.controller.frames[current_frame_name]
                AdminPanel(self.controller.root, current_frame, self.controller, on_close_callback=self.refresh_product_list)
        
        # Create and show custom password window
        self.create_password_window(callback=on_password_result)

    def clear_filters(self):
        for var in self.search_vars.values():
            var.set("")
        self.sort_by.set("Size")
        self.stock_filter.set("All")
        self.refresh_product_list()

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

        self.tree.delete(*self.tree.get_children())

        with connect_db() as conn:
            cur = conn.cursor()

            # Build the base query
            query = """SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price 
                        FROM products WHERE 1=1"""
            params = []
            
            # Add search filters - using UPPER for case-insensitive search
            for key, var in self.search_vars.items():
                val = self.get_var(key)
                if val:
                    if key == 'brand':
                        col = 'brand'
                    elif key == 'part_no':
                        col = 'part_no'
                    else:
                        col = key
                    
                    # Use UPPER for case-insensitive prefix matching
                    query += f" AND UPPER({col}) LIKE UPPER(?)"
                    params.append(f"{val}%")

            cur.execute(query, params)
            products = cur.fetchall()

            # Get transactions for stock calculation
            cur.execute("""SELECT type, id_size, od_size, th_size, quantity, is_restock 
                         FROM transactions ORDER BY date ASC""")
            all_transactions = cur.fetchall()

            # Calculate stock levels
            stock_map = {}
            for row in all_transactions:
                type_, id_raw, od_raw, th_raw, quantity, is_restock = row
                key = (type_, id_raw, od_raw, th_raw)

                if is_restock == 2:
                    stock_map[key] = quantity
                else:
                    stock_map[key] = stock_map.get(key, 0) + quantity

        # Process products for display
        display_data = []
        for row in products:
            type_, id_raw, od_raw, th_raw, brand, part_no, origin, notes, price = row
            qty = stock_map.get((type_, id_raw, od_raw, th_raw), 0)
            
            # Apply stock filter
            if not self.stock_filter_matches(qty):
                continue

            id_num = self.parse_number(id_raw)
            od_num = self.parse_number(od_raw)
            th_num = self.parse_number(th_raw)

            size_str = f"{self.format_display_value(id_raw)}×{self.format_display_value(od_raw)}×{self.format_display_value(th_raw)}"
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

        # Sort the data
        if self.sort_by.get() == "Size":
            display_data.sort(
                key=lambda x: (
                    self.parse_number(x[8]),
                    self.parse_number(x[9]),
                    parse_thickness_sort(x[10])
                )
            )
        elif self.sort_by.get() == "Quantity":
            display_data.sort(key=lambda x: x[6], reverse=True)

        # Insert data into tree
        for item in display_data:
            qty = item[6]
            if qty == OUT_OF_STOCK:
                tag = "out"
            elif qty <= LOW_STOCK_THRESHOLD:
                tag = "low"
            else:
                tag = "normal"

            self.tree.insert("", tk.END, values=item[:8], tags=(tag,))

        self.status_label.configure(text=f"Total products: {len(display_data)}")

    def open_transaction_page(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            print("DEBUG: No row under mouse")
            return

        self.tree.selection_set(item_id)
        item = self.tree.item(item_id)["values"]
        if not item:
            return

        try:
            size_str = item[1].replace("×", "-").replace("x", "-")
            parts = size_str.split("-")
            # store as strings, not floats
            id_, od, th = [p.strip() for p in parts]
        except Exception as e:
            print(f"DEBUG: Could not parse size from {item[1]} → {e}")
            return

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