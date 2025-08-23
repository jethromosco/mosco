import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from .gui_transactions import TransactionTab
from .gui_prod_aed import ProductFormHandler
from ..admin.products import ProductsLogic


class AdminPanel:
    def __init__(self, parent, main_app, controller, on_close_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_close_callback = on_close_callback
        
        # Initialize logic handler
        self.products_logic = ProductsLogic()
        
        # Create CustomTkinter window
        # Create hidden
        self.win = ctk.CTkToplevel(parent)
        self.win.withdraw()

        # Remove window manager decorations (prevents flash resize)
        self.win.overrideredirect(True)

        # Set directly to full screen size
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        self.win.geometry(f"{screen_w}x{screen_h}+0+0")

        # Reapply titlebar AFTER it's full screen (optional)
        self.win.overrideredirect(False)
        self.win.title("Manage Database")
        self.win.configure(fg_color="#000000")  # Set window background to black

        # Now show without resize flash
        self.win.deiconify()
        
        # Create main container with NO PADDING to eliminate gray borders
        main_container = ctk.CTkFrame(self.win, fg_color="#000000")
        main_container.pack(fill="both", expand=True)  # REMOVED padx=20, pady=20
        
        # Create custom tab system to match the app style
        self.create_tab_system(main_container)
        
        # Add a protocol to call the callback when the window is closed
        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_tab_system(self, parent):
        """Create custom tab system matching the app's design"""
        # Tab header frame - NO BACKGROUND, just for positioning
        tab_header = ctk.CTkFrame(parent, fg_color="transparent", height=60)
        tab_header.pack(fill="x", pady=(20, 10), padx=20)
        tab_header.pack_propagate(False)
        
        # Tab buttons container - transparent background
        tab_buttons_frame = ctk.CTkFrame(tab_header, fg_color="transparent")
        tab_buttons_frame.pack(expand=True, pady=15)
        
        # Tab state management
        self.current_tab = "products"
        
        # Products tab button
        self.products_tab_btn = ctk.CTkButton(
            tab_buttons_frame,
            text="Products",
            font=("Poppins", 16, "bold"),
            fg_color="#D00000",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            corner_radius=25,
            width=150,
            height=40,
            command=lambda: self.switch_tab("products")
        )
        self.products_tab_btn.pack(side="left", padx=(0, 10))
        
        # Transactions tab button
        self.transactions_tab_btn = ctk.CTkButton(
            tab_buttons_frame,
            text="Transactions",
            font=("Poppins", 16, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=150,
            height=40,
            command=lambda: self.switch_tab("transactions")
        )
        self.transactions_tab_btn.pack(side="left")
        
        # Tab content frame - ADD padding here instead
        self.tab_content = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=40)
        self.tab_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))  # MOVED padding here
        
        # Create tab frames
        self.products_frame = ctk.CTkFrame(self.tab_content, fg_color="transparent")
        self.transactions_frame = ctk.CTkFrame(self.tab_content, fg_color="transparent")
        
        # Initialize tabs
        self.create_products_tab()
        self.create_transactions_tab()
        
        # Show initial tab
        self.switch_tab("products")
    
    def create_transactions_tab(self):
        """Create the transactions tab using the TransactionTab class"""
        self.transaction_tab = TransactionTab(
            notebook=self.transactions_frame,
            main_app=self.main_app,
            controller=self.controller,
            on_refresh_callback=self.refresh_all_tabs
        )
    
    def switch_tab(self, tab_name):
        """Switch between tabs with proper styling updates"""
        # Hide all frames
        self.products_frame.pack_forget()
        self.transactions_frame.pack_forget()
        
        # Update button colors
        if tab_name == "products":
            self.products_tab_btn.configure(fg_color="#D00000", hover_color="#B71C1C")
            self.transactions_tab_btn.configure(fg_color="#4B5563", hover_color="#6B7280")
            # CONSISTENT padding for products frame
            self.products_frame.pack(fill="both", expand=True)  # REMOVED padx, pady here
        else:
            self.products_tab_btn.configure(fg_color="#4B5563", hover_color="#6B7280")
            self.transactions_tab_btn.configure(fg_color="#D00000", hover_color="#B71C1C")
            # CONSISTENT padding for transactions frame
            self.transactions_frame.pack(fill="both", expand=True)  # REMOVED padx, pady here
            
            # Refresh transactions when switching to that tab
            if hasattr(self, 'transaction_tab'):
                self.transaction_tab.refresh_transactions()
        
        self.current_tab = tab_name

    def refresh_all_tabs(self):
        """Refresh products tab + main app without closing AdminPanel."""
        self.refresh_products()
        if self.on_close_callback:
            self.on_close_callback()

    def on_closing(self):
        """Callback function to handle window closing and trigger refresh in the main app."""
        if self.on_close_callback:
            self.on_close_callback()
        self.win.destroy()

    def create_products_tab(self):
        """Create the products tab with the app's styling"""
        # Initialize form handler
        self.prod_form_handler = ProductFormHandler(
            self.win, 
            None, 
            self.refresh_products
        )

        # === Search Section === - First grey container with corner radius
        search_container = ctk.CTkFrame(self.products_frame, fg_color="#2b2b2b", corner_radius=40, height=90)
        search_container.pack(fill="x", pady=(20, 15), padx=20)
        search_container.pack_propagate(False)
        
        search_inner = ctk.CTkFrame(search_container, fg_color="transparent")
        search_inner.pack(fill="x", padx=20, pady=15)
        
        # Search container
        search_input_container = ctk.CTkFrame(search_inner, fg_color="transparent")
        search_input_container.pack(fill="x")
        search_input_container.grid_columnconfigure(1, weight=1)
        
        # Label
        search_label = ctk.CTkLabel(
            search_input_container,
            text="Search:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF"
        )
        search_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Search entry
        self.prod_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_input_container,
            textvariable=self.prod_search_var,
            font=("Poppins", 13),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            placeholder_text="Enter search term..."
        )
        search_entry.grid(row=0, column=1, sticky="ew")
        
        # Hover + Focus effects (mirroring gui_mm.py)
        def on_entry_hover(entry, is_enter):
            if entry.focus_get() != entry:
                if is_enter:
                    entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
                else:
                    entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

        def on_entry_focus(entry, has_focus):
            if has_focus:
                entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
            else:
                entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

        search_entry.bind("<Enter>", lambda e: on_entry_hover(search_entry, True))
        search_entry.bind("<Leave>", lambda e: on_entry_hover(search_entry, False))
        search_entry.bind("<FocusIn>", lambda e: on_entry_focus(search_entry, True))
        search_entry.bind("<FocusOut>", lambda e: on_entry_focus(search_entry, False))
        
        self.prod_search_var.trace_add("write", lambda *args: self.refresh_products())

        # === Table Section === - Second grey container with corner radius (separate from buttons)
        table_container = ctk.CTkFrame(self.products_frame, fg_color="#2b2b2b", corner_radius=40)
        table_container.pack(fill="both", expand=True, pady=(0, 15), padx=20)
        
        inner_table = ctk.CTkFrame(table_container, fg_color="transparent")
        inner_table.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Products.Treeview",
                        background="#2b2b2b",
                        foreground="#FFFFFF",
                        fieldbackground="#2b2b2b",
                        font=("Poppins", 12),
                        rowheight=35)
        style.configure("Products.Treeview.Heading",
                        background="#000000",
                        foreground="#D00000",
                        font=("Poppins", 12, "bold"))
        style.map("Products.Treeview", background=[("selected", "#374151")])
        style.map("Products.Treeview.Heading", background=[("active", "#111111")])

        # Create Treeview
        columns = ("item", "brand", "part_no", "origin", "notes", "price")
        self.headers = ["ITEM", "BRAND", "PART_NO", "ORIGIN", "NOTES", "PRICE"]
        self.sort_direction = {col: None for col in columns}
        self.prod_tree = ttk.Treeview(inner_table, columns=columns, show="headings", style="Products.Treeview")

        for col, header in zip(columns, self.headers):
            self.prod_tree.heading(col, text=header, command=lambda c=col: self.sort_column(c))
            self.prod_tree.column(col, width=150, anchor="center")

        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(inner_table, orient="vertical", command=self.prod_tree.yview)
        self.prod_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.prod_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Pass treeview to handler
        self.prod_form_handler.prod_tree = self.prod_tree

        # === Buttons Section === - ON BLACK BACKGROUND, separate from table
        button_frame = ctk.CTkFrame(self.products_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 20))
        
        # Add button
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
        
        # Edit button
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
        
        # Delete button
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

        # Store current products data for sorting
        self.current_products_data = []
        
        self.refresh_products()

    def refresh_products(self):
        """Refresh the products display using logic layer."""
        # Clear the tree
        self.prod_tree.delete(*self.prod_tree.get_children())
        
        # Get search keyword
        keyword = self.prod_search_var.get()
        
        # Use logic layer to get filtered products
        self.current_products_data = self.products_logic.search_products(keyword)
        
        # Display products in tree
        for product in self.current_products_data:
            self.prod_tree.insert("", tk.END, values=(
                product['item'],
                product['brand'],
                product['part_no'],
                product['origin'],
                product['notes'],
                product['price']
            ))

    def sort_column(self, col):
        """Sort table by column using logic layer."""
        if col in ("part_no", "notes"):
            return

        # Toggle sort direction
        ascending = self.sort_direction[col] != "asc"
        self.sort_direction[col] = "asc" if ascending else "desc"

        # Use logic layer to sort data
        sorted_data = self.products_logic.sort_products_data(
            self.current_products_data, 
            col, 
            ascending
        )
        
        # Clear and repopulate tree with sorted data
        self.prod_tree.delete(*self.prod_tree.get_children())
        for product in sorted_data:
            self.prod_tree.insert("", tk.END, values=(
                product['item'],
                product['brand'],
                product['part_no'],
                product['origin'],
                product['notes'],
                product['price']
            ))

        # Update headers with sort indicators
        for c, h in zip(self.prod_tree["columns"], self.headers):
            arrow = " ↑" if c == col and ascending else " ↓" if c == col else ""
            self.prod_tree.heading(c, text=h + arrow)