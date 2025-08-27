import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
from customtkinter import CTkImage
from typing import Any, Dict
import os
from datetime import datetime

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


class TransactionWindow(ctk.CTkFrame):
    def __init__(self, parent, details: Dict[str, Any], controller, return_to):
        super().__init__(parent, fg_color="#000000")
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

    def _build_ui(self):
        self._create_header_section()
        self._create_main_content()
        self._create_history_section()

    def _create_header_section(self):
        header_frame = ctk.CTkFrame(self, fg_color="#000000", height=120)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        header_frame.columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back",
            font=("Poppins", 20, "bold"),
            fg_color="#D00000",
            hover_color="#B71C1C",
            text_color="#FFFFFF",
            corner_radius=40,
            width=120,
            height=50,
            command=self._handle_back_button
        )
        back_btn.grid(row=0, column=0, sticky="w", padx=(40, 10), pady=35)

    def _handle_back_button(self):
        if self.controller and self.return_to:
            self.controller.show_frame(self.return_to)
        else:
            self.master.destroy()

    def _create_main_content(self):
        main_container = ctk.CTkFrame(self, fg_color="#000000")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        combined_section = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=40)
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
            title_left, 
            text="", 
            font=("Poppins", 24, "bold"), 
            text_color="#FFFFFF"
        )
        self.header_label.pack(anchor="w")

        self.sub_header_label = ctk.CTkLabel(
            title_left, 
            text="", 
            font=("Poppins", 20, "bold"), 
            text_color="#CCCCCC"
        )
        self.sub_header_label.pack(anchor="w", pady=(5, 0))

    def _create_stock_price_section(self, parent):
        stock_srp_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stock_srp_frame.grid(row=0, column=1)

        # Emphasized stock label (headline)
        self.stock_label = ctk.CTkLabel(
            stock_srp_frame, 
            text="", 
            font=("Poppins", 26, "bold"), 
            text_color="#FFFFFF", 
            cursor="hand2"
        )
        self.stock_label.pack(anchor="center")
        self.stock_label.bind("<Button-1>", self.open_stock_settings)

        # Emphasized SRP label/value (headline)
        self.srp_display = ctk.CTkLabel(
            stock_srp_frame, 
            textvariable=self.srp_var, 
            font=("Poppins", 26, "bold"), 
            text_color="#FFFFFF"
        )
        self.srp_display.pack(anchor="center", pady=(10, 0))

        self.srp_entry = ctk.CTkEntry(
            stock_srp_frame, 
            textvariable=self.srp_var, 
            font=("Poppins", 22, "bold"), 
            fg_color="#374151", 
            text_color="#FFFFFF", 
            corner_radius=20, 
            height=44, 
            width=150, 
            justify="center"
        )

    def _create_photo_section(self, parent):
        photo_container2 = ctk.CTkFrame(parent, fg_color="transparent", width=100, height=100)
        photo_container2.grid(row=0, column=2, sticky="e")
        photo_container2.grid_propagate(False)

        photo_frame2 = ctk.CTkFrame(photo_container2, width=100, height=100, fg_color="#374151", corner_radius=20)
        photo_frame2.pack_propagate(False)
        photo_frame2.pack(fill="both", expand=True)

        self.photo_label = ctk.CTkLabel(
            photo_frame2, 
            text="📷", 
            font=("Poppins", 24), 
            text_color="#CCCCCC", 
            cursor="hand2"
        )
        self.photo_label.pack(fill="both", expand=True)
        self.photo_label.bind("<Button-1>", self.show_photo_menu)

        self.upload_button = ctk.CTkButton(
            photo_container2, 
            text="Upload", 
            font=("Poppins", 12, "bold"), 
            fg_color="#4B5563", 
            hover_color="#6B7280", 
            text_color="#FFFFFF", 
            corner_radius=20, 
            height=30, 
            width=80, 
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

        ctk.CTkLabel(
            loc_frame, 
            text="LOCATION", 
            font=("Poppins", 18, "bold"), 
            text_color="#FFFFFF"
        ).pack(anchor="w", pady=(0, 5))

        self.location_entry = ctk.CTkEntry(
            loc_frame, 
            textvariable=self.location_var, 
            font=("Poppins", 18), 
            fg_color="#374151", 
            text_color="#FFFFFF", 
            corner_radius=20, 
            height=44, 
            width=120, 
            state="readonly"
        )
        self.location_entry.pack()

    def _create_notes_section(self, parent):
        notes_frame = ctk.CTkFrame(parent, fg_color="transparent")
        notes_frame.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        ctk.CTkLabel(
            notes_frame, 
            text="NOTES", 
            font=("Poppins", 18, "bold"), 
            text_color="#FFFFFF"
        ).pack(anchor="w", pady=(0, 5))

        self.notes_entry = ctk.CTkEntry(
            notes_frame, 
            textvariable=self.notes_var, 
            font=("Poppins", 18), 
            fg_color="#374151", 
            text_color="#FFFFFF", 
            corner_radius=20, 
            height=44, 
            state="readonly"
        )
        self.notes_entry.pack(fill="x")

    def _create_edit_section(self, parent):
        edit_frame = ctk.CTkFrame(parent, fg_color="transparent")
        edit_frame.grid(row=0, column=2, sticky="e")

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
            command=self.toggle_edit_mode
        )
        # Align with textfield baseline instead of label
        self.edit_btn.pack(pady=(22, 0))

        # Remove status label to keep Edit button aligned with fields
        self.save_status_label = None

    def _create_history_section(self):
        main_container = self.winfo_children()[1] # Get main container
        
        history_section = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=40)
        history_section.pack(fill="both", expand=True)

        # Make the table occupy the full card by removing header spacer and increasing paddings
        table_container = ctk.CTkFrame(history_section, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=30, pady=30)

        self._setup_treeview_style()
        self._create_history_table(table_container)

    def _setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Transaction.Treeview",
                        background="#2b2b2b",
                        foreground="#FFFFFF",
                        fieldbackground="#2b2b2b",
                        font=("Poppins", 18),
                        rowheight=40)
        style.configure("Transaction.Treeview.Heading",
                        background="#000000",
                        foreground="#D00000",
                        font=("Poppins", 20, "bold"))
        style.map("Transaction.Treeview", background=[("selected", "#374151")])
        style.map("Transaction.Treeview.Heading", background=[("active", "#111111")])

    def _create_history_table(self, parent):
        columns = ("date", "qty_restock", "cost", "name", "qty", "price", "stock")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", style="Transaction.Treeview")

        self.tree.tag_configure("red", foreground="#EF4444")
        self.tree.tag_configure("blue", foreground="#3B82F6")
        self.tree.tag_configure("green", foreground="#22C55E")

        column_config = {
            "date": {"text": "DATE", "anchor": "center", "width": 90},
            "qty_restock": {"text": "QTY RESTOCK", "anchor": "center", "width": 100},
            "cost": {"text": "COST", "anchor": "center", "width": 80},
            "name": {"text": "NAME", "anchor": "w", "width": 200},
            "qty": {"text": "QTY SOLD", "anchor": "center", "width": 80},
            "price": {"text": "PRICE", "anchor": "center", "width": 80},
            "stock": {"text": "STOCK", "anchor": "center", "width": 80},
        }

        for col in columns:
            config = column_config[col]
            self.tree.heading(col, text=config["text"])
            self.tree.column(col, anchor=config["anchor"], width=config["width"])

        tree_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

    def show_save_status(self, message="Saved!", duration=2000):
        # No-op to avoid adding extra text under the button
        return

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

        # Summarize transactions
        summarized_rows = summarize_running_stock(rows)

        # Sort by date descending; format is MM/DD/YY
        summarized_rows.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%y"), reverse=True)

        for values in summarized_rows:
            date_str, qty_restock, cost, name, display_qty, price_str, running_stock = values
            tag = get_transaction_tag(qty_restock, price_str)
            self.tree.insert("", "end", values=(date_str, qty_restock, cost, name, display_qty, price_str, running_stock), tags=(tag,))

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
        self.show_save_status()

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

    def open_stock_settings(self, event=None):
        settings = self._create_settings_window()
        self._populate_settings_form(settings)

    def _create_settings_window(self):
        settings = ctk.CTkToplevel(self)
        settings.title("Stock Color Settings")
        settings.geometry("400x300")
        settings.resizable(False, False)
        settings.configure(fg_color="#000000")
        settings.transient(self)
        settings.grab_set()
        return settings

    def _populate_settings_form(self, settings_window):
        main_frame = ctk.CTkFrame(settings_window, fg_color="#2b2b2b", corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main_frame, 
            text="Stock Threshold Settings", 
            font=("Poppins", 20, "bold"), 
            text_color="#FFFFFF"
        ).pack(pady=(30, 20))

        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=(0, 20))

        low_var = tk.IntVar()
        warn_var = tk.IntVar()
        low, warn = get_thresholds(self.details)
        low_var.set(low)
        warn_var.set(warn)

        ctk.CTkLabel(
            form_frame, 
            text="LOW THRESHOLD (Red)", 
            font=("Poppins", 14, "bold"), 
            text_color="#FFFFFF"
        ).pack(anchor="w", pady=(0, 5))

        low_entry = ctk.CTkEntry(
            form_frame, 
            textvariable=low_var, 
            font=("Poppins", 12), 
            fg_color="#374151", 
            text_color="#FFFFFF", 
            corner_radius=20, 
            height=35
        )
        low_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            form_frame, 
            text="WARNING THRESHOLD (Orange)", 
            font=("Poppins", 14, "bold"), 
            text_color="#FFFFFF"
        ).pack(anchor="w", pady=(0, 5))

        warn_entry = ctk.CTkEntry(
            form_frame, 
            textvariable=warn_var, 
            font=("Poppins", 12), 
            fg_color="#374151", 
            text_color="#FFFFFF", 
            corner_radius=20, 
            height=35
        )
        warn_entry.pack(fill="x", pady=(0, 20))

        self._create_settings_buttons(form_frame, settings_window, low_var, warn_var)

    def _create_settings_buttons(self, parent, settings_window, low_var, warn_var):
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(
            button_frame, 
            text="Cancel", 
            font=("Poppins", 14, "bold"), 
            fg_color="#6B7280", 
            hover_color="#4B5563", 
            text_color="#FFFFFF", 
            corner_radius=25, 
            width=100, 
            height=40, 
            command=settings_window.destroy
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame, 
            text="Save", 
            font=("Poppins", 14, "bold"), 
            fg_color="#22C55E", 
            hover_color="#16A34A", 
            text_color="#FFFFFF", 
            corner_radius=25, 
            width=100, 
            height=40, 
            command=lambda: self._save_thresholds(settings_window, low_var.get(), warn_var.get())
        ).pack(side="right")

    def _save_thresholds(self, settings_window, low: int, warn: int):
        update_thresholds(self.details, low, warn)
        settings_window.destroy()
        self._load_transactions()

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

    def _process_photo_upload(self, file_path: str):
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
            messagebox.showerror("Error", f"Failed to upload photo: {str(e)}")

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
        popup.configure(fg_color="#2b2b2b")

        x = self.photo_label.winfo_rootx() + self.photo_label.winfo_width() // 2 - 60
        y = self.photo_label.winfo_rooty() + self.photo_label.winfo_height() + 5
        popup.geometry(f"120x80+{x}+{y}")

        def close_menu(event=None):
            if popup and popup.winfo_exists():
                popup.destroy()

        def view():
            close_menu()
            self.show_fullscreen_photo()

        ctk.CTkButton(
            popup, 
            text="🔍 View", 
            font=("Poppins", 12), 
            fg_color="#4B5563", 
            hover_color="#6B7280", 
            text_color="#FFFFFF", 
            corner_radius=15, 
            height=30, 
            command=view
        ).pack(padx=5, pady=(5, 2))

        if is_photo_upload_allowed(self.details):
            def delete():
                close_menu()
                if messagebox.askyesno("Delete Photo", "Are you sure you want to delete this photo?"):
                    os.remove(self.image_path)
                    self.load_photo()

            ctk.CTkButton(
                popup, 
                text="🗑 Delete", 
                font=("Poppins", 12), 
                fg_color="#EF4444", 
                hover_color="#DC2626", 
                text_color="#FFFFFF", 
                corner_radius=15, 
                height=30, 
                command=delete
            ).pack(padx=5, pady=(2, 5))

        popup.bind("<FocusOut>", lambda e: close_menu())
        popup.focus_set()

    def show_fullscreen_photo(self):
        if not os.path.exists(self.image_path):
            return

        photo_viewer = self._create_photo_viewer_window()
        self._display_fullscreen_image(photo_viewer)

    def _create_photo_viewer_window(self):
        photo_viewer = ctk.CTkToplevel(self)
        photo_viewer.title("Photo Viewer")
        photo_viewer.transient(self)
        photo_viewer.grab_set()
        photo_viewer.configure(fg_color="#000000")

        screen_width = photo_viewer.winfo_screenwidth()
        screen_height = photo_viewer.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        photo_viewer.geometry(f"{window_width}x{window_height}+{x}+{y}")

        return photo_viewer

    def _display_fullscreen_image(self, photo_viewer):
        container = ctk.CTkFrame(photo_viewer, fg_color="#000000")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        original_img = Image.open(self.image_path)

        label = ctk.CTkLabel(container, text="", cursor="hand2")
        label.pack(fill="both", expand=True)

        def resize_image(event):
            display_width = event.width
            display_height = event.height

            width_ratio = display_width / original_img.width
            height_ratio = display_height / original_img.height
            scale_factor = min(width_ratio, height_ratio)  # fit whole image inside window

            new_width = max(1, int(original_img.width * scale_factor))
            new_height = max(1, int(original_img.height * scale_factor))

            resized_img = original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            ctk_img = CTkImage(light_image=resized_img, size=(new_width, new_height))

            label.configure(image=ctk_img)
            label.image = ctk_img

        container.bind("<Configure>", resize_image)

        label.bind("<Button-1>", lambda e: photo_viewer.destroy())

        container.update_idletasks()
        initial_event = type("Event", (), {"width": container.winfo_width(), "height": container.winfo_height()})()
        resize_image(initial_event)

        self._create_viewer_instructions(container, photo_viewer)

    def _create_viewer_instructions(self, container, photo_viewer):
        instruction_frame = ctk.CTkFrame(container, fg_color="transparent")
        instruction_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            instruction_frame, 
            text="Click image or press ESC to close", 
            font=("Poppins", 12), 
            text_color="#CCCCCC"
        ).pack()

        close_btn = ctk.CTkButton(
            instruction_frame, 
            text="Close", 
            font=("Poppins", 12, "bold"), 
            fg_color="#D00000", 
            hover_color="#B71C1C", 
            text_color="#FFFFFF", 
            corner_radius=20, 
            width=100, 
            height=30, 
            command=photo_viewer.destroy
        )
        close_btn.pack(pady=(10, 0))

        photo_viewer.bind("<Escape>", lambda e: photo_viewer.destroy())
        photo_viewer.focus_set()
