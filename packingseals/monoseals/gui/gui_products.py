import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_transactions import TransactionTab
from .gui_prod_aed import ProductFormHandler
from ..admin.products import ProductsLogic
from theme import theme


class AdminPanel:
    def __init__(self, parent, main_app, controller, on_close_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_close_callback = on_close_callback

        # Initialize logic handler
        self.products_logic = ProductsLogic()

        # Create CustomTkinter window
        self.win = ctk.CTkToplevel(parent)
        self.win.withdraw()
        self.win.title("Manage Database")
        self.win.configure(fg_color=theme.get("bg"))  # Set window background to theme

        # Apply desired default window state: windowed fullscreen (maximized properly)
        self._apply_initial_maximized_state()

        # Show window
        self.win.deiconify()

        # Configure minimum usable size to avoid too-small layouts
        try:
            self.win.minsize(1000, 700)
        except Exception:
            pass

        # Bind to minimize/unmap to implement custom shrink-and-center behavior
        self.win.bind("<Unmap>", self._on_unmap_minimize)

        # Create main container with dynamic background
        self.main_container = ctk.CTkFrame(self.win, fg_color=theme.get("bg"))
        self.main_container.pack(fill="both", expand=True)

        # Create tabs
        self.create_tab_system(self.main_container)

        # Handle window closing
        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Subscribe to theme changes to update colors dynamically
        theme.subscribe(self.update_colors)

        # --- Add keyboard shortcut bindings here ---
        self._bind_shortcuts()

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts for the admin panel"""
        root = self.win
        
        # Existing shortcut
        root.bind("<Control-Key-2>", lambda event: self.prod_form_handler.add_product())
        
        # Add Ctrl+Tab for switching between tabs
        root.bind("<Control-Tab>", self._cycle_tabs)
        root.bind("<Control-Shift-Tab>", self._reverse_cycle_tabs)

    def _cycle_tabs(self, event=None):
        """Cycle forward through tabs (Products → Transactions → Products...)"""
        if self.current_tab == "products":
            self.switch_tab("transactions")
        else:
            self.switch_tab("products")
        
        # Prevent default Tab behavior
        return "break"

    def _reverse_cycle_tabs(self, event=None):
        """Cycle backward through tabs (same as forward since only 2 tabs)"""
        if self.current_tab == "products":
            self.switch_tab("transactions")
        else:
            self.switch_tab("products")
        
        # Prevent default Tab behavior
        return "break"

    # --- Rest of your existing methods below ---

    def _apply_initial_maximized_state(self):
        """Maximize using the window manager to avoid geometry/titlebar mismatches.

        Tries native 'zoomed' state first, then falls back to the WM-reported
        maximum size to emulate a proper windowed-fullscreen without cutting off
        content when toggling maximize.
        """
        try:
            # Request maximize via WM
            self.win.update_idletasks()
            self.win.state("zoomed")

            # Validate maximize took effect; if not, fall back
            self.win.update_idletasks()
            max_w, max_h = self.win.wm_maxsize()
            cur_w = self.win.winfo_width()
            cur_h = self.win.winfo_height()
            if cur_w <= 1 or cur_h <= 1:
                # Window not yet realized; compute after another update
                self.win.update()
                cur_w = self.win.winfo_width()
                cur_h = self.win.winfo_height()

            # If not close to WM max size, apply fallback geometry
            if max_w and max_h and (abs(cur_w - max_w) > 10 or abs(cur_h - max_h) > 10):
                self.win.geometry(f"{max_w}x{max_h}+0+0")
        except Exception:
            # Fallback purely to wm_maxsize if zoomed is unsupported
            try:
                max_w, max_h = self.win.wm_maxsize()
                if max_w and max_h:
                    self.win.geometry(f"{max_w}x{max_h}+0+0")
                else:
                    # Last-resort: use screen size
                    screen_w = self.win.winfo_screenwidth()
                    screen_h = self.win.winfo_screenheight()
                    self.win.geometry(f"{screen_w}x{screen_h}+0+0")
            except Exception:
                pass

    def _on_unmap_minimize(self, event):
        """When the window is minimized/iconified, shrink and center instead of hiding."""
        try:
            # Only intercept actual minimize/iconify actions
            if self.win.state() == "iconic":
                # Deiconify and switch to normal state
                self.win.after(1, self._shrink_and_center)
        except Exception:
            pass


    def _shrink_and_center(self):
        """Resize to a smaller, centered window that remains visible."""
        try:
            self.win.deiconify()
            self.win.state("normal")
            self.win.update_idletasks()

            screen_w = self.win.winfo_screenwidth()
            screen_h = self.win.winfo_screenheight()

            # Reasonable smaller size (not too small)
            target_w = max(int(screen_w * 0.7), 1000)
            target_h = max(int(screen_h * 0.7), 700)

            pos_x = max((screen_w - target_w) // 2, 0)
            pos_y = max((screen_h - target_h) // 2, 0)

            self.win.geometry(f"{target_w}x{target_h}+{pos_x}+{pos_y}")
        except Exception:
            pass


    def create_tab_system(self, parent):
        tab_header = ctk.CTkFrame(parent, fg_color="transparent", height=60)
        tab_header.pack(fill="x", pady=(20, 10), padx=20)
        tab_header.pack_propagate(False)

        tab_buttons_frame = ctk.CTkFrame(tab_header, fg_color="transparent")
        tab_buttons_frame.pack(fill="x", expand=True, pady=15)

        # Left spacer for centering
        left_spacer = ctk.CTkFrame(tab_buttons_frame, fg_color="transparent")
        left_spacer.pack(side="left", expand=True)

        self.current_tab = "products"

        self.products_tab_btn = ctk.CTkButton(
            tab_buttons_frame,
            text="Products",
            font=("Poppins", 16, "bold"),
            fg_color=theme.get("primary"),
            hover_color=theme.get("primary_hover"),
            text_color="#FFFFFF",  # Initially selected tab text is white
            corner_radius=25,
            width=150,
            height=40,
            command=lambda: self.switch_tab("products")
        )
        self.products_tab_btn.pack(side="left", padx=(0, 10))

        self.transactions_tab_btn = ctk.CTkButton(
            tab_buttons_frame,
            text="Transactions",
            font=("Poppins", 16, "bold"),
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            corner_radius=25,
            width=150,
            height=40,
            command=lambda: self.switch_tab("transactions")
        )
        self.transactions_tab_btn.pack(side="left")

        # Right spacer for centering
        right_spacer = ctk.CTkFrame(tab_buttons_frame, fg_color="transparent")
        right_spacer.pack(side="left", expand=True)

        self.tab_content = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=40)
        self.tab_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.products_frame = ctk.CTkFrame(self.tab_content, fg_color="transparent")
        self.transactions_frame = ctk.CTkFrame(self.tab_content, fg_color="transparent")

        self.create_products_tab()
        self.create_transactions_tab()

        self.switch_tab("products")


    def create_transactions_tab(self):
        self.transaction_tab = TransactionTab(
            notebook=self.transactions_frame,
            main_app=self.main_app,
            controller=self.controller,
            on_refresh_callback=self.refresh_all_tabs
        )


    def switch_tab(self, tab_name):
        self.products_frame.pack_forget()
        self.transactions_frame.pack_forget()

        if tab_name == "products":
            self.products_tab_btn.configure(
                fg_color=theme.get("primary"),
                hover_color=theme.get("primary_hover"),
                text_color="#FFFFFF"  # white text when selected
            )
            self.transactions_tab_btn.configure(
                fg_color=theme.get("accent"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text")  # normal text color when unselected
            )
            self.products_frame.pack(fill="both", expand=True)
        else:
            self.products_tab_btn.configure(
                fg_color=theme.get("accent"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text")
            )
            self.transactions_tab_btn.configure(
                fg_color=theme.get("primary"),
                hover_color=theme.get("primary_hover"),
                text_color="#FFFFFF"
            )
            self.transactions_frame.pack(fill="both", expand=True)

            if hasattr(self, 'transaction_tab'):
                self.transaction_tab.refresh_transactions()

        self.current_tab = tab_name


    def refresh_all_tabs(self):
        self.refresh_products()
        if self.on_close_callback:
            self.on_close_callback()


    def on_closing(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.win.destroy()


    def create_products_tab(self):
        self.prod_form_handler = ProductFormHandler(
            self.win,
            None,
            self.refresh_products
        )
        # Attach a post-add hook so that after adding a product we can
        # switch to the Transactions tab and open the Add Transaction form
        def _on_product_added(details):
            try:
                # Ensure transactions tab exists
                self.switch_tab("transactions")
                # Give the transactions tab a moment to initialize
                self.transactions_frame.update_idletasks()
                if hasattr(self, 'transaction_tab') and hasattr(self.transaction_tab, 'form_handler'):
                    # Prepare keys mapping expected by TransactionFormHandler
                    keys = {
                        'Type': details.get('Type', ''),
                        'ID': details.get('ID', ''),
                        'OD': details.get('OD', ''),
                        'TH': details.get('TH', ''),
                        'Brand': details.get('Brand', ''),
                    }
                    # Set last_transaction_keys so transaction form will prefill
                    self.transaction_tab.form_handler.last_transaction_keys = keys
                    # Open Add Transaction form
                    self.transaction_tab.form_handler.add_transaction()
            except Exception:
                pass

        # assign hook
        self.prod_form_handler.on_product_added = _on_product_added

        self.search_container = ctk.CTkFrame(self.products_frame, fg_color=theme.get("card"), corner_radius=40, height=90)
        self.search_container.pack(fill="x", pady=(20, 15), padx=20)
        self.search_container.pack_propagate(False)

        search_inner = ctk.CTkFrame(self.search_container, fg_color="transparent")
        search_inner.pack(fill="x", padx=20, pady=15)

        search_input_container = ctk.CTkFrame(search_inner, fg_color="transparent")
        search_input_container.pack(fill="x")
        search_input_container.grid_columnconfigure(1, weight=1)

        search_label = ctk.CTkLabel(
            search_input_container,
            text="Search:",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        search_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.prod_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_input_container,
            textvariable=self.prod_search_var,
            font=("Poppins", 13),
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=35,
            border_width=1,
            border_color=theme.get("border"),
            placeholder_text="Enter search term..."
        )
        search_entry.grid(row=0, column=1, sticky="ew")

        def on_entry_hover(entry, is_enter):
            if entry.focus_get() != entry:
                if is_enter:
                    entry.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("accent"))
                else:
                    entry.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

        def on_entry_focus(entry, has_focus):
            if has_focus:
                entry.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("input_focus"))
            else:
                entry.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

        search_entry.bind("<Enter>", lambda e: on_entry_hover(search_entry, True))
        search_entry.bind("<Leave>", lambda e: on_entry_hover(search_entry, False))
        search_entry.bind("<FocusIn>", lambda e: on_entry_focus(search_entry, True))
        search_entry.bind("<FocusOut>", lambda e: on_entry_focus(search_entry, False))

        self.prod_search_var.trace_add("write", lambda *args: self.refresh_products())

        self.table_container = ctk.CTkFrame(self.products_frame, fg_color=theme.get("card"), corner_radius=40)
        self.table_container.pack(fill="both", expand=True, pady=(0, 15), padx=20)

        inner_table = ctk.CTkFrame(self.table_container, fg_color="transparent")
        inner_table.pack(fill="both", expand=True, padx=20, pady=20)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Products.Treeview",
                        background=theme.get("card_alt"),
                        foreground=theme.get("text"),
                        fieldbackground=theme.get("card_alt"),
                        font=("Poppins", 12),
                        rowheight=35)
        style.configure("Products.Treeview.Heading",
                        background=theme.get("heading_bg"),
                        foreground=theme.get("heading_fg"),
                        font=("Poppins", 12, "bold"))
        selected_fg = "#000000" if theme.mode == "light" else "#FFFFFF"
        style.map("Products.Treeview",
                  background=[("selected", theme.get("table_selected"))],
                  foreground=[("selected", selected_fg)])
        style.map("Products.Treeview.Heading", background=[("active", theme.get("heading_bg"))])

        columns = ("item", "part_no", "origin", "notes", "price")
        self.headers = ["ITEM", "PART_NO", "ORIGIN", "NOTES", "PRICE"]
        self.sort_direction = {col: None for col in columns}
        self.prod_tree = ttk.Treeview(inner_table, columns=columns, show="headings", style="Products.Treeview")

        for col, header in zip(columns, self.headers):
            self.prod_tree.heading(col, text=header, command=lambda c=col: self.sort_column(c))
            self.prod_tree.column(col, width=150, anchor="center")

        tree_scrollbar = ttk.Scrollbar(inner_table, orient="vertical", command=self.prod_tree.yview)
        self.prod_tree.configure(yscrollcommand=tree_scrollbar.set)

        self.prod_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        self.prod_form_handler.prod_tree = self.prod_tree

        button_frame = ctk.CTkFrame(self.products_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        add_btn = ctk.CTkButton(
            button_frame,
            text="Add",
            font=("Poppins", 16, "bold"),
            fg_color="#22C55E",
            hover_color="#16A34A",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=45,
            command=self.prod_form_handler.add_product
        )
        add_btn.pack(side="left", padx=(0, 10))

        edit_btn = ctk.CTkButton(
            button_frame,
            text="Edit",
            font=("Poppins", 16, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=45,
            command=self.prod_form_handler.edit_product
        )
        edit_btn.pack(side="left", padx=(0, 10))

        delete_btn = ctk.CTkButton(
            button_frame,
            text="Delete",
            font=("Poppins", 16, "bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=45,
            command=self.prod_form_handler.delete_product
        )
        delete_btn.pack(side="left")

        self.current_products_data = []

        self.refresh_products()


    def refresh_products(self):
        self.prod_tree.delete(*self.prod_tree.get_children())
        keyword = self.prod_search_var.get()
        self.current_products_data = self.products_logic.search_products(keyword)
        for product in self.current_products_data:
            self.prod_tree.insert("", tk.END, values=(
                product['item'],
                product['part_no'],
                product['origin'],
                product['notes'],
                product['price']
            ))


    def sort_column(self, col):
        if col in ("part_no", "notes"):
            return

        ascending = self.sort_direction[col] != "asc"
        self.sort_direction[col] = "asc" if ascending else "desc"

        sorted_data = self.products_logic.sort_products_data(
            self.current_products_data,
            col,
            ascending
        )

        self.prod_tree.delete(*self.prod_tree.get_children())
        for product in sorted_data:
            self.prod_tree.insert("", tk.END, values=(
                product['item'],
                product['part_no'],
                product['origin'],
                product['notes'],
                product['price']
            ))

        for c, h in zip(self.prod_tree["columns"], self.headers):
            arrow = " ↑" if c == col and ascending else " ↓" if c == col else ""
            self.prod_tree.heading(c, text=h + arrow)


    def update_colors(self):
        self.win.configure(fg_color=theme.get("bg"))
        self.main_container.configure(fg_color=theme.get("bg"))

        if hasattr(self, "search_container"):
            self.search_container.configure(fg_color=theme.get("card"))
        if hasattr(self, "table_container"):
            self.table_container.configure(fg_color=theme.get("card_alt"))

        style = ttk.Style()
        style.configure("Products.Treeview",
                        background=theme.get("card_alt"),
                        foreground=theme.get("text"),
                        fieldbackground=theme.get("card_alt"))
        style.configure("Products.Treeview.Heading",
                        background=theme.get("heading_bg"),
                        foreground=theme.get("heading_fg"))

        selected_fg = "#000000" if theme.mode == "light" else "#FFFFFF"
        style.map("Products.Treeview",
                  background=[("selected", theme.get("table_selected"))],
                  foreground=[("selected", selected_fg)])
        style.map("Products.Treeview.Heading", background=[("active", theme.get("heading_bg"))])

        # Update tab buttons text colors on theme change and selection
        if self.current_tab == "products":
            self.products_tab_btn.configure(
                fg_color=theme.get("primary"),
                hover_color=theme.get("primary_hover"),
                text_color="#FFFFFF"
            )
            self.transactions_tab_btn.configure(
                fg_color=theme.get("accent"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text")
            )
        else:
            self.products_tab_btn.configure(
                fg_color=theme.get("accent"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text")
            )
            self.transactions_tab_btn.configure(
                fg_color=theme.get("primary"),
                hover_color=theme.get("primary_hover"),
                text_color="#FFFFFF"
            )