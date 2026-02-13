import tkinter as tk
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk
from tkcalendar import DateEntry

from theme import theme
from .gui_trans_aed import TransactionFormHandler
from ..admin.transactions import TransactionsLogic, parse_date, parse_date_db, format_currency


class TransactionTab:
    """GUI class for managing transaction display and user interactions."""

    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price"]

    def __init__(self, notebook, main_app, controller, on_refresh_callback=None, logic=None):
        self.main_app = main_app
        self.controller = controller
        self.on_refresh_callback = on_refresh_callback

        # CRITICAL FIX: Allow injecting TransactionsLogic from dynamically selected category
        # This ensures transactions tab uses correct database when category dropdown changes
        if logic is not None:
            self.logic = logic
        else:
            # Fallback to default local module import
            self.logic = TransactionsLogic()

        # Support both ttk.Notebook and CTkFrame container
        if hasattr(notebook, "add"):
            self.frame = ctk.CTkFrame(notebook, fg_color="transparent")
            notebook.add(self.frame, text="Transactions")
        else:
            self.frame = notebook

        # Expose a back-reference so form handlers can obtain tab-level state
        try:
            self.frame._transaction_tab_ref = self
        except Exception:
            pass

        self.sort_direction = {}
        self.filtered_records = []
        self.fabrication_records = set()
        self.date_filter_active = False

        self.setup_controls()
        self.setup_treeview()

        # Initialize form handler with logic reference
        self.form_handler = TransactionFormHandler(
            parent_frame=self.frame,
            treeview=self.tran_tree,
            on_refresh_callback=self.refresh_transactions,
            controller=self.controller
        )
        self.form_handler._get_record_by_id = self._get_record_by_id

        self.setup_buttons()
        self.refresh_transactions()

    # ─────────────── controls (search, filters, date) ───────────────
    def setup_controls(self):
        """Create search and filter controls in one card matching the selector style."""
        # Single card container matching admin panel selector
        controls_card = ctk.CTkFrame(self.frame, fg_color=theme.get("card"), corner_radius=40)
        controls_card.pack(fill="x", pady=(0, 10), padx=20)
        
        # Inner content with reduced padding
        card_inner = ctk.CTkFrame(controls_card, fg_color="transparent")
        card_inner.pack(fill="both", expand=True, padx=20, pady=12)
        
        # Centered container for all controls
        controls_container = ctk.CTkFrame(card_inner, fg_color="transparent")
        controls_container.pack(fill="x", expand=True)
        controls_container.grid_columnconfigure(0, weight=1)  # Left spacer
        controls_container.grid_columnconfigure(1, weight=0, minsize=150)  # Search
        controls_container.grid_columnconfigure(2, weight=0, minsize=20)  # Spacing
        controls_container.grid_columnconfigure(3, weight=0, minsize=120)  # Date
        controls_container.grid_columnconfigure(4, weight=0, minsize=20)  # Spacing
        controls_container.grid_columnconfigure(5, weight=0, minsize=110)  # All Dates button
        controls_container.grid_columnconfigure(6, weight=0, minsize=20)  # Spacing
        controls_container.grid_columnconfigure(7, weight=0, minsize=160)  # Filter
        controls_container.grid_columnconfigure(8, weight=0, minsize=20)  # Spacing
        controls_container.grid_columnconfigure(9, weight=0, minsize=100)  # Total count
        controls_container.grid_columnconfigure(10, weight=1)  # Right spacer

        # Search field (FIRST - on the left)
        search_label = ctk.CTkLabel(
            controls_container,
            text="Search",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        search_label.grid(row=0, column=1, sticky="ew", pady=(0, 4))

        self.tran_search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            controls_container,
            textvariable=self.tran_search_var,
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
        self.tran_search_var.trace_add("write", lambda *args: self.refresh_transactions())

        # Date selector
        date_label = ctk.CTkLabel(
            controls_container,
            text="Date",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        date_label.grid(row=0, column=3, sticky="ew", pady=(0, 4))

        # Date picker container with matching style
        self.date_var = tk.StringVar()
        date_container = ctk.CTkFrame(
            controls_container,
            fg_color=theme.get("input"),
            corner_radius=40,
            height=40,
            border_width=1,
            border_color=theme.get("border")
        )
        date_container.grid(row=1, column=3, sticky="ew")
        date_container.grid_propagate(False)

        self.date_filter = DateEntry(
            date_container, 
            date_pattern="mm/dd/yy", 
            width=10,
            showweeknumbers=False, 
            textvariable=self.date_var, 
            state="normal",
            background='#2b2b2b', 
            foreground='#FFFFFF', 
            borderwidth=0, 
            relief='flat'
        )
        self.date_filter.pack(expand=True, fill="both", padx=8, pady=5)
        self.date_var.set("")
        self.date_filter.bind('<<DateEntrySelected>>', self.on_date_selected)

        # When typing, only apply filter if the current string is a valid MM/DD/YY date
        def _on_date_keyrelease(event=None):
            s = self.date_var.get().strip()
            if s == "":
                self.on_date_selected()
                return
            try:
                datetime.strptime(s, "%m/%d/%y")
                self.on_date_selected()
            except Exception:
                pass

        try:
            self.date_filter.bind('<KeyRelease>', _on_date_keyrelease)
        except Exception:
            pass

        # Hover effect for date container
        date_container.bind("<Enter>", lambda e: self._on_date_hover(date_container, True))
        date_container.bind("<Leave>", lambda e: self._on_date_hover(date_container, False))

        # All Dates button
        all_dates_label = ctk.CTkLabel(
            controls_container,
            text="",  # Empty label for spacing
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        all_dates_label.grid(row=0, column=5, sticky="ew", pady=(0, 4))

        self.clear_btn = ctk.CTkButton(
            controls_container,
            text="All Dates",
            font=("Poppins", 14, "bold"),
            fg_color=theme.get("primary"),
            hover_color=theme.get("primary_hover"),
            text_color="#FFFFFF",
            corner_radius=20,
            height=40,
            width=110,
            command=self.clear_date_filter
        )
        self.clear_btn.grid(row=1, column=5, sticky="ew")

        # Filter dropdown
        filter_label = ctk.CTkLabel(
            controls_container,
            text="Filter",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        filter_label.grid(row=0, column=7, sticky="ew", pady=(0, 4))

        self.restock_filter = tk.StringVar(value="All")
        self.filter_combo = ctk.CTkComboBox(
            controls_container,
            variable=self.restock_filter,
            values=["All", "Restock", "Sale", "Actual", "Fabrication"],
            state="readonly",
            width=160,
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
        self.filter_combo.grid(row=1, column=7, sticky="ew")
        self.filter_combo.bind("<Enter>", lambda e: self._on_combo_hover(self.filter_combo, True))
        self.filter_combo.bind("<Leave>", lambda e: self._on_combo_hover(self.filter_combo, False))
        self.restock_filter.trace_add("write", lambda *args: self.refresh_transactions())

        # Total count label
        total_label = ctk.CTkLabel(
            controls_container,
            text="Total",
            font=("Poppins", 14, "bold"),
            text_color=theme.get("text")
        )
        total_label.grid(row=0, column=9, sticky="ew", pady=(0, 4))

        self.count_label = ctk.CTkLabel(
            controls_container,
            text="0",
            font=("Poppins", 20, "bold"),
            text_color=theme.get("primary"),
            fg_color=theme.get("input"),
            corner_radius=20,
            height=40
        )
        self.count_label.grid(row=1, column=9, sticky="ew", padx=5)

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

    def _on_combo_hover(self, combo, is_enter):
        """Handle combo box hover effects"""
        if is_enter:
            combo.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("accent"))
        else:
            combo.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

    def _on_date_hover(self, container, is_enter):
        """Handle date container hover effects"""
        if is_enter:
            container.configure(border_color=theme.get("primary"), border_width=2, fg_color=theme.get("accent"))
        else:
            container.configure(border_color=theme.get("border"), border_width=1, fg_color=theme.get("input"))

    def on_date_selected(self, event=None):
        """Handle date selection."""
        self.frame.after(50, self.apply_date_filter)
        def _safe_focus_frame():
            try:
                if self.frame and getattr(self.frame, 'winfo_exists', lambda: False)() and self.frame.winfo_exists():
                    self.frame.focus_set()
            except Exception:
                pass
        self.frame.after(100, _safe_focus_frame)

    def apply_date_filter(self):
        """Apply the selected date filter."""
        self.date_filter_active = bool(self.date_var.get().strip())
        self.refresh_transactions()

    def clear_date_filter(self):
        """Clear the date filter."""
        self.date_var.set("")
        self.date_filter_active = False
        try:
            if self.frame and getattr(self.frame, 'winfo_exists', lambda: False)() and self.frame.winfo_exists():
                self.frame.focus_set()
        except Exception:
            pass
        self.refresh_transactions()

    # ─────────────── treeview ───────────────
    def setup_treeview(self):
        """Create and configure the transactions treeview."""
        table_container = ctk.CTkFrame(self.frame, fg_color=theme.get("card"), corner_radius=40)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        inner_table = ctk.CTkFrame(table_container, fg_color="transparent")
        inner_table.pack(fill="both", expand=True, padx=20, pady=20)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Transactions.Treeview",
                        background=theme.get("card_alt"),
                        foreground=theme.get("text"),
                        fieldbackground=theme.get("card_alt"),
                        font=("Poppins", 12),
                        rowheight=35)

        style.configure("Transactions.Treeview.Heading",
                        background=theme.get("heading_bg"), foreground=theme.get("heading_fg"),
                        font=("Poppins", 12, "bold"))
        style.map("Transactions.Treeview",
                background=[("selected", theme.get("table_selected"))],
                foreground=[("selected", theme.get("text"))])

        self.tran_tree = ttk.Treeview(
            inner_table,
            columns=("item", "date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings", selectmode="extended",
            style="Transactions.Treeview"
        )

        # Set darker colors in light mode
        if theme.mode == "light":
            red_color = "#B22222"
            blue_color = "#1E40AF"
            green_color = "#16A34A"
            gray_color = "#000000"
        else:
            red_color = "#EF4444"
            blue_color = "#3B82F6"
            green_color = "#22C55E"
            gray_color = "#9CA3AF"

        self.tran_tree.tag_configure("red", foreground=red_color)
        self.tran_tree.tag_configure("blue", foreground=blue_color)
        self.tran_tree.tag_configure("green", foreground=green_color)
        self.tran_tree.tag_configure("gray", foreground=gray_color)

        column_config = {
            "item": {"anchor": "center", "width": 180},
            "date": {"anchor": "center", "width": 90},
            "qty_restock": {"anchor": "center", "width": 60},
            "cost": {"anchor": "center", "width": 80},
            "name": {"anchor": "w", "width": 160},
            "qty": {"anchor": "center", "width": 60},
            "price": {"anchor": "center", "width": 80},
            "stock": {"anchor": "center", "width": 80},
        }
        for col in self.tran_tree["columns"]:
            header = col.upper().replace("_", " ")
            self.tran_tree.heading(col, text=header, command=lambda c=col: self.sort_by_column(c))
            self.tran_tree.column(col, **column_config[col])

        scrollbar = ttk.Scrollbar(inner_table, orient="vertical", command=self.tran_tree.yview)
        self.tran_tree.configure(yscrollcommand=scrollbar.set)
        self.tran_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ─────────────── buttons (Add / Edit / Delete) ───────────────
    def setup_buttons(self):
        """Create action buttons."""
        buttons_section = ctk.CTkFrame(self.frame, fg_color="transparent")
        buttons_section.pack(fill="x", pady=(0, 20))

        button_container = ctk.CTkFrame(buttons_section, fg_color="transparent")
        button_container.pack(anchor="center")

        add_btn = ctk.CTkButton(
            button_container, text="Add", font=("Poppins", 16, "bold"),
            fg_color="#22C55E", hover_color="#16A34A", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.add_transaction
        )
        add_btn.pack(side="left", padx=(0, 10))

        def _on_edit_requested(event=None):
            sel = self.tran_tree.selection()
            if not sel:
                return
            try:
                rowid = int(sel[0])
            except Exception:
                return self.form_handler.edit_transaction()
            return self.form_handler.edit_transaction()

        edit_btn = ctk.CTkButton(
            button_container, text="Edit", font=("Poppins", 16, "bold"),
            fg_color="#4B5563", hover_color="#6B7280", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=_on_edit_requested
        )
        edit_btn.pack(side="left", padx=(0, 10))

        delete_btn = ctk.CTkButton(
            button_container, text="Delete", font=("Poppins", 16, "bold"),
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.delete_transaction
        )
        delete_btn.pack(side="left")

        # Keyboard shortcuts
        root = self.frame.winfo_toplevel()
        root.bind("<Control-Key-1>", lambda e: self.form_handler.add_transaction())
        root.bind("<Delete>", lambda e: self.form_handler.delete_transaction())

    # ─────────────── transaction logic / refresh / rendering ───────────────
    def refresh_transactions(self):
        """Refresh the transaction display using logic layer."""
        all_records = self.logic.get_all_transactions()
        self.fabrication_pairs = self.logic.get_fabrication_pairs(all_records)
        self.fabrication_records = set((self.fabrication_pairs or {}).keys())

        keyword = self.tran_search_var.get()
        restock_filter = self.restock_filter.get()

        date_filter = None
        if self.date_filter_active and self.date_var.get().strip():
            try:
                date_filter = parse_date(self.date_var.get().strip()).date()
            except Exception:
                date_filter = None

        self.filtered_records = self.logic.filter_transactions(
            all_records, keyword, restock_filter, date_filter, self.fabrication_records
        )

        self.render_transactions(self.filtered_records)

        try:
            pairs_map = getattr(self, 'fabrication_pairs', {}) or {}
            display_ids = set()
            for rec in self.filtered_records:
                if rec.rowid in pairs_map:
                    restock_rec, sale_rec = pairs_map[rec.rowid]
                    canonical = min(restock_rec.rowid, sale_rec.rowid)
                    display_ids.add(('p', canonical))
                else:
                    display_ids.add(('s', rec.rowid))
            self.count_label.configure(text=f"{len(display_ids)}")
        except Exception:
            try:
                self.count_label.configure(text=f"{len(self.filtered_records)}")
            except Exception:
                pass

        if self.on_refresh_callback:
            self.on_refresh_callback()

    def _get_record_by_id(self, rowid):
        """Get a transaction record by its rowid."""
        return self.logic.get_transaction_by_id(self.filtered_records, rowid)

    def render_transactions(self, records):
        """Render transactions in the treeview."""
        self.tran_tree.delete(*self.tran_tree.get_children())

        if not records:
            return

        records_with_stock = self.logic.calculate_running_stock(records)
        all_records = self.logic.get_all_transactions()
        all_with_stock = self.logic.calculate_running_stock(all_records)
        stock_map_all = {rec.rowid: stock for rec, stock in all_with_stock}

        records_with_stock.sort(key=lambda x: (x[0].date, x[0].rowid), reverse=True)

        emitted = set()
        pairs_map = getattr(self, 'fabrication_pairs', {}) or {}

        for record, stock in records_with_stock:
            if record.rowid in emitted:
                continue

            if record.rowid in pairs_map:
                restock_rec, sale_rec = pairs_map[record.rowid]

                if restock_rec.is_restock != 1:
                    restock_rec, sale_rec = sale_rec, restock_rec

                try:
                    restock_qty = int(restock_rec.quantity)
                except Exception:
                    restock_qty = 0
                try:
                    sold_qty = abs(int(sale_rec.quantity))
                except Exception:
                    sold_qty = 0
                final_qty = restock_qty - sold_qty

                price_val = sale_rec.price if sale_rec.price and sale_rec.price > 0 else restock_rec.price
                price_str = format_currency(price_val) if price_val else ""

                item_str = f"{restock_rec.type} {restock_rec.id_size}-{restock_rec.od_size}-{restock_rec.th_size}"
                if restock_rec.brand:
                    item_str += f" {restock_rec.brand}"

                formatted_date_obj = parse_date_db(restock_rec.date)
                if formatted_date_obj:
                    formatted_date = formatted_date_obj.strftime("%m/%d/%y")
                else:
                    formatted_date = "Invalid Date"

                later = restock_rec
                try:
                    d1 = parse_date_db(restock_rec.date)
                    d2 = parse_date_db(sale_rec.date)
                    if d2 and d1 and (d2, sale_rec.rowid) > (d1, restock_rec.rowid):
                        later = sale_rec
                except Exception:
                    if sale_rec.rowid > restock_rec.rowid:
                        later = sale_rec

                stock_after = stock_map_all.get(later.rowid, "")

                values = (
                    item_str,
                    formatted_date,
                    restock_qty,
                    "",
                    restock_rec.name,
                    sold_qty,
                    price_str,
                    stock_after,
                )
                tag = "gray"

                iid = restock_rec.rowid
                self.tran_tree.insert("", tk.END, iid=iid, values=values, tags=(tag,))

                emitted.add(restock_rec.rowid)
                emitted.add(sale_rec.rowid)
                continue

            display_data = self.logic.format_transaction_for_display(record, stock)
            self.tran_tree.insert("", tk.END,
                                  iid=display_data['rowid'],
                                  values=display_data['values'],
                                  tags=(display_data['tag'],)
                                  )

    def sort_by_column(self, col):
        """Sort transactions by the specified column."""
        if not self.filtered_records:
            return

        self.sort_direction[col] = not self.sort_direction.get(col, False)
        ascending = not self.sort_direction[col]

        self.filtered_records = self.logic.sort_transactions(self.filtered_records, col, ascending)
        self.render_transactions(self.filtered_records)
