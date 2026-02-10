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
    def __init__(self, parent, details, controller=None, return_to=None):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.details = details
        self.controller = controller
        self.return_to = return_to
        
        # Main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Scrollable container
        self.main_scroll = ctk.CTkScrollableFrame(
            self, 
            fg_color=theme.get("bg"),
            scrollbar_fg_color=theme.get("scroll_trough"),
            scrollbar_button_color=theme.get("scroll_thumb"),
            scrollbar_button_hover_color=theme.get("scroll_thumb_hover")
        )
        self.main_scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Back button
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
            command=self.go_back
        )
        self.back_btn.place(x=40, y=40)
        
        # Header Section
        self.header_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=40, pady=(100, 20))
        
        header_text = create_header_text(self.details)
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text=header_text,
            font=("Hero", 36, "bold"),
            text_color=theme.get("text")
        )
        self.title_label.pack(anchor="w")
        
        subtitle_text = create_subtitle_text(self.details)
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text=subtitle_text,
            font=("Poppins", 18),
            text_color=theme.get("muted")
        )
        self.subtitle_label.pack(anchor="w")

        # Content Grid
        self.content_grid = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.content_grid.pack(fill="x", padx=40, pady=20)
        self.content_grid.grid_columnconfigure(0, weight=1) # Left: Stock/Info
        self.content_grid.grid_columnconfigure(1, weight=1) # Right: History
        
        # Left Column: Stock & Info
        self.info_panel = ctk.CTkFrame(self.content_grid, fg_color=theme.get("card"), corner_radius=20)
        self.info_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        self._build_info_panel()
        
        # Right Column: Transaction History
        self.history_panel = ctk.CTkFrame(self.content_grid, fg_color=theme.get("card"), corner_radius=20)
        self.history_panel.grid(row=0, column=1, sticky="nsew")
        
        self._build_history_panel()
        
    def go_back(self):
        if self.controller and self.return_to:
            self.controller.go_back(self.return_to)
            
    def _build_info_panel(self):
        # Load data
        rows = load_transactions_records(self.details)
        current_stock = calculate_current_stock(rows)
        low, warn = get_thresholds(self.details)
        loc, notes = get_location_and_notes(self.details)
        
        # Stock Display
        stock_color = get_stock_color(current_stock, low, warn)
        self.stock_label = ctk.CTkLabel(
            self.info_panel,
            text=f"STOCK: {current_stock}",
            font=("Hero", 48, "bold"),
            text_color=stock_color
        )
        self.stock_label.pack(pady=(40, 20))
        
        # Details
        self.details_frame = ctk.CTkFrame(self.info_panel, fg_color="transparent")
        self.details_frame.pack(fill="x", padx=30, pady=20)
        
        # Location
        ctk.CTkLabel(self.details_frame, text="Location:", font=("Poppins", 14, "bold"), text_color=theme.get("muted")).pack(anchor="w")
        ctk.CTkLabel(self.details_frame, text=loc or "Not set", font=("Poppins", 16), text_color=theme.get("text")).pack(anchor="w", pady=(0, 10))
        
        # Notes
        ctk.CTkLabel(self.details_frame, text="Notes:", font=("Poppins", 14, "bold"), text_color=theme.get("muted")).pack(anchor="w")
        ctk.CTkLabel(self.details_frame, text=notes or "-", font=("Poppins", 16), text_color=theme.get("text")).pack(anchor="w", pady=(0, 10))

    def _build_history_panel(self):
        ctk.CTkLabel(
            self.history_panel, 
            text="Transaction History", 
            font=("Poppins", 20, "bold"),
            text_color=theme.get("text")
        ).pack(pady=20)
        
        # Simple list for now
        self.history_scroll = ctk.CTkScrollableFrame(self.history_panel, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        rows = load_transactions_records(self.details)
        processed = summarize_running_stock(rows)
        
        for row in reversed(processed): # Show newest first
            date_str, name, qty, price, is_restock, brand, running = row
            tag = get_transaction_tag(is_restock)
            color = "#22C55E" if is_restock in (1, 2) else "#EF4444"
            text = f"{date_str} - {tag.upper()} {qty} (Stock: {running})"
            ctk.CTkLabel(self.history_scroll, text=text, font=("Poppins", 14), text_color=color).pack(anchor="w", pady=2)
