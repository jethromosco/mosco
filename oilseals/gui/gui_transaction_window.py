import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
from customtkinter import CTkImage
from typing import Any, Dict
import os
from datetime import datetime
from home_page import ICON_PATH

from ..ui.transaction_window import (
    load_transactions_records,
    get_thresholds,
    get_location_and_notes,
    update_location,
    update_price,
    update_notes,
    update_thresholds,
    summarize_running_stock,
    calculate_current_stock,
    get_stock_color,
    format_price_display,
    parse_price_input,
    validate_price_input,
    create_header_text,
    create_subtitle_text,
    get_transaction_tag,
    is_photo_upload_allowed,
    get_photo_path_by_type,
    validate_image_file,
    create_safe_filename,
    compress_and_save_image,
    delete_old_images,
    calculate_image_display_size,
    create_thumbnail_size,
    get_photos_directory,
)
from theme import theme


class TransactionWindow(ctk.CTkFrame):
    def __init__(self, parent, details: Dict[str, Any], controller, return_to):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.return_to = return_to
        self.main_app = None

        # Initialize data
        self.details = details
        
        # Initialize UI variables
        self.srp_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.edit_mode = False
        self.image_path = ""
        self.image_thumbnail = None

        # Build UI
        self._build_ui()
        
        # Subscribe to theme changes
        theme.subscribe(self.apply_theme)

    def _build_ui(self):
        self._create_header_section()
        self._create_main_content()
        self._create_history_section()

    # ------------------------------------------------------------------
    # Header section that mirrors gui_mm.py (fixed positions)
    # ------------------------------------------------------------------
    def _create_header_section(self):
        """
        Header with Back-Button, MOSCO logo, Admin-Button
        Uses the same absolute-position logic as gui_mm.py
        so nothing moves when the window changes.
        """
        self.header_frame = ctk.CTkFrame(self, fg_color=theme.get("bg"), height=140)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 0))
        self.header_frame.pack_propagate(False)

        # Back Button – top-left, 40 px margin
        self.back_btn = ctk.CTkButton(
            self.header_frame,
            text="← Back",
            font=("Poppins", 20, "bold"),
            fg_color=theme.get("primary"),
            hover_color=theme.get("primary_hover"),
            text_color="#FFFFFF",
            corner_radius=40,
            width=120,
            height=50,
            command=self._handle_back_button,
        )
        self.back_btn.place(x=40, y=40)

        # Admin Button – top-right, 40 px margin
        self.admin_btn = ctk.CTkButton(
            self.header_frame,
            text="Admin",
            font=("Poppins", 18, "bold"),
            width=100,
            height=50,
            corner_radius=25,
            fg_color=theme.get("primary"),
            hover_color=theme.get("primary_hover"),
            text_color="#FFFFFF",
            command=self.open_admin_panel,
        )
        # Initial x position (window width - margin)
        initial_width = self.winfo_toplevel().winfo_width() or 1280
        self.admin_btn.place(x=initial_width-140, y=45)

        # MOSCO logo frame – centered horizontally between buttons
        self.logo_frame = ctk.CTkFrame(self.header_frame, fg_color=theme.get("bg"))
        self.logo_frame.place(y=10)  # vertical position 20px from top

        # Load logo images with fallback
        try:
            self.logo_img1 = ctk.CTkImage(Image.open(f"{ICON_PATH}\\mosco logo.png"), size=(120, 120))
            self.logo_img_text = ctk.CTkImage(
                light_image=Image.open(f"{ICON_PATH}\\mosco text light.png"),
                dark_image=Image.open(f"{ICON_PATH}\\mosco text.png"),
                size=(420, 120)
            )
        except Exception as e:
            print(f"Error loading logo images: {e}")
            self.logo_img1 = None
            self.logo_img_text = None

        def create_logo_section():
            for widget in self.logo_frame.winfo_children():
                widget.destroy()
            if self.logo_img1 and self.logo_img_text:
                lbl1 = ctk.CTkLabel(self.logo_frame, image=self.logo_img1, text="", bg_color=theme.get("bg"))
                lbl1.pack(side="left", padx=(0, 5))
                lbl2 = ctk.CTkLabel(self.logo_frame, image=self.logo_img_text, text="", bg_color=theme.get("bg"))
                lbl2.pack(side="left")
            else:
                lbl = ctk.CTkLabel(self.logo_frame, text="MOSCO", font=("Hero", 36, "bold"), text_color=theme.get("text"))
                lbl.pack()

        create_logo_section()

        # Center logo_frame horizontally by after idle call to get header width
        def center_logo(event=None):
            header_width = self.header_frame.winfo_width()
            logo_width = 120 + 420 + 5  # same as InventoryApp
            x = (header_width - logo_width) // 2
            self.logo_frame.place(x=x, y=20)

        self.header_frame.bind("<Configure>", center_logo)
        self.after(10, center_logo)

    # ------------------------------------------------------------------
    # Admin / Password helpers (same as InventoryApp)
    # ------------------------------------------------------------------
    def open_admin_panel(self):
        """Open admin panel after password validation (identical to InventoryApp)."""
        def on_password_result(success):
            if success:
                from .gui_products import AdminPanel
                AdminPanel(
                    self.controller.root,
                    self,
                    self.controller,
                    on_close_callback=lambda: None
                )
        self.create_password_window(callback=on_password_result)

    def create_password_window(self, callback=None):
        """Create password input dialog (mirrored from gui_mm.py)."""
        password_window = ctk.CTkToplevel(self.master)
        password_window.title("Admin Access")
        password_window.geometry("450x350")
        password_window.resizable(False, False)
        password_window.configure(fg_color=theme.get("bg"))
        password_window.transient(self.master)
        password_window.grab_set()

        # center on screen
        password_window.update_idletasks()
        scr_w, scr_h = password_window.winfo_screenwidth(), password_window.winfo_screenheight()
        w, h = password_window.winfo_width(), password_window.winfo_height()
        password_window.geometry(f"{w}x{h}+{(scr_w-w)//2}+{(scr_h-h)//2}")

        # content
        main = ctk.CTkFrame(password_window, fg_color=theme.get("card"), corner_radius=40)
        main.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(main, text="Admin Access", font=("Poppins", 28, "bold"),
                     text_color=theme.get("heading_fg")).pack(pady=(40, 10))
        ctk.CTkLabel(main, text="Enter admin password to continue", font=("Poppins", 16),
                     text_color=theme.get("text")).pack(pady=(0, 30))

        entry_holder = ctk.CTkFrame(main, fg_color="transparent")
        entry_holder.pack(pady=(0, 20))
        pwd_var = tk.StringVar()
        pwd_entry = ctk.CTkEntry(entry_holder, textvariable=pwd_var, show="*",
                                 width=280, height=40, corner_radius=20,
                                 fg_color=theme.get("input"),
                                 text_color=theme.get("text"))
        pwd_entry.pack()
        pwd_entry.bind("<Return>", lambda e: self.check_password(pwd_entry, err_lbl, password_window, callback))
        pwd_entry.focus()

        err_lbl = ctk.CTkLabel(entry_holder, text="", font=("Poppins", 12), text_color="#FF4444")
        err_lbl.pack()

        # buttons
        btn_holder = ctk.CTkFrame(main, fg_color="transparent")
        btn_holder.pack(pady=(20, 30))
        ctk.CTkButton(btn_holder, text="Cancel", width=120, height=45, corner_radius=40,
                      fg_color=theme.get("accent_hover"), hover_color=theme.get("accent"),
                      text_color=theme.get("text"),
                      command=lambda: self.close_password_window(password_window, callback, False)).pack(side="left", padx=10)
        ctk.CTkButton(btn_holder, text="Submit", width=120, height=45, corner_radius=40,
                      fg_color=theme.get("primary"), hover_color=theme.get("primary_hover"),
                      text_color="#FFFFFF",
                      command=lambda: self.check_password(pwd_entry, err_lbl, password_window, callback)).pack(side="left", padx=10)

    def check_password(self, entry, err_lbl, win, callback):
        from ..ui.mm import validate_admin_password
        if validate_admin_password(entry.get().strip()):
            self.close_password_window(win, callback, True)
        else:
            err_lbl.configure(text="❌ Incorrect password. Please try again.")
            entry.delete(0, tk.END)
            entry.focus()
            win.after(3000, lambda: err_lbl.configure(text=""))

    def close_password_window(self, window, callback, success):
        window.destroy()
        if callback:
            callback(success)

    # ------------------------------------------------------------------
    # Remaining unchanged code (truncated for brevity)
    # ------------------------------------------------------------------
    def _handle_back_button(self):
        if self.controller and self.return_to:
            self.controller.show_frame(self.return_to)
        else:
            self.master.destroy()

    def _create_main_content(self):
        main_container = ctk.CTkFrame(self, fg_color=theme.get("bg"))
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        combined_section = ctk.CTkFrame(main_container, fg_color=theme.get("card"), corner_radius=40)
        combined_section.pack(fill="x", pady=(0, 10))

        combined_inner = ctk.CTkFrame(combined_section, fg_color="transparent")
        combined_inner.pack(fill="x", padx=20, pady=20)

        self._create_top_section(combined_inner)
        self._create_bottom_section(combined_inner)

    def _create_top_section(self, parent):
        top_grid = ctk.CTkFrame(parent, fg_color="transparent")
        top_grid.pack(fill="x", pady=(0, 10))
        top_grid.grid_columnconfigure(0, weight=0)
        top_grid.grid_columnconfigure(1, weight=1)
        top_grid.grid_columnconfigure(2, weight=0)

        self._create_title_section(top_grid)
        self._create_stock_price_section(top_grid)
        self._create_photo_section(top_grid)

    def _create_title_section(self, parent):
        title_left = ctk.CTkFrame(parent, fg_color="transparent")
        title_left.grid(row=0, column=0, sticky="w")

        self.header_label = ctk.CTkLabel(
            title_left, text="", font=("Poppins", 24, "bold"), text_color=theme.get("text")
        )
        self.header_label.pack(anchor="w")

        self.sub_header_label = ctk.CTkLabel(
            title_left, text="", font=("Poppins", 20, "bold"), text_color=theme.get("muted")
        )
        self.sub_header_label.pack(anchor="w", pady=(5, 0))

    def _create_stock_price_section(self, parent):
        stock_srp_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stock_srp_frame.grid(row=0, column=1)

        self.stock_label = ctk.CTkLabel(
            stock_srp_frame, text="", font=("Poppins", 26, "bold"),
            text_color=theme.get("text"), cursor="hand2"
        )
        self.stock_label.pack(anchor="center")
        self.stock_label.bind("<Button-1>", self.open_stock_settings)

        self.srp_display = ctk.CTkLabel(
            stock_srp_frame, textvariable=self.srp_var, font=("Poppins", 26, "bold"),
            text_color=theme.get("text")
        )
        self.srp_display.pack(anchor="center", pady=(10, 0))

        self.srp_entry = ctk.CTkEntry(
            stock_srp_frame, textvariable=self.srp_var, font=("Poppins", 22, "bold"),
            fg_color=theme.get("input"), text_color=theme.get("text"),
            corner_radius=20, height=44, width=150, justify="center"
        )

    def _create_photo_section(self, parent):
        photo_container = ctk.CTkFrame(parent, fg_color="transparent", width=100, height=100)
        photo_container.grid(row=0, column=2, sticky="e")
        photo_container.grid_propagate(False)

        photo_frame = ctk.CTkFrame(photo_container, width=100, height=100,
                                   fg_color=theme.get("input"), corner_radius=20)
        photo_frame.pack_propagate(False)
        photo_frame.pack(fill="both", expand=True)

        self.photo_label = ctk.CTkLabel(
            photo_frame, text="📷", font=("Poppins", 24),
            text_color=theme.get("muted"), cursor="hand2"
        )
        self.photo_label.pack(fill="both", expand=True)
        self.photo_label.bind("<Button-1>", self.show_photo_menu)

        self.upload_button = ctk.CTkButton(
            photo_container, text="Upload", font=("Poppins", 12, "bold"),
            fg_color=theme.get("accent"), hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"), corner_radius=20, height=30, width=80,
            command=self.upload_photo
        )

    def _create_bottom_section(self, parent):
        bottom_row = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_row.pack(fill="x")
        bottom_row.grid_columnconfigure(0, weight=0)
        bottom_row.grid_columnconfigure(1, weight=1)
        bottom_row.grid_columnconfigure(2, weight=0)

        self._create_location_section(bottom_row)
        self._create_notes_section(bottom_row)
        self._create_edit_section(bottom_row)

    def _create_location_section(self, parent):
        loc_frame = ctk.CTkFrame(parent, fg_color="transparent")
        loc_frame.grid(row=0, column=0, sticky="w", padx=(0, 12))
        ctk.CTkLabel(loc_frame, text="LOCATION", font=("Poppins", 18, "bold"),
                     text_color=theme.get("text")).pack(anchor="w", pady=(0, 5))
        self.location_entry = ctk.CTkEntry(
            loc_frame, textvariable=self.location_var, font=("Poppins", 18),
            fg_color=theme.get("input"), text_color=theme.get("text"),
            corner_radius=20, height=44, width=120, state="readonly"
        )
        self.location_entry.pack()

    def _create_notes_section(self, parent):
        notes_frame = ctk.CTkFrame(parent, fg_color="transparent")
        notes_frame.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ctk.CTkLabel(notes_frame, text="NOTES", font=("Poppins", 18, "bold"),
                     text_color=theme.get("text")).pack(anchor="w", pady=(0, 5))
        self.notes_entry = ctk.CTkEntry(
            notes_frame, textvariable=self.notes_var, font=("Poppins", 18),
            fg_color=theme.get("input"), text_color=theme.get("text"),
            corner_radius=20, height=44, state="readonly"
        )
        self.notes_entry.pack(fill="x")

    def _create_edit_section(self, parent):
        edit_frame = ctk.CTkFrame(parent, fg_color="transparent")
        edit_frame.grid(row=0, column=2, sticky="e")
        self.edit_btn = ctk.CTkButton(
            edit_frame, text="Edit", font=("Poppins", 18, "bold"),
            fg_color="#4B5563", hover_color="#6B7280", text_color="#FFFFFF",
            corner_radius=25, width=120, height=46, command=self.toggle_edit_mode
        )
        self.edit_btn.pack(pady=(20, 0))

    # ------------------------------------------------------------------
    # History / Table / Photo / Edit logic (unchanged)
    # ------------------------------------------------------------------
    def _create_history_section(self):
        main_container = self.winfo_children()[1]
        history_section = ctk.CTkFrame(main_container, fg_color=theme.get("card"), corner_radius=40)
        history_section.pack(fill="both", expand=True)

        table_container = ctk.CTkFrame(history_section, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=30, pady=30)
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        status_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        status_frame.grid_columnconfigure(0, weight=1)
        self.history_status_label = ctk.CTkLabel(
            status_frame, text="Transaction History",
            font=("Poppins", 20, "bold"), text_color="#FFFFFF"
        )
        self.history_status_label.pack(side="right")

        table_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self._setup_treeview_style()
        self._create_history_table(table_frame)

    def _setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Transaction.Treeview",
                        background=theme.get("card_alt"),
                        foreground=theme.get("text"),
                        fieldbackground=theme.get("card_alt"),
                        font=("Poppins", 18),
                        rowheight=40)
        style.configure("Transaction.Treeview.Heading",
                        background=theme.get("heading_bg"),
                        foreground=theme.get("heading_fg"),
                        font=("Poppins", 20, "bold"))
        if theme.mode == "dark":
            style.map("Transaction.Treeview",
                      background=[("selected", "#4A4A4A")],
                      foreground=[("selected", "#FFFFFF")])
        else:
            style.map("Transaction.Treeview",
                      background=[("selected", "#D0D0D0")],
                      foreground=[("selected", "#000000")])
        style.map("Transaction.Treeview.Heading", background=[("active", theme.get("accent_hover"))])
        style.configure(
            "Red.Vertical.TScrollbar",
            background=theme.get("primary"),
            troughcolor=theme.get("scroll_trough"),
            bordercolor=theme.get("scroll_trough"),
            lightcolor=theme.get("primary"),
            darkcolor=theme.get("primary"),
            arrowcolor="#FFFFFF",
            focuscolor="none"
        )
        style.map(
            "Red.Vertical.TScrollbar",
            background=[("active", theme.get("primary_hover"))],
            lightcolor=[("active", theme.get("primary_hover"))],
            darkcolor=[("active", theme.get("primary_hover"))]
        )

    def _create_history_table(self, parent):
        columns = ("date", "qty_restock", "cost", "name", "qty", "price", "stock")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", style="Transaction.Treeview")
        if theme.mode == "light":
            red, blue, green = "#B22222", "#1E40AF", "#166534"
        else:
            red, blue, green = "#EF4444", "#3B82F6", "#22C55E"
        self.tree.tag_configure("red", foreground=red, font=("Poppins", 18))
        self.tree.tag_configure("blue", foreground=blue, font=("Poppins", 18))
        self.tree.tag_configure("green", foreground=green, font=("Poppins", 18))

        cfg = {
            "date": {"text": "DATE", "anchor": "center", "width": 90},
            "qty_restock": {"text": "QTY RESTOCK", "anchor": "center", "width": 100},
            "cost": {"text": "COST", "anchor": "center", "width": 80},
            "name": {"text": "NAME", "anchor": "w", "width": 200},
            "qty": {"text": "QTY SOLD", "anchor": "center", "width": 80},
            "price": {"text": "PRICE", "anchor": "center", "width": 80},
            "stock": {"text": "STOCK", "anchor": "center", "width": 80},
        }
        for col in columns:
            self.tree.heading(col, text=cfg[col]["text"])
            self.tree.column(col, anchor=cfg[col]["anchor"], width=cfg[col]["width"])

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        parent.bind("<Button-1>", lambda e: self.tree.selection_remove(self.tree.selection()))
        self.tree.bind("<Button-1>", self._on_tree_click)

    def _on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        else:
            self.tree.selection_remove(self.tree.selection())
        return "break"

    # ------------------------------------------------------------------
    # Set data / edit / photo / etc. (unchanged)
    # ------------------------------------------------------------------
    def set_details(self, details: Dict[str, Any], main_app):
        self.details = details
        self.main_app = main_app
        self.srp_var.set(format_price_display(details['price']))
        self.image_path = get_photo_path_by_type(self.details)
        self._load_location()
        self._load_transactions()
        self.load_photo()

    def _load_transactions(self):
        rows = load_transactions_records(self.details)
        self.header_label.configure(text=create_header_text(self.details))
        self.sub_header_label.configure(text=create_subtitle_text(self.details))
        self.tree.delete(*self.tree.get_children())
        summarized = summarize_running_stock(rows)
        summarized.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%y"), reverse=True)
        for vals in summarized:
            tag = get_transaction_tag(vals[1], vals[5])
            self.tree.insert("", "end", values=vals, tags=(tag,))
        self._update_stock_display(rows)

    def _update_stock_display(self, rows):
        low, warn = get_thresholds(self.details)
        stock = calculate_current_stock(rows)
        color = get_stock_color(stock, low, warn)
        self.stock_label.configure(text=f"STOCK: {stock}", text_color=color)

    def _load_location(self):
        location, notes = get_location_and_notes(self.details)
        self.location_var.set(location)
        self.notes_var.set(notes)

    def toggle_edit_mode(self):
        if not self.edit_mode:
            self._enter_edit_mode()
        else:
            self._exit_edit_mode()
        self.edit_mode = not self.edit_mode

    def _enter_edit_mode(self):
        self.location_entry.configure(state="normal")
        self.notes_entry.configure(state="normal")
        self.srp_display.pack_forget()
        self.srp_entry.pack(anchor="center")
        current_price = self.srp_var.get().replace("₱", "").strip()
        self.srp_var.set(current_price)
        self.edit_btn.configure(text="Save", fg_color="#22C55E", hover_color="#16A34A")

    def _exit_edit_mode(self):
        self.save_location()
        self.save_srp()
        self.save_notes()
        self.location_entry.configure(state="readonly")
        self.notes_entry.configure(state="readonly")
        self.srp_entry.pack_forget()
        self.srp_display.pack(anchor="center", pady=(10, 0))
        self.edit_btn.configure(text="Edit", fg_color="#4B5563", hover_color="#6B7280")

    def save_location(self):
        update_location(self.details, self.location_var.get())
        if self.main_app:
            self.main_app.refresh_product_list()

    def save_srp(self):
        if not validate_price_input(self.srp_var.get()):
            messagebox.showerror("Error", "Invalid price")
            return
        try:
            new_price = parse_price_input(self.srp_var.get())
            self.srp_var.set(format_price_display(new_price))
            update_price(self.details, new_price)
            if self.main_app:
                self.main_app.refresh_product_list()
        except Exception:
            messagebox.showerror("Error", "Invalid price format")

    def save_notes(self):
        update_notes(self.details, self.notes_var.get())
        if self.main_app:
            self.main_app.refresh_product_list()

    # ------------------------------------------------------------------
    # Stock settings window
    # ------------------------------------------------------------------
    def open_stock_settings(self, event=None):
        settings = self._create_settings_window()
        self._populate_settings_form(settings)

    def _create_settings_window(self):
        settings = ctk.CTkToplevel(self)
        settings.title("Stock Color Settings")
        settings.geometry("400x300")
        settings.resizable(False, False)
        settings.configure(fg_color=theme.get("bg"))
        settings.transient(self)
        settings.grab_set()
        settings.update_idletasks()
        w, h = settings.winfo_width(), settings.winfo_height()
        sw, sh = settings.winfo_screenwidth(), settings.winfo_screenheight()
        settings.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        return settings

    def _populate_settings_form(self, settings_window):
        main_frame = ctk.CTkFrame(settings_window, fg_color=theme.get("card"), corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(main_frame, text="Stock Threshold Settings",
                     font=("Poppins", 20, "bold"), text_color=theme.get("text")).pack(pady=(30, 20))
        form = ctk.CTkFrame(main_frame, fg_color="transparent")
        form.pack(fill="x", padx=30, pady=(0, 20))

        low_var, warn_var = tk.StringVar(), tk.StringVar()
        low, warn = get_thresholds(self.details)
        low_var.set(str(low))
        warn_var.set(str(warn))

        for lbl, var, txt in [("RESTOCK NEEDED (Red)", low_var, "low"),
                              ("LOW ON STOCK (Orange)", warn_var, "warn")]:
            ctk.CTkLabel(form, text=lbl, font=("Poppins", 14, "bold"),
                         text_color=theme.get("text")).pack(anchor="w", pady=(0, 5))
            ent = ctk.CTkEntry(form, textvariable=var, font=("Poppins", 12),
                               fg_color=theme.get("input"), text_color=theme.get("text"),
                               corner_radius=20, height=35)
            ent.pack(fill="x", pady=(0, 15))
            ent.bind("<Return>", lambda e: self._save_thresholds(settings_window, low_var.get(), warn_var.get()))

        btn_holder = ctk.CTkFrame(form, fg_color="transparent")
        btn_holder.pack(fill="x")
        ctk.CTkButton(btn_holder, text="Cancel", width=100, height=40, corner_radius=25,
                      fg_color=theme.get("accent_hover"), hover_color=theme.get("accent"),
                      text_color=theme.get("text"), command=settings_window.destroy).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_holder, text="Save", width=100, height=40, corner_radius=25,
                      fg_color="#22C55E", hover_color="#16A34A", text_color="#FFFFFF",
                      command=lambda: self._save_thresholds(settings_window, low_var.get(), warn_var.get())).pack(side="right")

    def _save_thresholds(self, settings_window, low_str, warn_str):
        try:
            low, warn = int(low_str), int(warn_str)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integer values.")
            return
        update_thresholds(self.details, low, warn)
        settings_window.destroy()
        self._load_transactions()

    # ------------------------------------------------------------------
    # Photo upload / viewer
    # ------------------------------------------------------------------
    def upload_photo(self):
        if not is_photo_upload_allowed(self.details):
            messagebox.showinfo("Not Allowed", "Photo upload is only allowed for MOS brand products.")
            return
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if not validate_image_file(file_path):
            if file_path:
                messagebox.showerror("Invalid File", "Only .jpg, .jpeg, .png are supported.")
            return
        self._process_photo_upload(file_path)

    def _process_photo_upload(self, file_path):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            filename = create_safe_filename(self.details, ext)
            photos_dir = get_photos_directory()
            save_path = os.path.join(photos_dir, filename)

            if not compress_and_save_image(file_path, save_path):
                messagebox.showerror("Error", "Failed to process image.")
                return
            delete_old_images(self.details)
            self.image_path = save_path
            self.load_photo()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload photo: {e}")

    def load_photo(self):
        self.image_path = get_photo_path_by_type(self.details)
        if os.path.exists(self.image_path):
            self._display_photo_thumbnail()
        else:
            self._display_photo_placeholder()

    def _display_photo_thumbnail(self):
        try:
            img = Image.open(self.image_path)
            img.thumbnail((80, 80))
            ctk_img = CTkImage(light_image=img, size=img.size)
            self.image_thumbnail = ctk_img
            self.photo_label.configure(image=ctk_img, text="")
            self.upload_button.pack_forget()
        except Exception:
            self._display_photo_placeholder()

    def _display_photo_placeholder(self):
        self.photo_label.configure(image=None, text="📷")
        if is_photo_upload_allowed(self.details):
            self.upload_button.pack(pady=(5, 0))
        else:
            self.upload_button.pack_forget()

    def show_photo_menu(self, event=None):
        if not os.path.exists(self.image_path):
            if not is_photo_upload_allowed(self.details):
                self.show_fullscreen_photo()
            return
        if not is_photo_upload_allowed(self.details):
            self.show_fullscreen_photo()
            return
        self._create_photo_menu()

    def _create_photo_menu(self):
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(fg_color=theme.get("card"))
        x = self.photo_label.winfo_rootx() + self.photo_label.winfo_width() // 2 - 60
        y = self.photo_label.winfo_rooty() + self.photo_label.winfo_height() + 5
        popup.geometry(f"120x80+{x}+{y}")

        def close(event=None):
            if popup and popup.winfo_exists():
                popup.destroy()

        def view():
            close()
            self.show_fullscreen_photo()

        ctk.CTkButton(popup, text="🔍 View", font=("Poppins", 12),
                      fg_color=theme.get("accent"), hover_color=theme.get("accent_hover"),
                      text_color=theme.get("text"), corner_radius=15, height=30,
                      command=view).pack(padx=5, pady=(5, 2))

        if is_photo_upload_allowed(self.details):
            def delete():
                close()
                if messagebox.askyesno("Delete Photo", "Are you sure you want to delete this photo?"):
                    os.remove(self.image_path)
                    self.load_photo()
            ctk.CTkButton(popup, text="🗑 Delete", font=("Poppins", 12),
                          fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
                          corner_radius=15, height=30, command=delete).pack(padx=5, pady=(2, 5))
        popup.bind("<FocusOut>", lambda e: close())
        popup.focus_set()

    def show_fullscreen_photo(self):
        if not os.path.exists(self.image_path):
            return
        photo_viewer = self._create_photo_viewer_window()
        self._display_fullscreen_image(photo_viewer)

    def _create_photo_viewer_window(self):
        pv = ctk.CTkToplevel(self)
        pv.title("Photo Viewer")
        pv.transient(self)
        pv.grab_set()
        pv.configure(fg_color=theme.get("bg"))
        sw, sh = pv.winfo_screenwidth(), pv.winfo_screenheight()
        ww, wh = int(sw * 0.8), int(sh * 0.8)
        pv.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
        return pv

    def _display_fullscreen_image(self, pv):
        container = ctk.CTkFrame(pv, fg_color=theme.get("bg"))
        container.pack(fill="both", expand=True, padx=20, pady=20)
        img = Image.open(self.image_path)
        label = ctk.CTkLabel(container, text="", cursor="hand2")
        label.pack(fill="both", expand=True)

        def resize(evt):
            dw, dh = evt.width, evt.height
            scale = min(dw / img.width, dh / img.height)
            nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            ctk_img = CTkImage(light_image=resized, size=(nw, nh))
            label.configure(image=ctk_img)
            label.image = ctk_img
        container.bind("<Configure>", resize)
        label.bind("<Button-1>", lambda e: pv.destroy())
        container.update_idletasks()
        resize(type("Evt", (), {"width": container.winfo_width(), "height": container.winfo_height()})())
        ctk.CTkLabel(container, text="Click image or press ESC to close",
                     font=("Poppins", 12), text_color="#CCCCCC").pack()
        ctk.CTkButton(container, text="Close", font=("Poppins", 12, "bold"),
                      fg_color="#D00000", hover_color="#B71C1C", text_color="#FFFFFF",
                      corner_radius=20, width=100, height=30,
                      command=pv.destroy).pack(pady=(10, 0))
        pv.bind("<Escape>", lambda e: pv.destroy())
        pv.focus_set()

    # ------------------------------------------------------------------
    # Theme apply (unchanged)
    # ------------------------------------------------------------------
    def destroy(self):
        theme.unsubscribe(self.apply_theme)
        super().destroy()

    def apply_theme(self):
        try:
            if not self.winfo_exists():
                return
            self._setup_treeview_style()
            self.configure(fg_color=theme.get("bg"))
            for w in self.winfo_children():
                if isinstance(w, ctk.CTkFrame):
                    if w.cget("fg_color") == "transparent":
                        continue
                    if w.winfo_y() < 150:
                        w.configure(fg_color=theme.get("bg"))
                    else:
                        for c in w.winfo_children():
                            if isinstance(c, ctk.CTkFrame) and c.cget("fg_color") != "transparent":
                                c.configure(fg_color=theme.get("card"))
            for attr in ("header_label", "sub_header_label", "srp_display", "photo_label"):
                if hasattr(self, attr):
                    getattr(self, attr).configure(text_color=theme.get("text" if attr != "sub_header_label" else "muted"))
            if hasattr(self, "stock_label") and hasattr(self, "details") and self.details:
                self._update_stock_display(load_transactions_records(self.details))
            for en in ("srp_entry", "location_entry", "notes_entry"):
                if hasattr(self, en):
                    getattr(self, en).configure(fg_color=theme.get("input"), text_color=theme.get("text"))
            for btn in ("back_btn", "admin_btn"):
                if hasattr(self, btn):
                    getattr(self, btn).configure(
                        fg_color=theme.get("primary"),
                        hover_color=theme.get("primary_hover"),
                        text_color="#FFFFFF"
                    )
            if hasattr(self, "upload_button"):
                self.upload_button.configure(
                    fg_color=theme.get("accent"),
                    hover_color=theme.get("accent_hover"),
                    text_color=theme.get("text")
                )
            if hasattr(self, "tree"):
                for child in self.tree.get_children():
                    tags = self.tree.item(child)["tags"]
                    self.tree.item(child, tags=tags)
        except Exception as e:
            print(f"Error applying theme to transaction window: {e}")