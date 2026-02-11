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
    get_photos_directory,
)
from theme import theme

class TransactionWindow(ctk.CTkFrame):
    def __init__(self, parent, details: Dict[str, Any], controller, return_to):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.return_to = return_to
        self.main_app = None
        self.details = details

        self.srp_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.edit_mode = False
        self.image_path = ""
        self.image_thumbnail = None

        self._build_ui()
        self._setup_bindings()
        theme.subscribe(self.apply_theme)

        self.watermark_label = ctk.CTkLabel(
            self,
            text="developed by jethro · 2025",
            font=("Poppins", 10, "italic"),
            text_color=theme.get("muted"),
            fg_color=None
        )
        self.watermark_label.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=10)
        
    def _detect_category(self) -> str:
        """Detect category name from module path."""
        module_name = self.__class__.__module__
        if 'oilseals' in module_name:
            return 'OIL SEALS'
        elif 'monoseals' in module_name:
            return 'MONOSEALS'
        elif 'wiperseals' in module_name or 'wiper_seals' in module_name:
            return 'WIPER SEALS'
        return 'PRODUCTS'

    def _get_product_type_label(self) -> str:
        """Get category-specific product type label for display."""
        category = self._detect_category()
        if 'MONOSEALS' in category:
            return 'Monoseal'
        elif 'WIPER' in category:
            return 'Wiper Seal'
        return 'Oil Seal'
        
    def _setup_bindings(self):
        self.bind("<Configure>", self._on_window_resize)

    def _on_window_resize(self, event=None):
        if hasattr(self, 'admin_btn') and self.admin_btn.winfo_exists():
            window_width = self.winfo_width()
            if window_width > 1:
                self.admin_btn.place(x=window_width-140, y=40)

        if hasattr(self, 'logo_frame') and self.logo_frame.winfo_exists():
            window_width = self.winfo_width()
            if window_width > 1:
                logo_width = 540
                center_x = (window_width - logo_width) // 2
                self.logo_frame.place(x=center_x, y=20)
        # Update tree columns responsiveness
        try:
            self._adjust_tree_columns()
        except Exception:
            pass
    def _build_ui(self):
        self._create_header_section()
        self._create_main_content()

    def _create_header_section(self):
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
            command=self._open_admin_panel
        )
        self.admin_btn.place(x=1200, y=40)

        self.logo_frame = ctk.CTkFrame(self, fg_color=theme.get("bg"))
        self.logo_frame.place(x=0, y=20)
        self._create_logo_section()

    def _open_admin_panel(self):
        # Minimal implementation to avoid AttributeError
        # Extend as per your existing admin panel code
        from .gui_products import AdminPanel
        if self.controller:
            AdminPanel(self.controller.root, self, self.controller, on_close_callback=lambda: None)

    def _create_password_window(self, callback=None):
        """Create admin access password modal consistent with InventoryApp style"""
        password_window = ctk.CTkToplevel(self.master)
        password_window.title("MOS Inventory")
        password_window.geometry("450x350")
        password_window.resizable(False, False)
        password_window.configure(fg_color=theme.get("bg"))
        password_window.transient(self.master)
        password_window.grab_set()
        
        # Center modal over parent window
        password_window.update_idletasks()
        px = self.master.winfo_rootx()
        py = self.master.winfo_rooty()
        sw = self.master.winfo_width()
        sh = self.master.winfo_height()
        w, h = password_window.winfo_width(), password_window.winfo_height()
        x = px + (sw - w) // 2
        y = py + (sh - h) // 2
        password_window.geometry(f"{w}x{h}+{x}+{y}")
        
        main_frame = ctk.CTkFrame(password_window, fg_color=theme.get("bg"), corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        content_frame = ctk.CTkFrame(
            main_frame, 
            fg_color=theme.get("card"), 
            corner_radius=40, 
            border_width=1, 
            border_color=theme.get("border")
        )
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

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

        def focus_entry(event):
            password_entry.focus()

        password_entry.bind("<Map>", focus_entry)

        def on_enter(event):
            if password_entry.focus_get() != password_entry:
                password_entry.configure(border_color=theme.get("primary"), fg_color=theme.get("accent"))
        
        def on_leave(event):
            if password_entry.focus_get() != password_entry:
                password_entry.configure(border_color=theme.get("border"), fg_color=theme.get("input"))
        
        def on_focus_in(event):
            password_entry.configure(border_color=theme.get("primary"), fg_color=theme.get("input_focus"))
        
        def on_focus_out(event):
            password_entry.configure(border_color=theme.get("border"), fg_color=theme.get("input"))
        
        password_entry.bind("<Enter>", on_enter)
        password_entry.bind("<Leave>", on_leave)
        password_entry.bind("<FocusIn>", on_focus_in)
        password_entry.bind("<FocusOut>", on_focus_out)

        error_label = ctk.CTkLabel(
            entry_container, 
            text="", 
            font=("Poppins", 12), 
            text_color="#FF4444"
        )
        error_label.pack()

        button_container = ctk.CTkFrame(content_frame, fg_color="transparent")
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
            command=lambda: self._close_password_window(password_window, callback, False)
        )
        cancel_btn.pack(side="left", padx=(0, 20))
        
        submit_btn = ctk.CTkButton(
            button_container, 
            text="Submit", 
            font=("Poppins", 16, "bold"), 
            fg_color=theme.get("primary"), 
            hover_color=theme.get("primary_hover"), 
            text_color="#FFFFFF",
            corner_radius=40, 
            width=120, 
            height=45, 
            command=lambda: self._check_password(password_entry, error_label, password_window, callback)
        )
        submit_btn.pack(side="right", padx=(20, 0))

        password_window.bind('<Return>', lambda e: self._check_password(password_entry, error_label, password_window, callback))
        password_window.bind('<Escape>', lambda e: self._close_password_window(password_window, callback, False))
        
        password_entry.focus()


    def _check_password(self, entry, err_lbl, window, callback):
        """Validate admin password, show error or close modal on success"""
        from ..ui.mm import validate_admin_password
        pw = entry.get().strip()
        if validate_admin_password(pw):
            self._close_password_window(window, callback, True)
        else:
            err_lbl.configure(text="❌ Incorrect password. Please try again.")
            entry.delete(0, tk.END)
            entry.focus()
            window.after(3000, lambda: err_lbl.configure(text=""))


    def _close_password_window(self, window, callback, success):
        """Close password modal and notify caller with success boolean"""
        window.destroy()
        if callback:
            callback(success)


    def _open_admin_panel(self):
        """Open admin panel after password validation"""
        def on_password_result(success):
            if success:
                from .gui_products import AdminPanel
                AdminPanel(self.controller.root, self, self.controller, on_close_callback=lambda: None)
        self._create_password_window(callback=on_password_result)



    def _check_password(self, entry, err_lbl, window, callback):
        """Validate admin password, show error or close modal on success"""
        from ..ui.mm import validate_admin_password
        pw = entry.get().strip()
        if validate_admin_password(pw):
            self._close_password_window(window, callback, True)
        else:
            err_lbl.configure(text="❌ Incorrect password. Please try again.")
            entry.delete(0, tk.END)
            entry.focus()
            window.after(3000, lambda: err_lbl.configure(text=""))


    def _close_password_window(self, window, callback, success):
        """Close password modal and notify caller with success boolean"""
        window.destroy()
        if callback:
            callback(success)

    def _open_admin_panel(self):
        """Open admin panel after password validation"""
        def on_password_result(success):
            if success:
                from .gui_products import AdminPanel
                AdminPanel(self.controller.root, self, self.controller, on_close_callback=lambda: None)
        self._create_password_window(callback=on_password_result)

    def _create_logo_section(self):
        for widget in self.logo_frame.winfo_children():
            widget.destroy()

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
            lbl1 = ctk.CTkLabel(self.logo_frame, image=self.logo_img1, text="", bg_color=theme.get("bg"))
            lbl1.pack(side="left", padx=(0, 5))
            lbl2 = ctk.CTkLabel(self.logo_frame, image=self.logo_img_text, text="", bg_color=theme.get("bg"))
            lbl2.pack(side="left")
        except Exception as e:
            print(f"Error loading logo images: {e}")
            title_label = ctk.CTkLabel(self.logo_frame, text="MOSCO",
                                        font=("Hero", 36, "bold"), text_color=theme.get("text"))
            title_label.pack()

    def _handle_back_button(self):
        if self.controller and self.return_to:
            self.controller.show_frame(self.return_to)
        else:
            self.master.destroy()

    def _create_main_content(self):
        self.main_content = ctk.CTkFrame(self, fg_color=theme.get("bg"))
        self.main_content.pack(fill="both", expand=True, pady=(170, 20), padx=20)

        self._create_product_details_section()
        self._create_history_section()

    def _create_product_details_section(self):
        details_section = ctk.CTkFrame(self.main_content, fg_color=theme.get("card"), corner_radius=40)
        details_section.pack(fill="x", pady=(0, 10))

        details_inner = ctk.CTkFrame(details_section, fg_color="transparent")
        details_inner.pack(fill="x", padx=20, pady=20)
        self._create_top_details_section(details_inner)
        self._create_bottom_details_section(details_inner)

    def _create_top_details_section(self, parent):
        top_section = ctk.CTkFrame(parent, fg_color="transparent")
        top_section.pack(fill="x", pady=(0, 20))

        top_section.grid_columnconfigure(0, weight=1)
        top_section.grid_columnconfigure(1, weight=1)
        top_section.grid_columnconfigure(2, weight=1)

        self._create_title_section(top_section)
        self._create_stock_price_section(top_section)
        self._create_photo_section(top_section)

    def _create_title_section(self, parent):
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=(0, 20))

        self.header_label = ctk.CTkLabel(
            title_frame, 
            text="", 
            font=("Poppins", 24, "bold"), 
            text_color=theme.get("text")
        )
        self.header_label.pack(anchor="w")

        self.sub_header_label = ctk.CTkLabel(
            title_frame, 
            text="", 
            font=("Poppins", 20, "bold"), 
            text_color=theme.get("muted")
        )
        self.sub_header_label.pack(anchor="w", pady=(5, 0))

    def _create_stock_price_section(self, parent):
        stock_price_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stock_price_frame.grid(row=0, column=1, sticky="nsew", padx=20)

        self.stock_label = ctk.CTkLabel(
            stock_price_frame, 
            text="", 
            font=("Poppins", 26, "bold"),
            text_color=theme.get("text"), 
            cursor="hand2", 
            anchor="center"
        )
        self.stock_label.pack(anchor="center")
        self.stock_label.bind("<Button-1>", self._open_stock_settings)

        self.srp_display = ctk.CTkLabel(
            stock_price_frame, 
            textvariable=self.srp_var, 
            font=("Poppins", 26, "bold"),
            text_color=theme.get("text"), 
            anchor="center"
        )
        self.srp_display.pack(pady=(10, 0), anchor="center")
        # Right-click price on product card copies formatted product info
        self.srp_display.bind("<Button-3>", lambda e: self._copy_product_info_to_clipboard())

        self.srp_entry = ctk.CTkEntry(
            stock_price_frame, 
            textvariable=self.srp_var, 
            font=("Poppins", 22, "bold"),
            fg_color=theme.get("input"), 
            text_color=theme.get("text"),
            corner_radius=20, 
            height=44, 
            width=150, 
            justify="center"
        )
        # When in edit mode, allow right-click on entry to copy formatted product info
        self.srp_entry.bind("<Button-3>", lambda e: self._copy_product_info_to_clipboard())

    def _create_photo_section(self, parent):
        photo_container = ctk.CTkFrame(parent, fg_color="transparent", width=100, height=100)
        photo_container.grid(row=0, column=2, sticky="e", padx=(20, 0))
        photo_container.pack_propagate(False)

        photo_frame = ctk.CTkFrame(
            photo_container, 
            width=100, 
            height=100,
            fg_color=theme.get("input"), 
            corner_radius=20
        )
        photo_frame.pack_propagate(False)
        photo_frame.pack(fill="both", expand=True)

        self.photo_label = ctk.CTkLabel(
            photo_frame,
            text="📷",
            font=("Poppins", 48),
            text_color=theme.get("muted"),
            cursor="hand2",
            anchor="center"
        )
        self.photo_label.pack(fill="both", expand=True)
        self.photo_label.bind("<Button-1>", self._photo_label_clicked)

    def _photo_label_clicked(self, event=None):
        """Handle clicks on photo label area:
        - If no photo and MOS brand, open upload dialog
        - If photo exists and MOS brand, show context menu
        - If photo exists and not MOS, show fullscreen photo"""
        if not is_photo_upload_allowed(self.details):
            # Not MOS brand, show photo fullscreen if exists
            if os.path.exists(self.image_path):
                self._show_fullscreen_photo()
            # Else do nothing on click
            return

        # MOS brand
        if not os.path.exists(self.image_path):
            # No photo yet, open upload dialog
            self._upload_photo()
        else:
            # Have photo, show context menu
            self._create_photo_context_menu()

    def _display_photo_thumbnail(self):
        """Display photo thumbnail"""
        try:
            img = Image.open(self.image_path)
            img.thumbnail((80, 80), Image.Resampling.LANCZOS)
            ctk_img = CTkImage(light_image=img, size=img.size)
            self.image_thumbnail = ctk_img
            self.photo_label.configure(image=ctk_img, text="")
        except Exception as e:
            print(f"Error loading photo thumbnail: {e}")
            self._display_photo_placeholder()

    def _display_photo_placeholder(self):
        """Display photo placeholder with camera emoji"""
        self.photo_label.configure(image=None, text="📷")

    def _load_photo(self):
        """Load and display photo thumbnail or placeholder"""
        self.image_path = get_photo_path_by_type(self.details)

        if os.path.exists(self.image_path):
            self._display_photo_thumbnail()
        else:
            self._display_photo_placeholder()

    def _create_bottom_details_section(self, parent):
        bottom_section = ctk.CTkFrame(parent, fg_color="transparent")
        bottom_section.pack(fill="x")

        self._create_location_section(bottom_section)
        self._create_notes_section(bottom_section)
        self._create_edit_button_section(bottom_section)

    def _create_location_section(self, parent):
        location_frame = ctk.CTkFrame(parent, fg_color="transparent")
        location_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            location_frame,
            text="LOCATION",
            font=("Poppins", 18, "bold"),
            text_color=theme.get("text")
        ).pack(anchor="w", pady=(0, 5))

        self.location_entry = ctk.CTkEntry(
            location_frame,
            textvariable=self.location_var,
            font=("Poppins", 18),
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=44,
            width=200,#LOCATION WIDTH
            state="readonly"
        )
        self.location_entry.pack()

    def _create_notes_section(self, parent):
        notes_frame = ctk.CTkFrame(parent, fg_color="transparent")
        notes_frame.pack(side="left", fill="x", expand=True, padx=(0, 20))

        ctk.CTkLabel(
            notes_frame,
            text="NOTES",
            font=("Poppins", 18, "bold"),
            text_color=theme.get("text")
        ).pack(anchor="w", pady=(0, 5))

        self.notes_entry = ctk.CTkEntry(
            notes_frame,
            textvariable=self.notes_var,
            font=("Poppins", 18),
            fg_color=theme.get("input"),
            text_color=theme.get("text"),
            corner_radius=20,
            height=44,
            state="readonly"
        )
        self.notes_entry.pack(fill="x")

    def _create_edit_button_section(self, parent):
        edit_frame = ctk.CTkFrame(parent, fg_color="transparent")
        edit_frame.pack(side="right")

        self.edit_btn = ctk.CTkButton(
            edit_frame,
            text="Edit",
            font=("Poppins", 18, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=44,
            command=self._toggle_edit_mode
        )
        self.edit_btn.pack(pady=(33, 0))

    def _create_history_section(self):
        history_section = ctk.CTkFrame(self.main_content, fg_color=theme.get("card"), corner_radius=40)
        history_section.pack(fill="both", expand=True)

        history_inner = ctk.CTkFrame(history_section, fg_color="transparent")
        history_inner.pack(fill="both", expand=True, padx=30, pady=30)

        self.history_status_label = ctk.CTkLabel(
            history_inner,
            text="Transaction History",
            font=("Poppins", 20, "bold"),
            text_color=theme.get("text")
        )
        self.history_status_label.pack(pady=(0, 15))

        self._create_history_table(history_inner)

    def _create_history_table(self, parent):
        self._setup_treeview_style()
        columns = ("date", "qty_restock", "cost", "name", "qty", "price", "stock")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", style="Transaction.Treeview")

        colors = {
            "red": "#B22222" if theme.mode == "light" else "#EF4444",
            "blue": "#1E40AF" if theme.mode == "light" else "#3B82F6",
            "green": "#16A34A" if theme.mode == "light" else "#22C55E",  # Darker green in light mode for Actual
            "gray": "#000000" if theme.mode == "light" else "#9CA3AF",  # Black for Fabrication in light, gray in dark
        }

        for color, value in colors.items():
            self.tree.tag_configure(color, foreground=value, font=("Poppins", 18))

        self.tree.tag_configure("alt_even", background=theme.get("card_alt"))
        self.tree.tag_configure("alt_odd", background=theme.get("card"))

        column_config = {
            "date": {"text": "DATE", "anchor": "center", "width": 90, "minwidth": 50},
            "qty_restock": {"text": "QTY", "anchor": "center", "width": 60, "minwidth": 30},
            "cost": {"text": "COST", "anchor": "center", "width": 70, "minwidth": 40},
            "name": {"text": "NAME", "anchor": "w", "width": 200, "minwidth": 60},
            "qty": {"text": "QTY", "anchor": "center", "width": 40, "minwidth": 24},
            "price": {"text": "PRICE", "anchor": "center", "width": 70, "minwidth": 40},
            "stock": {"text": "STOCK", "anchor": "center", "width": 50, "minwidth": 30},
        }

        for col in columns:
            config = column_config[col]
            self.tree.heading(col, text=config["text"])
            # Non-name columns should be allowed to stretch first; name has
            # lower stretch priority and a small minwidth so it will shrink
            # before others when space is constrained.
            stretch = False if col == "name" else True
            self.tree.column(
                col,
                anchor=config["anchor"],
                width=config["width"],
                minwidth=config.get("minwidth", 40),
                stretch=stretch,
            )

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview, style="Red.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _parent_click_clear(event):
            # Do not clear selection when clicking on the tree headings or separators
            try:
                tx = event.x_root - self.tree.winfo_rootx()
                ty = event.y_root - self.tree.winfo_rooty()
                region = self.tree.identify_region(tx, ty)
                if region and (region.startswith("heading") or region == "separator"):
                    return
            except Exception:
                # If any error, fall back to default behavior
                pass
            try:
                self.tree.selection_remove(self.tree.selection())
            except Exception:
                pass

        parent.bind("<Button-1>", _parent_click_clear)
        self.tree.bind("<Button-1>", self._on_tree_click)
        # Right-click price to copy formatted product info to clipboard
        self.tree.bind("<Button-3>", self._on_tree_right_click)

        # Adjust columns when the tree size changes
        try:
            self.tree.bind("<Configure>", lambda e: self._adjust_tree_columns())
        except Exception:
            pass
    
    def _apply_column_tag(self, item_id: str, color_tag: str):
        """Apply color tag to item for column-only coloring."""
        if not color_tag:
            return
        current_tags = self.tree.item(item_id, "tags")
        new_tags = list(current_tags) if current_tags else []
        if color_tag not in new_tags:
            new_tags.append(color_tag)
        self.tree.item(item_id, tags=tuple(new_tags))

    def _setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Transaction.Treeview",
            background=theme.get("card_alt"),
            foreground=theme.get("text"),
            fieldbackground=theme.get("card_alt"),
            font=("Poppins", 18),
            rowheight=40,
            borderwidth=1,
            relief="solid"
        )

        style.configure(
            "Transaction.Treeview.Heading",
            background=theme.get("heading_bg"),
            foreground=theme.get("heading_fg"),
            font=("Poppins", 20, "bold")
        )

        if theme.mode == "dark":
            style.map("Transaction.Treeview",
                    background=[("selected", "#4A4A4A")],
                    foreground=[("selected", "#FFFFFF")])
        else:
            style.map("Transaction.Treeview",
                    background=[("selected", "#D0D0D0")],
                    foreground=[("selected", "#000000")])

        style.map("Transaction.Treeview.Heading", 
                background=[("active", theme.get("accent_hover"))])

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

    def _adjust_tree_columns(self):
        """Dynamically allocate widths giving priority to non-name columns.

        The Name column is made the last priority and will shrink first when
        space is limited.
        """
        if not hasattr(self, 'tree'):
            return
        try:
            total_w = max(100, self.tree.winfo_width())
        except Exception:
            return

        columns = ("date", "qty_restock", "cost", "name", "qty", "price", "stock")
        # Desired widths and minimums (match column_config defaults)
        # Give DATE a larger desired width to avoid year cropping in half-screen.
        desired = {"date": 110, "qty_restock": 80, "cost": 70, "name": 200, "qty": 40, "price": 70, "stock": 50}
        minw = {k: max(30, int(desired[k] * 0.4)) for k in desired}
        # Make name column min smaller so it shrinks first
        minw["name"] = 60

        non_name = [c for c in columns if c != "name"]
        sum_desired_nonname = sum(desired[c] for c in non_name)

        # If enough space for all desired widths, use desired.
        # However, when in very wide windows (fullscreen) prefer a larger
        # `name` column so product names are emphasized.
        if total_w >= sum_desired_nonname + desired["name"]:
            if total_w >= 1200:
                # allocate a larger share to name on wide screens
                name_w = max(desired["name"], int(total_w * 0.45))
                remaining = total_w - name_w
                # distribute remaining proportionally among other columns
                non_name_total = sum(desired[c] for c in non_name)
                for c in non_name:
                    w = int(remaining * (desired[c] / non_name_total))
                    w = max(minw[c], w)
                    self.tree.column(c, width=w)
                self.tree.column("name", width=name_w)
                return
            else:
                for c in columns:
                    self.tree.column(c, width=desired[c])
                return

        # Otherwise, reserve as much as possible for non-name columns then name
        name_width = max(minw["name"], total_w - sum_desired_nonname)
        remaining = total_w - name_width
        if remaining <= 0:
            # Worst case: give minimums
            for c in non_name:
                self.tree.column(c, width=minw[c])
            self.tree.column("name", width=minw["name"])
            return

        # Distribute remaining to non-name columns proportionally to desired widths
        total_des = sum(desired[c] for c in non_name)
        for c in non_name:
            w = int(remaining * (desired[c] / total_des))
            w = max(minw[c], w)
            self.tree.column(c, width=w)

        # Finally set name column
        self.tree.column("name", width=name_width)

    def _on_tree_click(self, event):
        # Allow header/separator interactions (sorting/resizing) to proceed.
        try:
            region = self.tree.identify_region(event.x, event.y)
            if region in ("heading", "separator"):
                return None
        except Exception:
            pass

        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        else:
            self.tree.selection_remove(self.tree.selection())
        return "break"

    def _on_tree_right_click(self, event):
        """If right-clicked on the price column, copy formatted product info to clipboard."""
        try:
            item = self.tree.identify_row(event.y)
            if not item:
                return
            col = self.tree.identify_column(event.x)
            # identify_column returns like '#1'..'#7' for our columns; price is column index 6 -> '#6'
            try:
                col_idx = int(col.lstrip('#')) - 1
            except Exception:
                col_idx = -1

            # Price column index is 5 (0-based)
            if col_idx != 5:
                return

            vals = self.tree.item(item).get('values') or []
            price_val = ""
            if len(vals) > 5 and vals[5]:
                # vals[5] is formatted like '₱12.34' or similar
                price_val = vals[5]
            else:
                # fallback to product SRP stored in details
                price_val = format_price_display(self.details.get('price', 0.0)) if self.details else ""

            # Build first line from product details
            t = (self.details.get('type', '') if self.details else '').strip()
            id_ = (self.details.get('id', '') if self.details else '').strip()
            od = (self.details.get('od', '') if self.details else '').strip()
            th = (self.details.get('th', '') if self.details else '').strip()
            brand = (self.details.get('brand', '') if self.details else '').strip()
            origin = (self.details.get('country_of_origin', '') if self.details else '').strip()

            origin_part = f" {origin}" if origin else ""
            product_type = self._get_product_type_label()
            first_line = f"{t} {id_}-{od}-{th} {brand} {product_type}{origin_part}".strip()

            # Normalize price_val to numeric if possible
            p_num = None
            try:
                # remove peso symbol and commas
                cleaned = str(price_val).replace('₱', '').replace(',', '').strip()
                if cleaned.endswith('-'):
                    cleaned = cleaned[:-1]
                p_num = float(cleaned)
            except Exception:
                try:
                    p_num = float(self.details.get('price', 0.0))
                except Exception:
                    p_num = 0.0

            if abs(p_num - int(p_num)) < 1e-9:
                price_line = f"₱{int(p_num)}- / pc."
            else:
                price_line = f"₱{p_num:.2f} / pc."

            out_text = f"{first_line}\n{price_line}"

            try:
                # Use the widget's clipboard
                self.clipboard_clear()
                self.clipboard_append(out_text)
                # temporary feedback
                old = self.history_status_label.cget('text') if hasattr(self, 'history_status_label') else ''
                try:
                    self.history_status_label.configure(text='Copied to clipboard!')
                    self.after(1500, lambda: self.history_status_label.configure(text=old))
                except Exception:
                    pass
            except Exception:
                pass

        except Exception:
            return

    def _copy_product_info_to_clipboard(self):
        """Copy the product card's formatted info to clipboard."""
        try:
            details = getattr(self, 'details', {}) or {}
            t = (details.get('type', '') or '').strip()
            id_ = (details.get('id', '') or '').strip()
            od = (details.get('od', '') or '').strip()
            th = (details.get('th', '') or '').strip()
            brand = (details.get('brand', '') or '').strip()
            origin = (details.get('country_of_origin', '') or '').strip()

            origin_part = f" {origin}" if origin else ""
            product_type = self._get_product_type_label()
            first_line = f"{t} {id_}-{od}-{th} {brand} {product_type}{origin_part}".strip()

            # srp_var may contain formatted price like '₱123.00' or plain number
            raw_price = str(self.srp_var.get() or "").replace('₱', '').replace(',', '').strip()
            try:
                if raw_price.endswith('-'):
                    raw_price = raw_price[:-1].strip()
                pnum = float(raw_price) if raw_price != '' else float(details.get('price', 0.0) or 0.0)
            except Exception:
                try:
                    pnum = float(details.get('price', 0.0) or 0.0)
                except Exception:
                    pnum = 0.0

            if abs(pnum - int(pnum)) < 1e-9:
                price_line = f"₱{int(pnum)}- / pc."
            else:
                price_line = f"₱{pnum:.2f} / pc."

            out_text = f"{first_line}\n{price_line}"

            try:
                self.clipboard_clear()
                self.clipboard_append(out_text)
                # brief feedback on history_status_label
                try:
                    old = self.history_status_label.cget('text') if hasattr(self, 'history_status_label') else ''
                    self.history_status_label.configure(text='Copied to clipboard!')
                    self.after(1500, lambda: self.history_status_label.configure(text=old))
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

    def set_details(self, details: Dict[str, Any], main_app):
        self.details = details
        self.main_app = main_app
        self.srp_var.set(format_price_display(details['price']))
        self.image_path = get_photo_path_by_type(self.details)

        self._load_location()
        self._load_transactions()
        self._load_photo()
        
        # Schedule a refresh after a brief delay to ensure rendering is complete
        # This fixes the issue where transaction history appears empty immediately after redirect
        self.after(100, self._refresh_transaction_display)

    def _refresh_transaction_display(self):
        """Force refresh of transaction display - ensures data is shown after redirect"""
        try:
            if hasattr(self, 'tree') and hasattr(self, 'details'):
                self._load_transactions()
        except Exception:
            pass

    def _load_transactions(self):
        rows = load_transactions_records(self.details)

        self.header_label.configure(text=create_header_text(self.details))
        self.sub_header_label.configure(text=create_subtitle_text(self.details))

        self.tree.delete(*self.tree.get_children())

        # Build running stock map (per-row) using new unknown stock logic
        from ..ui.mm import apply_stock_transaction, format_stock_display
        running_stock = 0
        running_map = {}
        for idx, row in enumerate(rows):
            date, name, qty, cost, is_restock, brand = row
            if is_restock == 2:
                # Reset to actual count
                running_stock = int(qty)
            else:
                # Apply transaction using the new unknown stock logic
                is_restock_tx = (is_restock == 1)  # 1 = restock, 0 = sale
                running_stock = apply_stock_transaction(running_stock, int(qty), is_restock_tx)
            running_map[idx] = running_stock

        # Identify fabrication pairs (same date and name: one restock + one sale)
        groups = {}
        for idx, row in enumerate(rows):
            date, name, qty, cost, is_restock, brand = row
            key = (date, name)
            groups.setdefault(key, {'restocks': [], 'sales': []})
            if is_restock == 1:
                groups[key]['restocks'].append(idx)
            elif is_restock == 0:
                groups[key]['sales'].append(idx)

        pairs = {}
        for key, lists in groups.items():
            rlist = lists['restocks']
            slist = lists['sales']
            # Pair greedily by order
            count = min(len(rlist), len(slist))
            for i in range(count):
                r_idx = rlist[i]
                s_idx = slist[i]
                pairs[r_idx] = (r_idx, s_idx)
                pairs[s_idx] = (r_idx, s_idx)

        displayed = []
        emitted = set()

        def format_date(d):
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                dt = datetime.strptime(d, "%m/%d/%y")
            return dt.strftime("%m/%d/%y")

        for idx, row in enumerate(rows):
            if idx in emitted:
                continue

            if idx in pairs:
                r_idx, s_idx = pairs[idx]
                # Only emit once, pick the earlier index to preserve order
                first_idx = min(r_idx, s_idx)
                if idx != first_idx:
                    continue
                rrow = rows[r_idx]
                srow = rows[s_idx]
                # build merged display
                date_str = format_date(rrow[0])
                # qty_restock from the restock record
                qty_restock = rrow[2] if rrow[4] == 1 else ""
                cost_str = ""  # leave cost empty for merged fabrication rows
                name = rrow[1]
                qty_sold = abs(int(srow[2])) if srow[4] == 0 else ""
                # prefer sale price if available
                price_val = None
                try:
                    if srow[3] is not None:
                        price_val = float(srow[3])
                except (ValueError, TypeError):
                    price_val = None
                price_str = f"₱{price_val:.2f}" if price_val is not None else ""
                later_idx = max(r_idx, s_idx)
                stock_after = running_map.get(later_idx, "")
                stock_after_display = format_stock_display(stock_after)  # Format for display
                displayed.append(((date_str, qty_restock, cost_str, name, qty_sold, price_str, stock_after_display), 'gray'))
                emitted.add(r_idx)
                emitted.add(s_idx)
            else:
                # Unpaired row: format like summarize_running_stock
                date, name, qty, cost, is_restock, brand = row
                date_str = format_date(date)
                qty_restock = ""
                cost_str = ""
                price_str = ""
                display_qty = ""
                if is_restock == 1:
                    qty_restock = qty
                    try:
                        cost_value = float(cost) if cost is not None else 0.0
                    except (ValueError, TypeError):
                        cost_value = 0.0
                    # Display cost as integer centavos for reference (e.g., 99.00 -> 9900)
                    cost_str = f"₱{int(cost_value * 100)}" if cost_value > 0 else ""
                elif is_restock == 0:
                    display_qty = abs(int(qty))
                    try:
                        price_val = float(cost) if cost is not None else 0.0
                    except (ValueError, TypeError):
                        price_val = 0.0
                    price_str = format_price_display(price_val) if price_val is not None else ""
                elif is_restock == 2:
                    # Actual transaction: optional cost shown in cost column as centavos integer
                    try:
                        cost_value = float(cost) if cost is not None else 0.0
                    except (ValueError, TypeError):
                        cost_value = 0.0
                    cost_str = f"₱{int(cost_value * 100)}" if cost_value > 0 else ""
                stock_after = running_map.get(idx, "")
                stock_after_display = format_stock_display(stock_after)  # Format for display
                tag = get_transaction_tag(qty_restock, price_str)
                if is_restock == 2:
                    tag = 'green'
                displayed.append(((date_str, qty_restock, cost_str, name, display_qty, price_str, stock_after_display), tag))

        def custom_sort_key(item):
            vals, tag = item
            dt = datetime.strptime(vals[0], "%m/%d/%y")
            tag_priority = {'blue': 0, 'gray': 0, 'red': 1, 'green': 2}
            return (dt, tag_priority.get(tag, 99))

        displayed.sort(key=custom_sort_key)

        for index, (vals, tag) in enumerate(displayed):
            alt_tag = "alt_even" if (index % 2 == 0) else "alt_odd"
            self.tree.insert("", "end", values=vals, tags=(alt_tag, tag))

        # Add auto-scroll to bottom to show latest date
        if self.tree.get_children():
            last_item = self.tree.get_children()[-1]
            self.tree.see(last_item)

        self._update_stock_display(rows)

    def _update_stock_display(self, rows):
        low, warn = get_thresholds(self.details)
        stock = calculate_current_stock(rows)
        color = get_stock_color(stock, low, warn)
        from ..ui.mm import format_stock_display
        stock_display = format_stock_display(stock)
        self.stock_label.configure(text=f"STOCK: {stock_display}", text_color=color)

    def _load_location(self):
        location, notes = get_location_and_notes(self.details)
        self.location_var.set(location)
        self.notes_var.set(notes)

    # ==================== EDIT MODE ====================
    def _toggle_edit_mode(self):
        """Toggle between edit and view modes"""
        if not self.edit_mode:
            self._enter_edit_mode()
        else:
            self._exit_edit_mode()
        self.edit_mode = not self.edit_mode

    def _enter_edit_mode(self):
        """Enter edit mode"""
        self.location_entry.configure(state="normal")
        self.notes_entry.configure(state="normal")

        # Switch to price entry
        self.srp_display.pack_forget()
        self.srp_entry.pack(anchor="center")

        # Remove currency symbol for editing
        current_price = self.srp_var.get().replace("₱", "").strip()
        self.srp_var.set(current_price)

        # Update button appearance
        self.edit_btn.configure(
            text="Save",
            fg_color="#22C55E",
            hover_color="#16A34A"
        )

    def _exit_edit_mode(self):
        """Exit edit mode and save changes"""
        self._save_all_changes()

        self.location_entry.configure(state="readonly")
        self.notes_entry.configure(state="readonly")

        # Switch back to price display
        self.srp_entry.pack_forget()
        self.srp_display.pack(pady=(10, 0), anchor="center")

        # Update button appearance
        self.edit_btn.configure(
            text="Edit",
            fg_color="#4B5563",
            hover_color="#6B7280"
        )

    def _save_all_changes(self):
        """Save all changes made in edit mode"""
        self._save_location()
        self._save_price()
        self._save_notes()

    def _save_location(self):
        """Save location changes"""
        update_location(self.details, self.location_var.get())
        if self.main_app:
            self.main_app.refresh_product_list()

    def _save_price(self):
        """Save price changes"""
        price_str = self.srp_var.get()
        if not validate_price_input(price_str):
            messagebox.showerror("Error", "Invalid price format")
            return

        try:
            new_price = parse_price_input(price_str)
            self.srp_var.set(format_price_display(new_price))
            update_price(self.details, new_price)
            if self.main_app:
                self.main_app.refresh_product_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save price: {e}")

    def _save_notes(self):
        """Save notes changes"""
        update_notes(self.details, self.notes_var.get())
        if self.main_app:
            self.main_app.refresh_product_list()

    # ==================== STOCK SETTINGS ====================
    def _open_stock_settings(self, event=None):
        """Open stock threshold settings window"""
        settings_window = self._create_settings_window()
        self._populate_settings_form(settings_window)

    def _create_settings_window(self):
        """Create stock settings window"""
        settings = ctk.CTkToplevel(self)
        settings.title("MOS Inventory")
        settings.geometry("400x300")
        settings.resizable(False, False)
        settings.configure(fg_color=theme.get("bg"))
        settings.transient(self)
        settings.grab_set()

        # Center window
        settings.update_idletasks()
        w, h = settings.winfo_width(), settings.winfo_height()
        sw, sh = settings.winfo_screenwidth(), settings.winfo_screenheight()
        settings.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        return settings

    def _populate_settings_form(self, settings_window):
        """Populate settings form with threshold controls"""
        main_frame = ctk.CTkFrame(settings_window, fg_color=theme.get("card"), corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        ctk.CTkLabel(
            main_frame,
            text="Stock Threshold Settings",
            font=("Poppins", 20, "bold"),
            text_color=theme.get("text")
        ).pack(pady=(30, 20))

        # Form container
        form = ctk.CTkFrame(main_frame, fg_color="transparent")
        form.pack(fill="x", padx=30, pady=(0, 20))

        # Get current thresholds
        low_var, warn_var = tk.StringVar(), tk.StringVar()
        low, warn = get_thresholds(self.details)
        low_var.set(str(low))
        warn_var.set(str(warn))

        # Threshold inputs
        threshold_configs = [
            ("RESTOCK NEEDED (Red)", low_var),
            ("LOW ON STOCK (Orange)", warn_var)
        ]

        for label_text, var in threshold_configs:
            ctk.CTkLabel(
                form,
                text=label_text,
                font=("Poppins", 14, "bold"),
                text_color=theme.get("text")
            ).pack(anchor="w", pady=(0, 5))

            entry = ctk.CTkEntry(
                form,
                textvariable=var,
                font=("Poppins", 12),
                fg_color=theme.get("input"),
                text_color=theme.get("text"),
                corner_radius=20,
                height=35
            )
            entry.pack(fill="x", pady=(0, 15))
            entry.bind("<Return>", lambda e: self._save_thresholds(settings_window, low_var.get(), warn_var.get()))

        # Buttons
        btn_holder = ctk.CTkFrame(form, fg_color="transparent")
        btn_holder.pack(fill="x")

        ctk.CTkButton(
            btn_holder,
            text="Cancel",
            width=100,
            height=40,
            corner_radius=25,
            fg_color=theme.get("accent_hover"),
            hover_color=theme.get("accent"),
            text_color=theme.get("text"),
            command=settings_window.destroy
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_holder,
            text="Save",
            width=100,
            height=40,
            corner_radius=25,
            fg_color="#22C55E",
            hover_color="#16A34A",
            text_color="#FFFFFF",
            command=lambda: self._save_thresholds(settings_window, low_var.get(), warn_var.get())
        ).pack(side="right")

    def _save_thresholds(self, settings_window, low_str, warn_str):
        """Save threshold settings"""
        try:
            low, warn = int(low_str), int(warn_str)
            if low < 0 or warn < 0:
                raise ValueError("Negative values not allowed")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid positive integer values.")
            return

        update_thresholds(self.details, low, warn)
        settings_window.destroy()
        self._load_transactions()  # Refresh to update colors

    # ==================== PHOTO FUNCTIONALITY ====================
    def _upload_photo(self):
        """Handle photo upload for MOS brand products"""
        if not is_photo_upload_allowed(self.details):
            messagebox.showinfo("Not Allowed", "Photo upload is only allowed for MOS brand products.")
            return

        file_path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )

        if not validate_image_file(file_path):
            if file_path:  # User selected a file but it's invalid
                messagebox.showerror("Invalid File", "Please select a .jpg, .jpeg, or .png image file.")
            return

        self._process_photo_upload(file_path)

    def _process_photo_upload(self, file_path):
        """Process and save uploaded photo"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            filename = create_safe_filename(self.details, ext)
            photos_dir = get_photos_directory()
            save_path = os.path.join(photos_dir, filename)

            if not compress_and_save_image(file_path, save_path):
                messagebox.showerror("Error", "Failed to process image. Please try again.")
                return

            # Clean up old images before setting new one
            delete_old_images(self.details)

            self.image_path = save_path
            self._load_photo()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload photo: {str(e)}")

    def _show_photo_menu(self, event=None):
        """Show photo context menu or view photo"""
        if not os.path.exists(self.image_path):
            return

        # For non-MOS products, just show the photo
        if not is_photo_upload_allowed(self.details):
            self._show_fullscreen_photo()
            return

        # For MOS products, show context menu
        self._create_photo_context_menu()

    def _create_photo_context_menu(self):
        """Create photo context menu for MOS products"""
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(fg_color=theme.get("card"))

        # Position menu near photo
        x = self.photo_label.winfo_rootx() + self.photo_label.winfo_width() // 2 - 60
        y = self.photo_label.winfo_rooty() + self.photo_label.winfo_height() + 5
        popup.geometry(f"120x80+{x}+{y}")

        def close_menu():
            if popup and popup.winfo_exists():
                popup.destroy()

        def view_photo():
            close_menu()
            self._show_fullscreen_photo()

        def delete_photo():
            close_menu()
            if messagebox.askyesno("Delete Photo", "Are you sure you want to delete this photo?"):
                try:
                    os.remove(self.image_path)
                    self.image_path = ""  # reset internally
                    # Directly show placeholder forcing update
                    self.photo_label.configure(image=None, text="📷")
                    self.photo_label.image = None
                    # Optionally destroy and recreate the label
                    self.photo_label.destroy()
                    # Recreate photo label widget
                    photo_frame = self.photo_label.master
                    self.photo_label = ctk.CTkLabel(
                        photo_frame,
                        text="📷",
                        font=("Poppins", 48),
                        text_color=theme.get("muted"),
                        cursor="hand2",
                        anchor="center"
                    )
                    self.photo_label.pack(fill="both", expand=True)
                    self.photo_label.bind("<Button-1>", self._photo_label_clicked)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete photo: {str(e)}")

        # View button
        ctk.CTkButton(
            popup,
            text="🔍 View",
            font=("Poppins", 12),
            fg_color=theme.get("accent"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            corner_radius=15,
            height=30,
            command=view_photo
        ).pack(padx=5, pady=(5, 2))

        # Delete button (only for MOS products)
        ctk.CTkButton(
            popup,
            text="🗑 Delete",
            font=("Poppins", 12),
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            corner_radius=15,
            height=30,
            command=delete_photo
        ).pack(padx=5, pady=(2, 5))

        # Close menu when losing focus
        popup.bind("<FocusOut>", lambda e: close_menu())
        def _safe_focus(w):
            try:
                if w and getattr(w, 'winfo_exists', lambda: False)() and w.winfo_exists():
                    w.focus_set()
            except Exception:
                pass

        _safe_focus(popup)

    def _show_fullscreen_photo(self):
        """Show photo in fullscreen viewer"""
        if not os.path.exists(self.image_path):
            return

        photo_viewer = self._create_photo_viewer_window()
        self._display_fullscreen_image(photo_viewer)

    def _create_photo_viewer_window(self):
        """Create photo viewer window"""
        viewer = ctk.CTkToplevel(self)
        viewer.title("MOS Inventory")
        viewer.transient(self)
        viewer.grab_set()
        viewer.configure(fg_color=theme.get("bg"))

        # Size as 80% of screen
        sw, sh = viewer.winfo_screenwidth(), viewer.winfo_screenheight()
        ww, wh = int(sw * 0.8), int(sh * 0.8)
        viewer.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")

        return viewer

    def _display_fullscreen_image(self, viewer):
        """Display fullscreen image in viewer"""
        container = ctk.CTkFrame(viewer, fg_color=theme.get("bg"))
        container.pack(fill="both", expand=True, padx=20, pady=20)

        try:
            img = Image.open(self.image_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            viewer.destroy()
            return

        label = ctk.CTkLabel(container, text="", cursor="hand2")
        label.pack(fill="both", expand=True)

        def resize_image(event):
            """Resize image to fit container while maintaining aspect ratio"""
            container_width, container_height = event.width, event.height

            # Calculate scale to fit image in container
            scale = min(container_width / img.width, container_height / img.height)
            new_width = max(1, int(img.width * scale))
            new_height = max(1, int(img.height * scale))

            # Resize image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            ctk_img = CTkImage(light_image=resized_img, size=(new_width, new_height))

            label.configure(image=ctk_img)
            label.image = ctk_img  # Keep reference

        # Bind resize event
        container.bind("<Configure>", resize_image)
        label.bind("<Button-1>", lambda e: viewer.destroy())

        # Initial resize
        container.update_idletasks()
        resize_image(type("Event", (), {
            "width": container.winfo_width(),
            "height": container.winfo_height()
        })())

        # Instructions and close button
        ctk.CTkLabel(
            container,
            text="Click image or press ESC to close",
            font=("Poppins", 12),
            text_color="#CCCCCC"
        ).pack()

        ctk.CTkButton(
            container,
            text="Close",
            font=("Poppins", 12, "bold"),
            fg_color="#D00000",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            corner_radius=20,
            width=100,
            height=30,
            command=viewer.destroy
        ).pack(pady=(10, 0))

        # Keyboard shortcut
        viewer.bind("<Escape>", lambda e: viewer.destroy())
        def _safe_focus_viewer():
            try:
                if viewer and getattr(viewer, 'winfo_exists', lambda: False)() and viewer.winfo_exists():
                    viewer.focus_set()
            except Exception:
                pass
        _safe_focus_viewer()

    # ==================== THEME MANAGEMENT ====================
    def destroy(self):
        """Clean up theme subscription on destroy"""
        theme.unsubscribe(self.apply_theme)
        super().destroy()

    def apply_theme(self):
        """Apply theme changes to all UI elements"""
        try:
            if not self.winfo_exists():
                return

            # Update main frames
            self.configure(fg_color=theme.get("bg"))
            if hasattr(self, 'main_content'):
                self.main_content.configure(fg_color=theme.get("bg"))

            # Update header elements
            if hasattr(self, 'logo_frame'):
                self.logo_frame.configure(fg_color=theme.get("bg"))
                self._create_logo_section()  # Recreate for theme switching

            # Update buttons with consistent styling
            button_updates = [
                ("back_btn", theme.get("primary"), theme.get("primary_hover"), "#FFFFFF"),
                ("admin_btn", theme.get("primary"), theme.get("primary_hover"), "#FFFFFF")
            ]

            for btn_name, fg_color, hover_color, text_color in button_updates:
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    btn.configure(fg_color=fg_color, hover_color=hover_color, text_color=text_color)

            # Update labels
            label_updates = [
                ("header_label", theme.get("text")),
                ("sub_header_label", theme.get("muted")),
                ("srp_display", theme.get("text")),
                ("photo_label", theme.get("muted")),
                ("history_status_label", theme.get("text"))
            ]

            for label_name, text_color in label_updates:
                if hasattr(self, label_name):
                    getattr(self, label_name).configure(text_color=text_color)

            # Update entry widgets
            entry_widgets = ["srp_entry", "location_entry", "notes_entry"]
            for entry_name in entry_widgets:
                if hasattr(self, entry_name):
                    getattr(self, entry_name).configure(
                        fg_color=theme.get("input"),
                        text_color=theme.get("text")
                    )

            # Update stock display with appropriate color
            if hasattr(self, "details") and self.details:
                rows = load_transactions_records(self.details)
                self._update_stock_display(rows)

            # Update card frames recursively
            self._update_card_frames_recursive(self)
            
            if hasattr(self, 'watermark_label'):
                self.watermark_label.configure(text_color=theme.get("muted"))
            # Update treeview styling
            if hasattr(self, "tree"):
                self._setup_treeview_style()
                # Refresh tree item tags for new colors
                for child in self.tree.get_children():
                    tags = self.tree.item(child)["tags"]
                    if tags:
                        self.tree.item(child, tags=tags)

            # Update positions after theme change
            self.after(10, self._on_window_resize)

        except Exception as e:
            print(f"Error applying theme to transaction window: {e}")

    def _update_card_frames_recursive(self, parent):
        """Recursively update card frame colors"""
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                if child.cget("fg_color") != "transparent":
                    # Header elements stay as bg color
                    if hasattr(child, 'winfo_y') and child.winfo_y() < 150:
                        child.configure(fg_color=theme.get("bg"))
                    else:
                        child.configure(fg_color=theme.get("card"))

                # Recurse into child frames
                self._update_card_frames_recursive(child)
