import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from ..database import connect_db
from .gui_transactions import TransactionTab
from .gui_prod_aed import ProductFormHandler
from fractions import Fraction


def parse_measurement(value):
    try:
        if "/" in value:
            return float(Fraction(value))
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid measurement: {value}")


class AdminPanel:
    def __init__(self, parent, main_app, controller, on_close_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_close_callback = on_close_callback
        
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

        # Reapply titlebar AFTER it’s full screen (optional)
        self.win.overrideredirect(False)
        self.win.title("Manage Database")

        # Now show without resize flash
        self.win.deiconify()
        
        # Create main container with the app's styling
        main_container = ctk.CTkFrame(self.win, fg_color="#000000")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create custom tab system to match the app style
        self.create_tab_system(main_container)
        
        # Add a protocol to call the callback when the window is closed
        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_tab_system(self, parent):
        """Create custom tab system matching the app's design"""
        # Tab header frame
        tab_header = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=40, height=60)
        tab_header.pack(fill="x", pady=(0, 10))
        tab_header.pack_propagate(False)
        
        # Tab buttons container
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
        
        # Tab content frame
        self.tab_content = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=40)
        self.tab_content.pack(fill="both", expand=True)
        
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
            self.products_frame.pack(fill="both", expand=True, padx=20, pady=20)
        else:
            self.products_tab_btn.configure(fg_color="#4B5563", hover_color="#6B7280")
            self.transactions_tab_btn.configure(fg_color="#D00000", hover_color="#B71C1C")
            self.transactions_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
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
        self.prod_form_handler = ProductFormHandler(self.win, None, self.refresh_products)

        # === Search Section ===
        search_section = ctk.CTkFrame(self.products_frame, fg_color="#374151", corner_radius=25)
        search_section.pack(fill="x", pady=(0, 15))
        
        search_inner = ctk.CTkFrame(search_section, fg_color="transparent")
        search_inner.pack(fill="x", padx=20, pady=15)
        
        # Search container
        search_container = ctk.CTkFrame(search_inner, fg_color="transparent")
        search_container.pack(fill="x")
        search_container.grid_columnconfigure(1, weight=1)
        
        # Search label
        search_label = ctk.CTkLabel(
            search_container,
            text="Search ITEM:",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF"
        )
        search_label.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # Search entry
        self.prod_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_container,
            textvariable=self.prod_search_var,
            font=("Poppins", 13),
            fg_color="#2b2b2b",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            border_width=1,
            border_color="#4B5563",
            placeholder_text="Enter search term..."
        )
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        # Hover effects
        def on_search_enter(event):
            if search_entry.focus_get() != search_entry:
                search_entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
        def on_search_leave(event):
            if search_entry.focus_get() != search_entry:
                search_entry.configure(border_color="#4B5563", border_width=1, fg_color="#2b2b2b")
        def on_search_focus_in(event):
            search_entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
        def on_search_focus_out(event):
            search_entry.configure(border_color="#4B5563", border_width=1, fg_color="#2b2b2b")
        
        search_entry.bind("<Enter>", on_search_enter)
        search_entry.bind("<Leave>", on_search_leave)
        search_entry.bind("<FocusIn>", on_search_focus_in)
        search_entry.bind("<FocusOut>", on_search_focus_out)
        
        self.prod_search_var.trace_add("write", lambda *args: self.refresh_products())

        # === Table Section ===
        table_container = ctk.CTkFrame(self.products_frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, pady=(0, 15))
        
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
        self.prod_tree = ttk.Treeview(table_container, columns=columns, show="headings", style="Products.Treeview")

        for col, header in zip(columns, self.headers):
            self.prod_tree.heading(col, text=header, command=lambda c=col: self.sort_column(c))
            self.prod_tree.column(col, width=150, anchor="center")

        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.prod_tree.yview)
        self.prod_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.prod_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Pass treeview to handler
        self.prod_form_handler.prod_tree = self.prod_tree

        # === Buttons Section ===
        buttons_section = ctk.CTkFrame(self.products_frame, fg_color="transparent")
        buttons_section.pack(fill="x")
        
        button_container = ctk.CTkFrame(buttons_section, fg_color="transparent")
        button_container.pack(anchor="center")
        
        # Add button
        add_btn = ctk.CTkButton(
            button_container,
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
            button_container,
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
            button_container,
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

        self.refresh_products()

    def refresh_products(self):
        self.prod_tree.delete(*self.prod_tree.get_children())

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price
            FROM products
            ORDER BY id ASC, od ASC, th ASC
        """)
        rows = cur.fetchall()
        conn.close()

        keyword = self.prod_search_var.get().lower()
        for row in rows:
            type_, id_, od, th, brand, part_no, origin, notes, price = row

            def fmt(val):
                return str(val) if isinstance(val, str) else (str(int(val)) if float(val).is_integer() else str(val))

            id_str = fmt(id_)
            od_str = fmt(od)
            th_str = fmt(th)

            item_str = f"{type_.upper()} {id_str}-{od_str}-{th_str}"
            combined = f"{type_} {id_str} {od_str} {th_str}".lower()

            if keyword in combined:
                self.prod_tree.insert("", tk.END,
                    values=(item_str, brand, part_no, origin, notes, f"₱{price:.2f}")
                )

    def sort_column(self, col):
        if col in ("part_no", "notes"):
            return

        ascending = self.sort_direction[col] != "asc"
        self.sort_direction[col] = "asc" if ascending else "desc"

        data = [(self.prod_tree.set(child, col), child) for child in self.prod_tree.get_children()]

        if col == "item":
            def size_key(val):
                try:
                    size_str = val[0].split(" ")[1]
                    parts = size_str.split("-")
                    return tuple(parse_measurement(p) for p in parts)
                except:
                    return (0, 0, 0)
            data.sort(key=lambda x: size_key(x), reverse=not ascending)
        elif col == "price":
            data.sort(key=lambda x: float(x[0].replace("₱", "").replace(",", "")), reverse=not ascending)
        else:
            data.sort(key=lambda x: x[0].lower(), reverse=not ascending)

        for index, (_, child) in enumerate(data):
            self.prod_tree.move(child, '', index)

        for c, h in zip(self.prod_tree["columns"], self.headers):
            arrow = " ↑" if c == col and ascending else " ↓" if c == col else ""
            self.prod_tree.heading(c, text=h + arrow)