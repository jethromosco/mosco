import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from .gui_trans_aed import TransactionFormHandler
from ..admin.transactions import TransactionsLogic, parse_date, parse_date_db, format_currency
from theme import theme


class TransactionTab:
    """GUI class for managing transaction display and user interactions."""

    FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price"]

    def __init__(self, notebook, main_app, controller, on_refresh_callback=None):
        self.main_app = main_app
        self.controller = controller
        self.on_refresh_callback = on_refresh_callback

        # Initialize logic handler
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
        )
        self.form_handler._get_record_by_id = self._get_record_by_id

        self.setup_buttons()
        self.refresh_transactions()

    # ─────────────── controls (search, filters, date) ───────────────
    def setup_controls(self):
        """Create search and filter controls."""
        controls_section = ctk.CTkFrame(self.frame, fg_color=theme.get("card"), corner_radius=40, height=90)
        controls_section.pack(fill="x", padx=20, pady=(20, 15))
        controls_section.pack_propagate(False)

        controls_inner = ctk.CTkFrame(controls_section, fg_color="transparent")
        controls_inner.pack(fill="x", padx=20, pady=15)

        # Single row: Search + Date + All Dates + Filter
        row = ctk.CTkFrame(controls_inner, fg_color="transparent")
        row.pack(fill="x")

        # Search label
        search_label = ctk.CTkLabel(row, text="Search:", font=("Poppins", 14, "bold"), text_color=theme.get("text"))
        search_label.pack(side="left", padx=(0, 10))

        # Search
        self.tran_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            row, textvariable=self.tran_search_var,
            font=("Poppins", 13), fg_color=theme.get("input"), text_color=theme.get("text"),
            corner_radius=20, height=35, border_width=1, border_color=theme.get("border"),
            placeholder_text="Enter search term...", width=260
        )
        search_entry.pack(side="left")
        self.tran_search_var.trace_add("write", lambda *args: self.refresh_transactions())

        # Hover + Focus effects (mirroring gui_mm.py)
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

        # Spacer
        ctk.CTkLabel(row, text=" ", fg_color="transparent").pack(side="left", padx=10)

        # Date label
        date_label = ctk.CTkLabel(row, text="Date:", font=("Poppins", 14, "bold"), text_color=theme.get("text"))
        date_label.pack(side="left", padx=(10, 10))

        # Date
        self.date_var = tk.StringVar()
        date_frame = ctk.CTkFrame(row, fg_color=theme.get("input"), corner_radius=20, height=35)
        date_frame.pack(side="left")
        date_frame.pack_propagate(False)

        # Allow typing into the DateEntry (state normal) so users can type mm/dd/yy
        self.date_filter = DateEntry(
            date_frame, date_pattern="mm/dd/yy", width=12,
            showweeknumbers=False, textvariable=self.date_var, state="normal",
            background='#2b2b2b', foreground='#FFFFFF', borderwidth=0, relief='flat'
        )
        self.date_filter.pack(expand=True, padx=5, pady=2)
        self.date_var.set("")
        self.date_filter.bind('<<DateEntrySelected>>', self.on_date_selected)

        # When typing, only apply filter if the current string is a valid MM/DD/YY date.
        def _on_date_keyrelease(event=None):
            s = self.date_var.get().strip()
            if s == "":
                # treat empty as cleared
                self.on_date_selected()
                return
            try:
                datetime.strptime(s, "%m/%d/%y")
                # valid date string -> apply filter
                self.on_date_selected()
            except Exception:
                # partial/invalid input: do not trigger the filter yet
                pass

        try:
            self.date_filter.bind('<KeyRelease>', _on_date_keyrelease)
        except Exception:
            pass

        # Bind hover/focus to date container after creation (visual only)
        def on_frame_hover(frame, is_enter):
            if is_enter:
                frame.configure(fg_color=theme.get("accent"))
            else:
                frame.configure(fg_color=theme.get("input"))

        date_frame.bind("<Enter>", lambda e: on_frame_hover(date_frame, True))
        date_frame.bind("<Leave>", lambda e: on_frame_hover(date_frame, False))

        # All Dates
        self.clear_btn = ctk.CTkButton(
            row, text="All Dates", font=("Poppins", 13, "bold"),
            fg_color=theme.get("bg"), hover_color=theme.get("card_alt"), text_color=theme.get("text"),
            corner_radius=20, width=110, height=35, command=self.clear_date_filter
        )
        self.clear_btn.pack(side="left", padx=10)

        # Transaction count label (shows number of filtered transactions)
        self.count_label = ctk.CTkLabel(row, text="Total: 0", font=("Poppins", 14, "bold"), text_color=theme.get("muted"))
        self.count_label.pack(side="right", padx=(10, 0))

        # Filter label
        filter_label = ctk.CTkLabel(row, text="Filter:", font=("Poppins", 14, "bold"), text_color=theme.get("text"))
        filter_label.pack(side="left", padx=(10, 10))

        # Filter
        self.restock_filter = tk.StringVar(value="All")
        restock_combo = ctk.CTkComboBox(
            row, variable=self.restock_filter,
            values=["All", "Restock", "Sale", "Actual", "Fabrication"],
            font=("Poppins", 13), dropdown_font=("Poppins", 12),
            fg_color=theme.get("input"), text_color=theme.get("text"),
            dropdown_fg_color=theme.get("card"), dropdown_text_color=theme.get("text"),
            button_color=theme.get("accent"), button_hover_color=theme.get("accent_hover"),
            border_color=theme.get("border"), corner_radius=20, width=160, height=35, state="readonly"
        )
        restock_combo.pack(side="left", padx=(0, 0))
        self.restock_filter.trace_add("write", lambda *args: self.refresh_transactions())

        # Hover/focus binds for combo (visual only)
        def on_combo_hover(is_enter):
            try:
                restock_combo.configure(fg_color=theme.get("accent") if is_enter else theme.get("input"))
            except Exception:
                pass
        restock_combo.bind("<Enter>", lambda e: on_combo_hover(True))
        restock_combo.bind("<Leave>", lambda e: on_combo_hover(False))

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
        # Set selected background to grey and keep text color unchanged on selection
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
            red_color = "#B22222"   # Dark red
            blue_color = "#1E40AF"  # Dark blue
            green_color = "#166534" # Dark green
        else:
            red_color = "#EF4444"   # Brighter red in dark mode
            blue_color = "#3B82F6"  # Brighter blue in dark mode
            green_color = "#22C55E" # Brighter green in dark mode

        self.tran_tree.tag_configure("red", foreground=red_color)
        self.tran_tree.tag_configure("blue", foreground=blue_color)
        self.tran_tree.tag_configure("green", foreground=green_color)
        self.tran_tree.tag_configure("gray", foreground="#9CA3AF")

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
            # If multiple selection, use the first selected
            sel = self.tran_tree.selection()
            if not sel:
                return
            # Take the first item id (rowid)
            try:
                rowid = int(sel[0])
            except Exception:
                return self.form_handler.edit_transaction()
            # Proceed to edit (form handler will handle fabrication pairs)
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
        # Get all transactions from logic
        all_records = self.logic.get_all_transactions()

        # Identify fabrication pairs (based on same date + same product name)
        # `pairs_map` maps a rowid -> (restock_record, sale_record)
        self.fabrication_pairs = self.logic.get_fabrication_pairs(all_records)
        # Derive a set of rowids that are part of fabrication pairs
        self.fabrication_records = set(self.fabrication_pairs.keys())

        # Apply filters
        keyword = self.tran_search_var.get()
        restock_filter = self.restock_filter.get()

        # Date filter
        date_filter = None
        if self.date_filter_active and self.date_var.get().strip():
            try:
                date_filter = parse_date(self.date_var.get().strip()).date()
            except Exception:
                date_filter = None

        # Filter transactions using logic
        self.filtered_records = self.logic.filter_transactions(
            all_records, keyword, restock_filter, date_filter, self.fabrication_records
        )

        # Render the filtered transactions
        self.render_transactions(self.filtered_records)

        # Update transaction count label: count fabrication pairs as one transaction
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
            self.count_label.configure(text=f"Total: {len(display_ids)}")
        except Exception:
            try:
                self.count_label.configure(text=f"Total: {len(self.filtered_records)}")
            except Exception:
                pass

        # Trigger refresh callback if provided
        if self.on_refresh_callback:
            self.on_refresh_callback()

    def _get_record_by_id(self, rowid):
        """Get a transaction record by its rowid."""
        return self.logic.get_transaction_by_id(self.filtered_records, rowid)

    def render_transactions(self, records):
        """Render transactions in the treeview."""
        # Clear existing items
        self.tran_tree.delete(*self.tran_tree.get_children())

        if not records:
            return

        # Calculate running stock using logic for the filtered records (used for normal rows)
        records_with_stock = self.logic.calculate_running_stock(records)

        # Also calculate running stock across ALL transactions so we can lookup
        # stock values for rowids that were removed by fabrication filtering.
        all_records = self.logic.get_all_transactions()
        all_with_stock = self.logic.calculate_running_stock(all_records)
        stock_map_all = {rec.rowid: stock for rec, stock in all_with_stock}

        # Sort the filtered records_with_stock by date (newest first) for display
        records_with_stock.sort(key=lambda x: (x[0].date, x[0].rowid), reverse=True)

        emitted = set()
        pairs_map = getattr(self, 'fabrication_pairs', {}) or {}

        # Add items to treeview (merge fabrication pairs)
        for record, stock in records_with_stock:
            if record.rowid in emitted:
                continue

            # If this record is part of a fabrication pair, render merged row once
            if record.rowid in pairs_map:
                restock_rec, sale_rec = pairs_map[record.rowid]

                # Ensure canonical ordering (restock, sale)
                if restock_rec.is_restock != 1:
                    restock_rec, sale_rec = sale_rec, restock_rec

                # Compute final quantity = restock_qty - sold_qty
                try:
                    restock_qty = int(restock_rec.quantity)
                except Exception:
                    restock_qty = 0
                try:
                    sold_qty = abs(int(sale_rec.quantity))
                except Exception:
                    sold_qty = 0
                final_qty = restock_qty - sold_qty

                # Keep price from sale if present, otherwise restock
                price_val = sale_rec.price if sale_rec.price and sale_rec.price > 0 else restock_rec.price
                price_str = format_currency(price_val) if price_val else ""

                # Build item string
                item_str = f"{restock_rec.type} {restock_rec.id_size}-{restock_rec.od_size}-{restock_rec.th_size}"
                if restock_rec.brand:
                    item_str += f" {restock_rec.brand}"

                formatted_date_obj = parse_date_db(restock_rec.date)
                if formatted_date_obj:
                    formatted_date = formatted_date_obj.strftime("%m/%d/%y")
                else:
                    formatted_date = "Invalid Date"

                # Choose stock after the later of the two records
                later = restock_rec
                try:
                    d1 = parse_date_db(restock_rec.date)
                    d2 = parse_date_db(sale_rec.date)
                    if d2 and d1 and (d2, sale_rec.rowid) > (d1, restock_rec.rowid):
                        later = sale_rec
                except Exception:
                    if sale_rec.rowid > restock_rec.rowid:
                        later = sale_rec

                # Prefer stock from the full history so later.rowid (which may have been
                # filtered out) still returns a meaningful stock-after value.
                stock_after = stock_map_all.get(later.rowid, "")

                # Show Fabricated Qty (restock), Net Qty (cost column), Sold Qty, and preserve Price
                # Treeview columns: (item, date, qty_restock, cost, name, qty, price, stock)
                values = (
                    item_str,
                    formatted_date,
                    restock_qty,
                    "",               # leave cost column empty (do not display Net here)
                    restock_rec.name,
                    sold_qty,
                    price_str,
                    stock_after,
                )
                tag = "gray"

                # Use restock rowid as iid for merged display (keeps deletion/edit flows)
                iid = restock_rec.rowid
                self.tran_tree.insert("", tk.END, iid=iid, values=values, tags=(tag,))

                # Mark both as emitted so we don't render them separately
                emitted.add(restock_rec.rowid)
                emitted.add(sale_rec.rowid)
                continue

            # Not a fabrication pair: render normally
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

        # Toggle sort direction
        self.sort_direction[col] = not self.sort_direction.get(col, False)
        ascending = not self.sort_direction[col]

        # Sort using logic layer
        self.filtered_records = self.logic.sort_transactions(self.filtered_records, col, ascending)

        # Re-render the sorted transactions
        self.render_transactions(self.filtered_records)
