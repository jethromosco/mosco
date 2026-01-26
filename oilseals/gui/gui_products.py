import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from ..admin.products import ProductsLogic
import importlib
from theme import theme
from home_page import categories
from .gui_transactions import TransactionTab
from .gui_prod_aed import ProductFormHandler


class AdminPanel:
    """Minimal AdminPanel with Category->Sub-category->Unit selector.

    This implementation delegates selection handling to `controller.set_inventory_context`.
    It avoids top-level imports that caused circular issues and keeps the UI minimal
    so InventoryApp modules can be loaded by the controller.
    """

    def __init__(self, parent, main_app, controller, on_close_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_close_callback = on_close_callback
        self.products_logic = ProductsLogic()

        self.win = ctk.CTkToplevel(parent)
        self.win.title("MOS Inventory")
        self.win.configure(fg_color=theme.get("bg"))
        try:
            self.win.minsize(900, 600)
        except Exception:
            pass

        self.main_container = ctk.CTkFrame(self.win, fg_color=theme.get("bg"))
        self.main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. CREATE TAB BUTTONS FIRST (at the top)
        self._create_tab_header(self.main_container)

        # 2. CREATE SELECTOR SECTION (below tabs)
        self._create_admin_selector(self.main_container)

        # 3. CREATE TAB CONTENT AREA (below selectors)
        self.tab_content = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=40)
        self.tab_content.pack(fill="both", expand=True, padx=0, pady=(10, 0))

        self.products_frame = ctk.CTkFrame(self.tab_content, fg_color="transparent")
        self.transactions_frame = ctk.CTkFrame(self.tab_content, fg_color="transparent")

        self.create_products_tab()
        self.create_transactions_tab()

        self.switch_tab("products")

        self.win.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Show window
        self.win.deiconify()

        # Configure minimum usable size to avoid too-small layouts
        try:
            self.win.minsize(1000, 700)
        except Exception:
            pass

        # Bind to minimize/unmap to implement custom shrink-and-center behavior
        self.win.bind("<Unmap>", self._on_unmap_minimize)

        # Subscribe to theme changes to update colors dynamically
        theme.subscribe(self.update_colors)

        # Add keyboard shortcut bindings
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

    def _create_tab_header(self, parent):
        """Create tab header buttons at the top"""
        tab_header = ctk.CTkFrame(parent, fg_color="transparent", height=60)
        tab_header.pack(fill="x", pady=(0, 10))  # Reduced bottom padding
        tab_header.pack_propagate(False)

        tab_buttons_frame = ctk.CTkFrame(tab_header, fg_color="transparent")
        tab_buttons_frame.pack(fill="x", expand=True, pady=8)

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
            text_color="#FFFFFF",
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

    def _create_admin_selector(self, parent):
        """Create selector section with search inline"""
        # Outer card container
        selector_card = ctk.CTkFrame(parent, fg_color=theme.get("card"), corner_radius=40)
        selector_card.pack(fill="x", pady=(0, 10), padx=20)
        
        # Inner content with reduced padding
        card_inner = ctk.CTkFrame(selector_card, fg_color="transparent")
        card_inner.pack(fill="both", expand=True, padx=20, pady=12)
        
        # Centered container for all selector controls
        selector_container = ctk.CTkFrame(card_inner, fg_color="transparent")
        selector_container.pack(fill="x", expand=True)
        selector_container.grid_columnconfigure(0, weight=1)  # Left spacer
        selector_container.grid_columnconfigure(1, weight=0, minsize=150)  # Search
        selector_container.grid_columnconfigure(2, weight=0, minsize=20)  # Spacing
        selector_container.grid_columnconfigure(3, weight=0, minsize=150)  # Category
        selector_container.grid_columnconfigure(4, weight=0, minsize=20)  # Spacing
        selector_container.grid_columnconfigure(5, weight=0, minsize=140)  # Subcategory
        selector_container.grid_columnconfigure(6, weight=0, minsize=20)  # Spacing
        selector_container.grid_columnconfigure(7, weight=0, minsize=120)  # Unit
        selector_container.grid_columnconfigure(8, weight=0, minsize=20)  # Spacing
        selector_container.grid_columnconfigure(9, weight=0, minsize=100)  # Button
        selector_container.grid_columnconfigure(10, weight=1)  # Right spacer

        # Search field (FIRST - on the left)
        search_label = ctk.CTkLabel(
            selector_container,
            text="Search",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        search_label.grid(row=0, column=1, sticky="ew", pady=(0, 4))

        self.prod_search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            selector_container,
            textvariable=self.prod_search_var,
            font=("Poppins", 14),
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            corner_radius=40,
            height=40,
            border_width=1,
            border_color=theme.get("border"),
            placeholder_text="Search..."
        )
        self.search_entry.grid(row=1, column=1, sticky="ew")
        self.search_entry.bind("<Enter>", lambda e: self._on_entry_hover(self.search_entry, True))
        self.search_entry.bind("<Leave>", lambda e: self._on_entry_hover(self.search_entry, False))
        self.search_entry.bind("<FocusIn>", lambda e: self._on_entry_focus(self.search_entry, True))
        self.search_entry.bind("<FocusOut>", lambda e: self._on_entry_focus(self.search_entry, False))

        # Category selector
        cat_label = ctk.CTkLabel(
            selector_container,
            text="Category",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        cat_label.grid(row=0, column=3, sticky="ew", pady=(0, 4))

        self._cat_var = tk.StringVar()
        cat_vals = list(categories.keys())
        self._cat_menu = ctk.CTkComboBox(
            selector_container,
            variable=self._cat_var,
            values=cat_vals,
            state="readonly",
            width=150,
            height=40,
            fg_color=theme.get("input"),
            button_color=theme.get("accent"),
            button_hover_color=theme.get("accent_hover"),
            dropdown_fg_color=theme.get("card"),
            dropdown_text_color=theme.get("text"),
            dropdown_hover_color=theme.get("combo_hover"),
            text_color=theme.get("text"),
            font=("Poppins", 14),
            corner_radius=40,
            border_width=1,
            border_color=theme.get("border"),
            command=self._on_category_change
        )
        self._cat_menu.grid(row=1, column=3, sticky="ew")  # ← FIXED! Changed from column=1 to column=3
        self._cat_menu.bind("<Enter>", lambda e: self._on_combo_hover(self._cat_menu, True))
        self._cat_menu.bind("<Leave>", lambda e: self._on_combo_hover(self._cat_menu, False))

    # Subcategory selector
        sub_label = ctk.CTkLabel(
            selector_container,
            text="Sub-category",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        sub_label.grid(row=0, column=5, sticky="ew", pady=(0, 4))

        self._sub_var = tk.StringVar()
        self._sub_menu = ctk.CTkComboBox(
            selector_container,
            variable=self._sub_var,
            values=["-"],
            state="readonly",
            width=140,
            height=40,
            fg_color=theme.get("input"),
            button_color=theme.get("accent"),
            button_hover_color=theme.get("accent_hover"),
            dropdown_fg_color=theme.get("card"),
            dropdown_text_color=theme.get("text"),
            dropdown_hover_color=theme.get("combo_hover"),
            text_color=theme.get("text"),
            font=("Poppins", 14),
            corner_radius=40,
            border_width=1,
            border_color=theme.get("border"),
            command=self._on_subcategory_change
        )
        self._sub_menu.grid(row=1, column=5, sticky="ew")
        self._sub_menu.bind("<Enter>", lambda e: self._on_combo_hover(self._sub_menu, True))
        self._sub_menu.bind("<Leave>", lambda e: self._on_combo_hover(self._sub_menu, False))

    # Unit selector
        unit_label = ctk.CTkLabel(
            selector_container,
            text="Unit",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        unit_label.grid(row=0, column=7, sticky="ew", pady=(0, 4))

        self._unit_var = tk.StringVar()
        self._unit_menu = ctk.CTkComboBox(
            selector_container,
            variable=self._unit_var,
            values=["-"],
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
            font=("Poppins", 14),
            corner_radius=40,
            border_width=1,
            border_color=theme.get("border")
        )
        self._unit_menu.grid(row=1, column=7, sticky="ew")
        self._unit_menu.bind("<Enter>", lambda e: self._on_combo_hover(self._unit_menu, True))
        self._unit_menu.bind("<Leave>", lambda e: self._on_combo_hover(self._unit_menu, False))

        # Select button
        open_btn = ctk.CTkButton(
            selector_container,
            text="Select",
            command=self._apply_selection,
            font=("Poppins", 14, "bold"),
            fg_color=theme.get("primary"),
            hover_color=theme.get("primary_hover"),
            height=40,
            corner_radius=20,
            width=100
        )
        open_btn.grid(row=1, column=9, sticky="ew")

        self.prod_search_var.trace_add("write", lambda *args: self.refresh_products())

        if cat_vals:
            self._cat_var.set(cat_vals[0])
            # populate sub/unit for default selection
            try:
                self._on_category_change(cat_vals[0])
            except Exception:
                pass

    def _on_combo_hover(self, combo, is_enter):
        """Handle combo box hover effects matching mm.py"""
        if is_enter:
            combo.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("accent"))
        else:
            combo.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

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
            entry.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("input_focus") if theme.get("input_focus") else theme.get("input"))
        else:
            entry.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

    def _on_category_change(self, value):
        try:
            cat_value = categories.get(value)
            if isinstance(cat_value, dict) and any(k in ("MM", "INCH", "VS", "VA", "VL") for k in cat_value.keys()):
                units = list(cat_value.keys())
                try:
                    self._sub_menu.configure(values=["-"])
                except Exception:
                    pass
                self._sub_var.set("-")
                try:
                    self._unit_menu.configure(values=units)
                    if units:
                        self._unit_var.set(units[0])
                except Exception:
                    pass
            elif isinstance(cat_value, dict):
                subcats = list(cat_value.keys())
                try:
                    self._sub_menu.configure(values=subcats)
                    self._sub_var.set(subcats[0] if subcats else "-")
                except Exception:
                    pass
                first = subcats[0] if subcats else None
                if first and isinstance(cat_value.get(first), dict):
                    units = list(cat_value[first].keys())
                    try:
                        self._unit_menu.configure(values=units if units else ["-"])
                        self._unit_var.set(units[0] if units else "-")
                    except Exception:
                        pass
                else:
                    try:
                        self._unit_menu.configure(values=["-"])
                        self._unit_var.set("-")
                    except Exception:
                        pass
            else:
                try:
                    self._sub_menu.configure(values=["-"])
                    self._unit_menu.configure(values=["-"])
                    self._sub_var.set("-")
                    self._unit_var.set("-")
                except Exception:
                    pass
        except Exception:
            pass

    def _on_subcategory_change(self, value):
        try:
            cat = self._cat_var.get()
            cat_value = categories.get(cat)
            if isinstance(cat_value, dict) and value and value != "-":
                sub_val = cat_value.get(value)
                if isinstance(sub_val, dict):
                    units = list(sub_val.keys())
                    try:
                        self._unit_menu.configure(values=units if units else ["-"])
                        self._unit_var.set(units[0] if units else "-")
                    except Exception:
                        pass
                else:
                    try:
                        self._unit_menu.configure(values=["-"])
                        self._unit_var.set("-")
                    except Exception:
                        pass
        except Exception:
            pass


    def _apply_selection(self):
        cat = self._cat_var.get()
        sub = self._sub_var.get() if hasattr(self, '_sub_var') else None
        unit = self._unit_var.get() if hasattr(self, '_unit_var') else None
        sub_norm = None if not sub or sub == '-' else sub
        unit_norm = None if not unit or unit == '-' else unit
        try:
            if self.controller:
                self.controller.set_inventory_context(cat, sub_norm, unit_norm)
        except Exception:
            pass  # Don't show error - controller already handles unknown categories

        # Determine target database module and patch admin modules so logic uses correct DB
        try:
            ac = importlib.import_module('app_controller')
            base_folder = getattr(ac, 'CATEGORY_FOLDER_MAP', {}).get(cat)
        except Exception:
            base_folder = None

        if not base_folder:
            # If mapping not found, try to match by key
            try:
                ac = importlib.import_module('app_controller')
                mapping = getattr(ac, 'CATEGORY_FOLDER_MAP', {})
                for k, v in mapping.items():
                    if k and k.lower() in (cat or '').lower():
                        base_folder = v
                        break
            except Exception:
                base_folder = None

        if not base_folder:
            # Category not available for admin - show Coming Soon
            self._show_coming_soon(cat, "Category not yet available")
            return

        db_module = None
        tried = []
        try:
            if base_folder == 'packingseals' and sub_norm and sub_norm != '-':
                sub_folder = sub_norm.replace(' ', '').lower()
                tried.append(f"{base_folder}.{sub_folder}.database")
                db_module = importlib.import_module(f"{base_folder}.{sub_folder}.database")
            if db_module is None:
                tried.append(f"{base_folder}.database")
                db_module = importlib.import_module(f"{base_folder}.database")
        except ModuleNotFoundError:
            # Database module not found - show Coming Soon instead of keeping old data
            unit_display = f" ({unit_norm})" if unit_norm else ""
            inventory_display = f"{cat} {sub_norm or ''}".strip()
            if unit_display:
                inventory_display += unit_display
            self._show_coming_soon(inventory_display, "Database not yet available")
            return

        connect_fn = getattr(db_module, 'connect_db', None)
        if not connect_fn:
            # No database support - show Coming Soon
            self._show_coming_soon(cat, "Admin not yet available")
            return

        # CRITICAL: Hide Coming Soon overlay and show tables
        self._hide_coming_soon()

        # Patch admin and ui modules so their connect_db points to selected DB
        target_modules = [
            f"{base_folder}.admin.products",
            f"{base_folder}.admin.transactions",
            f"{base_folder}.admin.prod_aed",
            f"{base_folder}.admin.trans_aed",
            f"{base_folder}.ui.transaction_window",
        ]
        # Also ensure oilseals modules are consistent when switching
        if base_folder != 'oilseals':
            target_modules += [
                'oilseals.admin.products',
                'oilseals.admin.transactions',
                'oilseals.admin.prod_aed',
                'oilseals.admin.trans_aed',
                'oilseals.ui.transaction_window',
            ]
        
        # Also patch monoseals modules if switching from another module
        if base_folder != 'packingseals':
            target_modules += [
                'packingseals.monoseals.admin.products',
                'packingseals.monoseals.admin.transactions',
                'packingseals.monoseals.admin.prod_aed',
                'packingseals.monoseals.admin.trans_aed',
                'packingseals.monoseals.ui.transaction_window',
            ]

        for mod_name in target_modules:
            try:
                m = importlib.import_module(mod_name)
                setattr(m, 'connect_db', connect_fn)
            except Exception:
                pass

        # Recreate logic objects so they pick up new connect_db, then refresh UI
        try:
            # Import TransactionsLogic from the SELECTED category, not the current admin panel's module
            if base_folder == 'packingseals' and sub_norm and sub_norm != '-':
                trans_module = importlib.import_module(f"{base_folder}.{sub_norm.replace(' ', '').lower()}.admin.transactions")
            else:
                trans_module = importlib.import_module(f"{base_folder}.admin.transactions")
            
            TransactionsLogic = getattr(trans_module, 'TransactionsLogic', None)
            
            # Recreate products logic with new connection
            self.products_logic = ProductsLogic()
            
            # Recreate form handler with new connection (CRITICAL FIX)
            if hasattr(self, 'prod_form_handler'):
                self.prod_form_handler = ProductFormHandler(
                    self.win,
                    None,
                    self.refresh_products
                )
                # Re-attach treeview to form handler
                if hasattr(self, 'prod_tree'):
                    self.prod_form_handler.prod_tree = self.prod_tree
                # CRITICAL: Re-attach the product-added callback after recreation
                self.prod_form_handler.on_product_added = self._handle_product_added
            
            # Recreate transaction logic and tab (CRITICAL: fully reinitialize)
            if hasattr(self, 'transaction_tab') and getattr(self, 'transaction_tab'):
                # CRITICAL: Clear old transaction tab's widgets (but keep frame alive)
                try:
                    if hasattr(self.transaction_tab, 'frame') and self.transaction_tab.frame is not None:
                        # Destroy all widgets in the frame (recursive)
                        for widget in list(self.transaction_tab.frame.winfo_children()):
                            try:
                                widget.destroy()
                            except Exception:
                                pass
                except Exception:
                    pass
                
                # Recreate transaction tab with fresh connection (same frame reference)
                try:
                    self.transaction_tab = TransactionTab(
                        notebook=self.transaction_tab.frame,
                        main_app=self.main_app,
                        controller=self.controller,
                        on_refresh_callback=self.refresh_all_tabs
                    )
                except Exception:
                    # If recreation fails, at least the frame still exists
                    self.transaction_tab = None
            else:
                # Create fresh transaction tab if none exists
                if TransactionsLogic:
                    self.transaction_tab = TransactionTab(
                        notebook=self.transactions_frame,
                        main_app=self.main_app,
                        controller=self.controller,
                        on_refresh_callback=self.refresh_all_tabs
                    )
            
            # Refresh both tables
            try:
                # Clear search filter when switching inventories
                self.prod_search_var.set("")
                self.refresh_products()
            except Exception:
                pass
        except Exception:
            pass

    def _show_coming_soon(self, inventory_name, reason):
        """Show Coming Soon overlay on top of admin tables - CRITICAL FOR SAFETY."""
        try:
            # CRITICAL: Clear transaction tab widgets but keep frame alive
            if hasattr(self, 'transaction_tab') and self.transaction_tab is not None:
                try:
                    if hasattr(self.transaction_tab, 'frame') and self.transaction_tab.frame is not None:
                        # Destroy all widgets in the transaction frame (but NOT the frame itself)
                        for widget in list(self.transaction_tab.frame.winfo_children()):
                            try:
                                widget.destroy()
                            except Exception:
                                pass
                except Exception:
                    pass
                self.transaction_tab = None
            
            # Hide tables
            self.products_frame.pack_forget()
            self.transactions_frame.pack_forget()
            
            # SECOND: Clear any existing coming soon frame
            if hasattr(self, 'coming_soon_frame') and self.coming_soon_frame is not None:
                try:
                    self.coming_soon_frame.destroy()
                except Exception:
                    pass
            
            # THIRD: Create a fresh Coming Soon overlay
            self.coming_soon_frame = ctk.CTkFrame(
                self.tab_content, 
                fg_color=theme.get("card"),
                corner_radius=20
            )
            self.coming_soon_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create centered content container
            content_container = ctk.CTkFrame(
                self.coming_soon_frame, 
                fg_color="transparent"
            )
            content_container.pack(fill="both", expand=True, padx=40, pady=60)
            
            # Add spacing above title
            top_spacer = ctk.CTkFrame(content_container, fg_color="transparent", height=20)
            top_spacer.pack(fill="x")
            top_spacer.pack_propagate(False)
            
            # "Coming Soon" title
            title_label = ctk.CTkLabel(
                content_container,
                text="Coming Soon",
                font=("Poppins", 48, "bold"),
                text_color=theme.get("text")
            )
            title_label.pack(pady=(0, 20))
            
            # Inventory name
            inventory_label = ctk.CTkLabel(
                content_container,
                text=inventory_name,
                font=("Poppins", 20),
                text_color=theme.get("text_secondary")
            )
            inventory_label.pack(pady=(0, 10))
            
            # Reason / Description
            reason_label = ctk.CTkLabel(
                content_container,
                text=reason,
                font=("Poppins", 14),
                text_color=theme.get("text_muted")
            )
            reason_label.pack(pady=(0, 30))
            
            # Additional info
            info_label = ctk.CTkLabel(
                content_container,
                text="This inventory is not yet available in the admin panel.",
                font=("Poppins", 12),
                text_color=theme.get("text_muted")
            )
            info_label.pack(pady=(0, 60))
            
            print(f"[Admin] Showing Coming Soon for: {inventory_name} ({reason})")
            
        except Exception as e:
            print(f"[Error] Failed to show Coming Soon: {e}")
            # Fallback: just hide tables
            try:
                self.products_frame.pack_forget()
                self.transactions_frame.pack_forget()
            except Exception:
                pass

    def _hide_coming_soon(self):
        """Hide Coming Soon overlay and show admin tables - CRITICAL FOR DATA INTEGRITY."""
        try:
            # Destroy Coming Soon frame if it exists
            if hasattr(self, 'coming_soon_frame') and self.coming_soon_frame is not None:
                try:
                    self.coming_soon_frame.destroy()
                except Exception:
                    pass
                self.coming_soon_frame = None
            
            # Show the current tab's frame
            if self.current_tab == "products":
                self.products_frame.pack(fill="both", expand=True, padx=0, pady=0)
            else:
                self.transactions_frame.pack(fill="both", expand=True, padx=0, pady=0)
            
            print(f"[Admin] Showing {self.current_tab} tables")
            
        except Exception as e:
            print(f"[Error] Failed to hide Coming Soon: {e}")

    def create_transactions_tab(self):
        self.transaction_tab = TransactionTab(
            notebook=self.transactions_frame,
            main_app=self.main_app,
            controller=self.controller,
            on_refresh_callback=self.refresh_all_tabs
        )

    def switch_tab(self, tab_name):
        """Switch between Products and Transactions tabs.
        
        This is DEFENSIVE: It checks if the transaction_tab exists before
        calling ANY methods on it. This prevents AttributeError crashes
        when switching to Coming Soon or when transactions aren't available.
        """
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

            # DEFENSIVE: Only call refresh if transaction_tab exists AND is not None
            if hasattr(self, 'transaction_tab') and self.transaction_tab is not None:
                try:
                    if hasattr(self.transaction_tab, 'refresh_transactions'):
                        self.transaction_tab.refresh_transactions()
                except Exception as e:
                    print(f"[WARNING] Failed to refresh transactions: {type(e).__name__}: {e}")

        self.current_tab = tab_name

    def refresh_all_tabs(self):
        self.refresh_products()
        if self.on_close_callback:
            self.on_close_callback()

    def on_closing(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.win.destroy()

    def _handle_product_added(self, details):
        """Handle post-product-add workflow: refresh inventory, auto-open transaction."""
        try:
            # CRITICAL FIX 1: Refresh the active GUI (gui_mm.py) immediately
            # so the newly added product appears without delay
            if hasattr(self.main_app, 'refresh_product_list'):
                self.main_app.refresh_product_list()
            
            # CRITICAL FIX 2: Auto-open Add Transaction with pre-filled data
            # DEFENSIVE: Check if transaction_tab exists and has form_handler
            self.switch_tab("transactions")
            self.transactions_frame.update_idletasks()
            
            # Only proceed if transaction_tab is available
            if hasattr(self, 'transaction_tab') and self.transaction_tab is not None:
                if hasattr(self.transaction_tab, 'form_handler') and self.transaction_tab.form_handler is not None:
                    # Prepare keys mapping expected by TransactionFormHandler
                    keys = {
                        'Type': details.get('Type', ''),
                        'ID': details.get('ID', ''),
                        'OD': details.get('OD', ''),
                        'TH': details.get('TH', ''),
                        'Brand': details.get('Brand', ''),
                    }
                    try:
                        # Set last_transaction_keys so transaction form will prefill
                        self.transaction_tab.form_handler.last_transaction_keys = keys
                        # Open Add Transaction form
                        self.transaction_tab.form_handler.add_transaction()
                    except Exception as e:
                        print(f"[WARNING] Failed to auto-open transaction form: {type(e).__name__}")
        except Exception as e:
            print(f"[WARNING] Product add hook failed: {type(e).__name__}")

    def create_products_tab(self):
        self.prod_form_handler = ProductFormHandler(
            self.win,
            None,
            self.refresh_products
        )
        # Attach a post-add hook so that after adding a product we can
        # switch to the Transactions tab and open the Add Transaction form
        self.prod_form_handler.on_product_added = self._handle_product_added

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
        style.map("Products.Treeview.Heading", background=[("active", theme.get("heading_bg")   )])

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