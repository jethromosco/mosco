import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from .gui_trans_aed import TransactionFormHandler
from ..admin.transactions import TransactionsLogic, parse_date


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
        controls_section = ctk.CTkFrame(self.frame, fg_color="#2b2b2b", corner_radius=40, height=90)
        controls_section.pack(fill="x", padx=20, pady=(20, 15))
        controls_section.pack_propagate(False)

        controls_inner = ctk.CTkFrame(controls_section, fg_color="transparent")
        controls_inner.pack(fill="x", padx=20, pady=15)

        # Single row: Search + Date + All Dates + Filter
        row = ctk.CTkFrame(controls_inner, fg_color="transparent")
        row.pack(fill="x")

        # Search
        self.tran_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            row, textvariable=self.tran_search_var,
            font=("Poppins", 13), fg_color="#374151", text_color="#FFFFFF",
            corner_radius=20, height=35, border_width=1, border_color="#4B5563",
            placeholder_text="Search...", width=260
        )
        search_entry.pack(side="left")
        self.tran_search_var.trace_add("write", lambda *args: self.refresh_transactions())

        # Hover + Focus effects (standardized)
        def on_widget_enter(event):
            widget = event.widget
            if hasattr(widget, 'configure') and widget.focus_get() != widget:
                try:
                    widget.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
                except Exception:
                    pass

        def on_widget_leave(event):
            widget = event.widget
            if hasattr(widget, 'configure') and widget.focus_get() != widget:
                try:
                    widget.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
                except Exception:
                    pass

        def on_widget_focus_in(event):
            widget = event.widget
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
                except Exception:
                    pass

        def on_widget_focus_out(event):
            widget = event.widget
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
                except Exception:
                    pass

        search_entry.bind("<Enter>", on_widget_enter)
        search_entry.bind("<Leave>", on_widget_leave)
        search_entry.bind("<FocusIn>", on_widget_focus_in)
        search_entry.bind("<FocusOut>", on_widget_focus_out)

        # Spacer
        ctk.CTkLabel(row, text=" ", fg_color="transparent").pack(side="left", padx=10)

        # Date
        self.date_var = tk.StringVar()
        date_frame = ctk.CTkFrame(row, fg_color="#374151", corner_radius=20, height=35)
        date_frame.pack(side="left")
        date_frame.pack_propagate(False)

        self.date_filter = DateEntry(
            date_frame, date_pattern="mm/dd/yy", width=12,
            showweeknumbers=False, textvariable=self.date_var, state="readonly",
            background='#2b2b2b', foreground='#FFFFFF', borderwidth=0, relief='flat'
        )
        self.date_filter.pack(expand=True, padx=5, pady=2)
        self.date_var.set("")
        self.date_filter.bind('<<DateEntrySelected>>', self.on_date_selected)

        # Bind hover/focus to date container after creation
        date_frame.bind("<Enter>", on_widget_enter)
        date_frame.bind("<Leave>", on_widget_leave)
        date_frame.bind("<FocusIn>", on_widget_focus_in)
        date_frame.bind("<FocusOut>", on_widget_focus_out)

        # All Dates
        self.clear_btn = ctk.CTkButton(
            row, text="All Dates", font=("Poppins", 13, "bold"),
            fg_color="#000000", hover_color="#111111", text_color="#FFFFFF",
            corner_radius=20, width=110, height=35, command=self.clear_date_filter
        )
        self.clear_btn.pack(side="left", padx=10)

        # Filter
        self.restock_filter = tk.StringVar(value="All")
        restock_combo = ctk.CTkComboBox(
            row, variable=self.restock_filter,
            values=["All", "Restock", "Sale", "Actual", "Fabrication"],
            font=("Poppins", 13), dropdown_font=("Poppins", 12),
            fg_color="#374151", text_color="#FFFFFF",
            dropdown_fg_color="#2b2b2b", dropdown_text_color="#FFFFFF",
            button_color="#4B5563", button_hover_color="#6B7280",
            border_color="#4B5563", corner_radius=20, width=160, height=35, state="readonly"
        )
        restock_combo.pack(side="left", padx=(10, 0))
        self.restock_filter.trace_add("write", lambda *args: self.refresh_transactions())

        # Hover/focus binds for combo
        restock_combo.bind("<Enter>", on_widget_enter)
        restock_combo.bind("<Leave>", on_widget_leave)
        restock_combo.bind("<FocusIn>", on_widget_focus_in)
        restock_combo.bind("<FocusOut>", on_widget_focus_out)

    def on_date_selected(self, event=None):
        """Handle date selection."""
        self.frame.after(50, self.apply_date_filter)
        self.frame.after(100, lambda: self.frame.focus_set())

    def apply_date_filter(self):
        """Apply the selected date filter."""
        self.date_filter_active = bool(self.date_var.get().strip())
        self.refresh_transactions()

    def clear_date_filter(self):
        """Clear the date filter."""
        self.date_var.set("")
        self.date_filter_active = False
        self.frame.focus_set()
        self.refresh_transactions()

    # ─────────────── treeview ───────────────
    def setup_treeview(self):
        """Create and configure the transactions treeview."""
        table_container = ctk.CTkFrame(self.frame, fg_color="#2b2b2b", corner_radius=40)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        inner_table = ctk.CTkFrame(table_container, fg_color="transparent")
        inner_table.pack(fill="both", expand=True, padx=20, pady=20)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Transactions.Treeview",
                        background="#2b2b2b", foreground="#FFFFFF",
                        fieldbackground="#2b2b2b", font=("Poppins", 12),
                        rowheight=35)
        style.configure("Transactions.Treeview.Heading",
                        background="#000000", foreground="#D00000",
                        font=("Poppins", 12, "bold"))
        style.map("Transactions.Treeview", background=[("selected", "#374151")])

        self.tran_tree = ttk.Treeview(
            inner_table,
            columns=("item", "date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings", selectmode="extended",
            style="Transactions.Treeview"
        )
        self.tran_tree.tag_configure("red", foreground="#EF4444")
        self.tran_tree.tag_configure("blue", foreground="#3B82F6")
        self.tran_tree.tag_configure("green", foreground="#22C55E")
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
            fg_color="#000000", hover_color="#111111", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.add_transaction
        )
        add_btn.pack(side="left", padx=(0, 10))

        edit_btn = ctk.CTkButton(
            button_container, text="Edit", font=("Poppins", 16, "bold"),
            fg_color="#000000", hover_color="#111111", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.edit_transaction
        )
        edit_btn.pack(side="left", padx=(0, 10))

        delete_btn = ctk.CTkButton(
            button_container, text="Delete", font=("Poppins", 16, "bold"),
            fg_color="#000000", hover_color="#111111", text_color="#FFFFFF",
            corner_radius=25, width=100, height=45,
            command=self.form_handler.delete_transaction
        )
        delete_btn.pack(side="left")

        # Keyboard shortcuts
        root = self.frame.winfo_toplevel()
        root.bind("<Control-a>", lambda e: self.form_handler.add_transaction())
        root.bind("<Control-e>", lambda e: self.form_handler.edit_transaction())
        root.bind("<Delete>", lambda e: self.form_handler.delete_transaction())

    # ─────────────── transaction logic / refresh / rendering ───────────────
    def refresh_transactions(self):
        """Refresh the transaction display using logic layer."""
        # Get all transactions from logic
        all_records = self.logic.get_all_transactions()
        
        # Identify fabrication records
        self.fabrication_records = self.logic.identify_fabrication_records(all_records)
        
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
        
        # Calculate running stock using logic
        records_with_stock = self.logic.calculate_running_stock(records)
        
        # Sort by date (newest first) for display
        records_with_stock.sort(key=lambda x: (x[0].date, x[0].rowid), reverse=True)
        
        # Add items to treeview
        for record, stock in records_with_stock:
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