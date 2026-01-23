import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from PIL import Image
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
from theme import theme
from home_page import ICON_PATH  # Import ICON_PATH for logo images


class InventoryApp(ctk.CTkFrame):
    def __init__(self, master, controller=None):
        super().__init__(master, fg_color=theme.get("bg"))
        self.controller = controller
        self.root = controller.root if controller else self.winfo_toplevel()

        # Default return target for back button
        self.return_to = "HomePage"

        self.root.title("Oil Seal Inventory Manager")
        # Do not force window state here — preserve whatever the user set
        # (main/app_controller should handle initial startup state).
        self._is_fullscreen = False

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
        self.search_label_widgets = []
        self.combo_widgets = []
        self.entry_fields = []  # For Backspace navigation

        # Setup UI and bindings
        self.create_widgets()
        self.refresh_product_list()
        self._setup_bindings()
        theme.subscribe(self.apply_theme)

    def _setup_bindings(self):
        """Setup keyboard bindings"""
        # Keep Escape dedicated to clearing filters (user requested).
        self.root.bind("<Escape>", lambda e: self.clear_filters())
        self.root.bind("<Return>", lambda e: self.remove_focus())
        # Add Ctrl+2 shortcut for admin access
        self.root.bind("<Control-Key-2>", lambda e: self.open_admin_panel())
        # Bind window resize to update button positions
        self.bind("<Configure>", self.on_window_resize)
        # F11 toggles exclusive fullscreen — delegate to controller if available
        if self.controller and hasattr(self.controller, '_toggle_fullscreen'):
            self.root.bind("<F11>", lambda e: self.controller._toggle_fullscreen())
        else:
            self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        # Setup Backspace navigation for search fields
        self._setup_entry_backspace_navigation()

    def _toggle_fullscreen(self, event=None):
        # Fallback local handler that delegates to controller if present.
        if self.controller and hasattr(self.controller, '_toggle_fullscreen'):
            return self.controller._toggle_fullscreen(event)
        try:
            self._is_fullscreen = not getattr(self, "_is_fullscreen", False)
            self.root.attributes("-fullscreen", self._is_fullscreen)
        except Exception:
            pass

    def _exit_fullscreen_or_clear_filters(self, event=None):
        """Deprecated helper (previously handled Escape)."""
        return None

    def on_window_resize(self, event=None):
        """Update absolute positioned elements on window resize"""
        if hasattr(self, 'admin_btn') and self.admin_btn.winfo_exists():
            window_width = self.winfo_width()
            if window_width > 1:
                self.admin_btn.place(x=window_width-140, y=40)  # 100 (button width) + 40 (margin) = 140
        
        # Center the logo
        if hasattr(self, 'logo_frame') and self.logo_frame.winfo_exists():
            window_width = self.winfo_width()
            if window_width > 1:
                logo_width = 540  # 120 + 420 + 5 padding
                center_x = (window_width - logo_width) // 2
                self.logo_frame.place(x=center_x, y=20)

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

    def _create_header_section(self):
        """Create header with back button, logo, and admin button"""
        # ABSOLUTE POSITIONED ELEMENTS - FIXED POSITIONS
        # Back Button - Top Left (same positioning as HomePage/CategoryPage)
        self.back_btn = ctk.CTkButton(
            self,
            text="← Back",
            font=("Poppins", 20, "bold"),
            fg_color=theme.get("primary"),
            hover_color=theme.get("primary_hover"),
            text_color="#FFFFFF",
            corner_radius=40,
            width=120,
            height=50,
            command=self._handle_back_button
        )
        self.back_btn.place(x=40, y=40)

        # Admin Button - Top Right with 40px margin
        self.admin_btn = ctk.CTkButton(
            self,
            text="Admin",
            font=("Poppins", 18, "bold"),
            width=100,
            height=50,
            corner_radius=25,
            fg_color=theme.get("primary"),
            hover_color=theme.get("primary_hover"),
            text_color="#FFFFFF",
            command=self.open_admin_panel
        )
        self.admin_btn.place(x=1200, y=40)  # Will be updated by on_window_resize

        self.watermark_label = ctk.CTkLabel(
            self,
            text="developed by jethro · 2025",
            font=("Poppins", 10, "italic"),
            text_color=theme.get("muted"),
            fg_color=None
        )
        self.watermark_label.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=10)

        # MOSCO Logo - ABSOLUTE POSITIONED at same level as buttons
        self.logo_frame = ctk.CTkFrame(self, fg_color=theme.get("bg"))
        self.logo_frame.place(x=0, y=40)  # Centered horizontally, 40px from top
        self.logo_frame.bind("<Button-1>", self.remove_focus)

        # Load bigger logo images
        try:
            self.logo_img1 = ctk.CTkImage(
                light_image=Image.open(f"{ICON_PATH}\\mosco logo light.png"),
                dark_image=Image.open(f"{ICON_PATH}\\mosco logo.png"), 
                size=(120, 120)
            )
            self.logo_img_text = ctk.CTkImage(
                light_image=Image.open(f"{ICON_PATH}\\mosco text light.png"),
                dark_image=Image.open(f"{ICON_PATH}\\mosco text.png"),
                size=(420, 120)
            )
        except Exception as e:
            print(f"Error loading logo images: {e}")
            self.logo_img1 = None
            self.logo_img_text = None

        self.create_logo_section()

        # Create main content frame (no scrollbar)
        self.main_content = ctk.CTkFrame(self, fg_color=theme.get("bg"))
        self.main_content.pack(fill="both", expand=True, pady=(170, 20), padx=20)  # Leave space for fixed elements
        self.watermark_label.lift()

    def create_logo_section(self):
        """Create bigger MOSCO logo section"""
        for widget in self.logo_frame.winfo_children():
            widget.destroy()

        try:
            if self.logo_img1 and self.logo_img_text:
                lbl1 = ctk.CTkLabel(self.logo_frame, image=self.logo_img1, text="", bg_color=theme.get("bg"))
                lbl1.pack(side="left", padx=(0, 5))
                lbl1.bind("<Button-1>", self.remove_focus)

                lbl2 = ctk.CTkLabel(self.logo_frame, image=self.logo_img_text, text="", bg_color=theme.get("bg"))
                lbl2.pack(side="left")
                lbl2.bind("<Button-1>", self.remove_focus)
            else:
                # Fallback text
                title_label = ctk.CTkLabel(self.logo_frame, text="MOSCO", 
                                         font=("Hero", 36, "bold"), text_color=theme.get("text"))
                title_label.pack()
                title_label.bind("<Button-1>", self.remove_focus)
        except Exception as e:
            print(f"Error creating logo section: {e}")

    def _handle_back_button(self):
        """Handle back button click"""
        if self.controller:
            self.controller.go_back(self.return_to)
        else:
            self.master.destroy()

    def _create_search_section(self):
        """Create search filters section"""
        self.search_section = ctk.CTkFrame(self.main_content, fg_color=theme.get("card"), corner_radius=40)
        self.search_section.pack(fill="x", pady=(0, 10))

        search_inner = ctk.CTkFrame(self.search_section, fg_color="transparent")
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
            text_color=theme.get("text")
        )
        label.grid(row=0, column=0, pady=(0, 8), sticky="ew")
        self.search_label_widgets.append(label)

        # Entry
        var = self.search_vars[key]
        entry = self._create_entry_widget(field_frame, var, display_name, key)
        entry.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        
        self.entry_widgets[key] = entry
        self.entry_fields.append(entry)  # Store for Backspace navigation
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
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            font=("Poppins", 18),
            corner_radius=40,
            border_width=1,
            border_color=theme.get("border"),
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
                entry.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("accent"))
            else:
                entry.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

    def _on_entry_focus(self, entry, has_focus):
        """Handle entry focus effects"""
        if has_focus:
            entry.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("input_focus"))
        else:
            entry.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

    def _create_inch_label(self, parent, key, var):
        """Create inch conversion label for size fields"""
        inch_label = ctk.CTkLabel(
            parent,
            text="",
            font=("Poppins", 18, "bold"),
            text_color=theme.get("text")
        )
        inch_label.grid(row=2, column=0, pady=(6, 0), sticky="ew")
        self.inch_labels[key] = inch_label

        # Initialize and setup trace
        self._update_inch_label(key)
        var.trace_add("write", lambda *args, k=key: self._update_inch_label(k))

    def _update_inch_label(self, key: str):
        """Update inch conversion label"""
        text, is_err = convert_mm_to_inches_display(self.get_var(key))
        color = "#FF4444" if is_err else theme.get("text")
        self.inch_labels[key].configure(text=text, text_color=color)

    def _setup_entry_backspace_navigation(self):
        """Setup Backspace navigation between Entry fields."""
        if not self.entry_fields:
            return
        for i, entry in enumerate(self.entry_fields):
            if hasattr(entry, '_entry'):
                entry._entry.bind("<BackSpace>", lambda e, idx=i: self._handle_entry_backspace(idx, e))
            else:
                entry.bind("<BackSpace>", lambda e, idx=i: self._handle_entry_backspace(idx, e))

    def _handle_entry_backspace(self, field_index: int, event):
        """Handle Backspace key on Entry fields."""
        current_entry = self.entry_fields[field_index]
        current_text = current_entry.get() if hasattr(current_entry, 'get') else current_entry._entry.get()
        
        if current_text:
            return None  # Allow normal deletion
        
        if field_index > 0:
            prev_entry = self.entry_fields[field_index - 1]
            prev_text = prev_entry.get() if hasattr(prev_entry, 'get') else prev_entry._entry.get()
            
            if prev_text:
                if hasattr(prev_entry, 'delete'):
                    prev_entry.delete(len(prev_text) - 1, "end")
                else:
                    prev_entry._entry.delete(len(prev_text) - 1, "end")
            
            prev_entry.focus() if hasattr(prev_entry, 'focus') else prev_entry._entry.focus()
        
        return "break"

    def _create_sort_controls(self, parent):
        """Create sort and filter controls"""
        # Sort control
        sort_frame = ctk.CTkFrame(parent, fg_color="transparent", height=130)
        sort_frame.grid(row=0, column=6, padx=5, sticky="ew")
        sort_frame.grid_propagate(False)
        sort_frame.grid_columnconfigure(0, weight=1)

        self.sort_label = ctk.CTkLabel(
            sort_frame, 
            text="Sort By",
            font=("Poppins", 18, "bold"),
            text_color=theme.get("text")
        )
        self.sort_label.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        sort_combo = self._create_combo_widget(
            sort_frame, 
            self.sort_by, 
            ["Size", "Quantity"]
        )
        sort_combo.grid(row=1, column=0, pady=(0, 8), sticky="ew")
        self.sort_by.trace_add("write", lambda *args: self.refresh_product_list())

        # Stock filter control
        stock_frame = ctk.CTkFrame(parent, fg_color="transparent", height=130)
        stock_frame.grid(row=0, column=7, padx=5, sticky="ew")
        stock_frame.grid_propagate(False)
        stock_frame.grid_columnconfigure(0, weight=1)

        self.stock_label = ctk.CTkLabel(
            stock_frame, 
            text="Stock Filter",
            font=("Poppins", 18, "bold"),
            text_color=theme.get("text")
        )
        self.stock_label.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        stock_combo = self._create_combo_widget(
            stock_frame, 
            self.stock_filter, 
            ["All", "In Stock", "Low Stock", "Out of Stock", "Unknown Stock"]
        )
        stock_combo.grid(row=1, column=0, pady=(0, 8), sticky="ew")
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
            fg_color=theme.get("input"),
            button_color=theme.get("accent"),
            button_hover_color=theme.get("accent_hover"),
            dropdown_fg_color=theme.get("card"),
            dropdown_text_color=theme.get("text"),
            dropdown_hover_color=theme.get("combo_hover"),
            text_color=theme.get("text"),
            font=("Poppins", 18),
            corner_radius=40,
            border_width=1,
            border_color=theme.get("border")
        )
        
        combo.bind("<Enter>", lambda e: self._on_combo_hover(combo, True))
        combo.bind("<Leave>", lambda e: self._on_combo_hover(combo, False))
        self.combo_widgets.append(combo)
        
        return combo

    def _on_combo_hover(self, combo, is_enter):
        """Handle combo box hover effects"""
        if is_enter:
            combo.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("accent"))
        else:
            combo.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

    def _create_table_section(self):
        """Create data table section that fills remaining space"""
        # Table section - fills all remaining space
        self.table_section = ctk.CTkFrame(self.main_content, fg_color=theme.get("card"), corner_radius=40)
        self.table_section.pack(fill="both", expand=True)

        # Table inner frame
        table_inner = ctk.CTkFrame(self.table_section, fg_color="transparent")
        table_inner.pack(fill="both", expand=True, padx=30, pady=30)
        table_inner.grid_rowconfigure(1, weight=1)  # Make table row expandable
        table_inner.grid_columnconfigure(0, weight=1)  # Make table column expandable

        # Status label INSIDE the table card - top right
        status_frame = ctk.CTkFrame(table_inner, fg_color="transparent")
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="",
            font=("Poppins", 20),  # Smaller font
            text_color=theme.get("text")
        )
        self.status_label.pack(side="top")

        # Table frame that expands to fill space
        table_frame = ctk.CTkFrame(table_inner, fg_color="transparent")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self._setup_treeview_style()
        self._create_treeview(table_frame)

    def _setup_treeview_style(self):
        """Configure treeview styling"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background=theme.get("card_alt"),
                        foreground=theme.get("text"),
                        fieldbackground=theme.get("card_alt"),
                        font=("Poppins", 18),
                        rowheight=40,
                        borderwidth=1,
                        relief="solid")
        style.configure("Custom.Treeview.Heading",
                        background=theme.get("heading_bg"),
                        foreground=theme.get("heading_fg"),
                        font=("Poppins", 20, "bold"),
                        borderwidth=1)
        
        # Selection styling uses theme-aware table_selected color (distinct from unknown stock)
        style.map("Custom.Treeview", 
                 background=[("selected", theme.get("table_selected"))],
                 foreground=[("selected", "#FFFFFF" if theme.mode == "dark" else "#000000")])
        
        style.map("Custom.Treeview.Heading", background=[("active", theme.get("accent_hover"))])

        # Fixed scrollbar styling - always use theme colors
        style.configure(
            "Red.Vertical.TScrollbar",
            background=theme.get("primary"),
            troughcolor=theme.get("scroll_trough"),
            bordercolor=theme.get("scroll_trough"),
            lightcolor=theme.get("primary"),
            darkcolor=theme.get("primary"),
            arrowcolor="#FFFFFF",  # Always white arrows for visibility on red
            focuscolor="none"
        )
        
        # Additional scrollbar states
        style.map(
            "Red.Vertical.TScrollbar",
            background=[("active", theme.get("primary_hover"))],
            lightcolor=[("active", theme.get("primary_hover"))],
            darkcolor=[("active", theme.get("primary_hover"))]
        )

    def _create_treeview(self, parent):
        """Create and configure treeview widget"""
        # Columns: Items (TYPE SIZE BRAND), Part No., Origin, Notes, Qty, Price
        columns = ("items", "part_no", "origin", "notes", "qty", "price")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", style="Custom.Treeview")
        
        # Configure tags (colors applied dynamically based on theme)
        self._apply_tree_tags_theme()

        # Configure columns
        display_names = {
            "items": "Items",
            "part_no": "Part No.",
            "origin": "Origin",
            "notes": "Notes",
            "qty": "Qty",
            "price": "Price"
        }

        for col in columns:
            self.tree.heading(col, text=display_names[col])
            # Make Items column wider for readability
            width = 260 if col == "items" else 120
            self.tree.column(col, anchor="center", width=width)

        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview, style="Red.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # Setup tree bindings
        # Highlight selection; remove highlight when clicking outside
        self.tree.bind("<Double-1>", self.open_transaction_page)
        # Right-click to copy formatted product info to clipboard
        self.tree.bind("<Button-3>", self._on_tree_right_click)
        self.bind("<Button-1>", lambda e: self.tree.selection_remove(self.tree.selection()))

    def remove_focus(self, event=None):
        """Remove focus from current widget"""
        self.focus()

    def create_password_window(self, callback=None):
        """Create password input dialog"""
        password_window = ctk.CTkToplevel(self.root)
        password_window.title("Admin Access")
        password_window.geometry("450x350")
        password_window.resizable(False, False)
        password_window.configure(fg_color=theme.get("bg"))
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
        main_frame = ctk.CTkFrame(window, fg_color=theme.get("bg"), corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        content_frame = ctk.CTkFrame(
            main_frame, 
            fg_color=theme.get("card"), 
            corner_radius=40, 
            border_width=1, 
            border_color=theme.get("border")
        )
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Title and subtitle
        title_label = ctk.CTkLabel(
            content_frame, 
            text="Admin Access", 
            font=("Poppins", 28, "bold"), 
            text_color=theme.get("heading_fg")
        )
        title_label.pack(pady=(40, 20))
        
        subtitle_label = ctk.CTkLabel(
            content_frame, 
            text="Enter admin password to continue", 
            font=("Poppins", 16), 
            text_color=theme.get("text")
        )
        subtitle_label.pack(pady=(0, 40))

        # Password entry section
        entry_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        entry_container.pack(pady=(0, 30))
        
        password_label = ctk.CTkLabel(
            entry_container, 
            text="Password", 
            font=("Poppins", 16, "bold"), 
            text_color=theme.get("text")
        )
        password_label.pack(pady=(0, 10))
        
        password_entry = ctk.CTkEntry(
        entry_container,
        width=280,
        height=40,
        fg_color=theme.get("input"),
        text_color=theme.get("text"),
        font=("Poppins", 14),
        corner_radius=40,
        border_width=2,
        border_color=theme.get("border"),
        placeholder_text="Enter password",
        show="*"
        )
        password_entry.pack(pady=(0, 10))

        # Bind <Map> event to focus when widget appears
        def focus_entry(event):
            password_entry.focus()

        password_entry.bind("<Map>", focus_entry)

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
                entry.configure(border_color=theme.get("primary"), fg_color=theme.get("accent"))
        
        def on_leave(event):
            if entry.focus_get() != entry:
                entry.configure(border_color=theme.get("border"), fg_color=theme.get("input"))
        
        def on_focus_in(event):
            entry.configure(border_color=theme.get("primary"), fg_color=theme.get("input_focus"))
        
        def on_focus_out(event):
            entry.configure(border_color=theme.get("border"), fg_color=theme.get("input"))
        
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
            fg_color=theme.get("accent_hover"), 
            hover_color=theme.get("accent"), 
            text_color=theme.get("text"), 
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
            fg_color=theme.get("primary"), 
            hover_color=theme.get("primary_hover"), 
            text_color="#FFFFFF",  # Always white on red
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

        # Populate tree with alternating rows
        for index, item in enumerate(display_data):
            qty = item[4]
            base_tag = get_stock_tag(qty)
            # Format quantity for display (show ? for unknown stock)
            from ..ui.mm import format_stock_display
            qty_display = format_stock_display(qty)
            # Create display row with formatted quantity
            display_item = list(item[:6])
            display_item[4] = qty_display  # Replace qty with formatted version
            
            # Always apply alternating background tag
            alt_tag = "alt_even" if (index % 2 == 0) else "alt_odd"
            
            # Apply both alternating tag and stock tag (stock tag provides text color)
            if base_tag == "normal":
                self.tree.insert("", tk.END, values=display_item, tags=(alt_tag, "normal"))
            else:
                self.tree.insert("", tk.END, values=display_item, tags=(alt_tag, base_tag))

        # Update status
        self.status_label.configure(text=f"Total Oil Seal Products: {len(display_data)}")

    def _apply_tree_tags_theme(self):
        """Apply tag colors for tree rows based on current theme/mode."""
        try:
            # Normal rows use themed foreground only (no background for column-specific coloring)
            self.tree.tag_configure("normal", foreground=theme.get("text"))
            # Alternate stripes - different background but no text coloring change
            self.tree.tag_configure("alt_even", background=theme.get("card_alt"))
            self.tree.tag_configure("alt_odd", background=theme.get("card"))
            # Stock highlight tags - use foreground colors only for Items column, keep default bg
            if theme.mode == "dark":
                low_fg = "#FFD700"      # Gold for low stock
                out_fg = "#FF6B6B"      # Red for out of stock
                unknown_fg = "#D9C4E8"  # Purple for unknown stock
            else:
                low_fg = "#FF8C00"      # Dark orange for low stock
                out_fg = "#B22222"      # Dark red for out of stock
                unknown_fg = "#8B5FA0"  # Dark purple for unknown stock
            
            self.tree.tag_configure("low", foreground=low_fg)
            self.tree.tag_configure("out", foreground=out_fg)
            self.tree.tag_configure("unknown", foreground=unknown_fg)
        except Exception:
            pass

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

    def _on_tree_right_click(self, event):
        """Copy formatted product info to clipboard on right-click."""
        try:
            item_id = self.tree.identify_row(event.y)
            if not item_id:
                return
            self.tree.selection_set(item_id)
            item_values = self.tree.item(item_id).get("values")
            if not item_values:
                return

            details = create_product_details(list(item_values))
            if not details:
                return

            # Build first line: TYPE ID-OD-TH BRAND Oil Seal (Origin)
            id_ = details.get('id', '')
            od = details.get('od', '')
            th = details.get('th', '')
            type_ = details.get('type', '')
            brand = details.get('brand', '')
            origin = details.get('country_of_origin', '')

            origin_part = f" {origin}" if origin else ""
            first_line = f"{type_} {id_}-{od}-{th} {brand} Oil Seal{origin_part}"

            # Price line: format as integer with trailing hyphen if no cents, else two decimals
            price = details.get('price', 0.0)
            try:
                p = float(price)
            except Exception:
                p = 0.0
            if abs(p - int(p)) < 1e-9:
                price_line = f"₱{int(p)}- / pc."
            else:
                price_line = f"₱{p:.2f} / pc."

            out_text = f"{first_line}\n{price_line}"

            # Copy to clipboard
            try:
                self.clipboard_clear()
                self.clipboard_append(out_text)
                # Temporary status update
                try:
                    self.status_label.configure(text="Copied to clipboard!")
                    self.after(1500, lambda: self.status_label.configure(text=f"Total Oil Seal Products: {len(self.tree.get_children())}"))
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            return

    def apply_theme(self):
        try:
            # Update main components
            self.configure(fg_color=theme.get("bg"))
            self.root.configure(bg=theme.get("bg"))
            
            # Update main content frame
            if hasattr(self, 'main_content'):
                self.main_content.configure(fg_color=theme.get("bg"))
            
            # Update logo frame
            if hasattr(self, 'logo_frame'):
                self.logo_frame.configure(fg_color=theme.get("bg"))
                self.create_logo_section()  # Recreate logo for light/dark switching
            
            # Update frames
            if hasattr(self, 'search_section'):
                self.search_section.configure(fg_color=theme.get("card"))
            if hasattr(self, 'table_section'):
                self.table_section.configure(fg_color=theme.get("card"))
            
            # Update buttons with consistent white text on red
            if hasattr(self, 'back_btn'):
                self.back_btn.configure(
                    fg_color=theme.get("primary"),
                    hover_color=theme.get("primary_hover"),
                    text_color="#FFFFFF"
                )
            if hasattr(self, 'admin_btn'):
                self.admin_btn.configure(
                    fg_color=theme.get("primary"),
                    hover_color=theme.get("primary_hover"),
                    text_color="#FFFFFF"
                )

            if hasattr(self, 'watermark_label'):
                self.watermark_label.configure(text_color=theme.get("muted"))
                self.watermark_label.lift()

            # Reapply treeview styles (including selection colors)
            self._setup_treeview_style()
            
            # Update entry widgets
            for key, entry in self.entry_widgets.items():
                entry.configure(
                    fg_color=theme.get("input"), 
                    text_color=theme.get("text"), 
                    border_color=theme.get("border")
                )
            
            # Update inch labels
            for key in self.inch_labels:
                self._update_inch_label(key)
            
            # Update search labels
            for lbl in getattr(self, 'search_label_widgets', []):
                try:
                    lbl.configure(text_color=theme.get("text"))
                except Exception:
                    pass
            
            # Update sort and stock labels
            for lbl in (getattr(self, 'sort_label', None), getattr(self, 'stock_label', None)):
                if lbl:
                    try:
                        lbl.configure(text_color=theme.get("text"))
                    except Exception:
                        pass
            
            # Update combobox widgets
            for combo in getattr(self, 'combo_widgets', []):
                try:
                    combo.configure(
                        fg_color=theme.get("input"),
                        button_color=theme.get("accent"),
                        button_hover_color=theme.get("accent_hover"),
                        dropdown_fg_color=theme.get("card"),
                        dropdown_text_color=theme.get("text"),
                        dropdown_hover_color=theme.get("combo_hover"),
                        text_color=theme.get("text"),
                        border_color=theme.get("border"),
                    )
                except Exception:
                    pass
            
            # Update status label
            if hasattr(self, 'status_label'):
                self.status_label.configure(text_color=theme.get("text"))
            
            # Re-apply row tag colors for normal/alternate and stock highlights
            if hasattr(self, 'tree'):
                self._apply_tree_tags_theme()
            
            # Update button positions after theme change
            self.after(10, self.on_window_resize)
                
        except Exception as e:
            print(f"Error applying theme: {e}")

    def on_frame_show(self):
        """Called when this frame is shown - refresh theme-dependent styles"""
        self._setup_treeview_style()
        self.refresh_product_list()