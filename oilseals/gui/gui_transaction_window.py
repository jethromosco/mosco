import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from ..database import connect_db
from PIL import Image
from customtkinter import CTkImage
from contextlib import contextmanager
import os


@contextmanager
def db_cursor():
    conn = connect_db()
    cur = conn.cursor()
    try:
        yield cur
    finally:
        conn.commit()
        conn.close()


class TransactionWindow(ctk.CTkFrame):
    def __init__(self, parent, details, controller, return_to):
        super().__init__(parent, fg_color="#000000")
        self.controller = controller
        self.return_to = return_to
        self.main_app = None

        self.srp_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.edit_mode = False
        self.image_path = ""
        self.image_thumbnail = None

        self._build_ui()

    def _build_ui(self):
        # === Header with Back Button and Photo ===
        header_frame = ctk.CTkFrame(self, fg_color="#000000", height=120)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)

        # Using grid for better control to avoid cut off
        header_frame.columnconfigure(0, weight=1)

        # Back button matching your app style
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
            command=lambda: self.controller.show_frame(self.return_to) if self.controller and self.return_to else self.master.destroy()
        )
        back_btn.grid(row=0, column=0, sticky="w", padx=(40,10), pady=35)

        # === Main Content Container (NO SCROLLBAR) ===
        main_container = ctk.CTkFrame(self, fg_color="#000000")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # === Combined Info Section (Details Without Photo) ===
        combined_section = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=40)
        combined_section.pack(fill="x", pady=(0, 10))

        combined_inner = ctk.CTkFrame(combined_section, fg_color="transparent")
        combined_inner.pack(fill="x", padx=20, pady=20)

        # Top grid: Left = item info, Center = Stock/SRP, Right = Photo
        top_grid = ctk.CTkFrame(combined_inner, fg_color="transparent")
        top_grid.pack(fill="x", pady=(0, 10))
        top_grid.grid_columnconfigure(0, weight=0)
        top_grid.grid_columnconfigure(1, weight=1)
        top_grid.grid_columnconfigure(2, weight=0)

        # Left: Product title (moved from separate title section)
        title_left = ctk.CTkFrame(top_grid, fg_color="transparent")
        title_left.grid(row=0, column=0, sticky="w")

        self.header_label = ctk.CTkLabel(
            title_left,
            text="",
            font=("Poppins", 20, "bold"),
            text_color="#FFFFFF"
        )
        self.header_label.pack(anchor="w")

        self.sub_header_label = ctk.CTkLabel(
            title_left,
            text="",
            font=("Poppins", 20),
            text_color="#CCCCCC"
        )
        self.sub_header_label.pack(anchor="w", pady=(5, 0))

        # Center: Stock Count + SRP (kept centered)
        stock_srp_frame = ctk.CTkFrame(top_grid, fg_color="transparent")
        stock_srp_frame.grid(row=0, column=1)

        self.stock_label = ctk.CTkLabel(
            stock_srp_frame,
            text="",
            font=("Poppins", 28, "bold"),
            text_color="#FFFFFF",
            cursor="hand2"
        )
        self.stock_label.pack(anchor="center")
        self.stock_label.bind("<Button-1>", self.open_stock_settings)

        self.srp_display = ctk.CTkLabel(
            stock_srp_frame,
            textvariable=self.srp_var,
            font=("Poppins", 24, "bold"),
            text_color="#FFFFFF"
        )
        self.srp_display.pack(anchor="center", pady=(10, 0))

        self.srp_entry = ctk.CTkEntry(
            stock_srp_frame,
            textvariable=self.srp_var,
            font=("Poppins", 16),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=40,
            width=150,
            justify="center"
        )

        # Right: Photo thumbnail and Upload button inside fixed 100x100 container
        photo_container2 = ctk.CTkFrame(top_grid, fg_color="transparent", width=100, height=100)
        photo_container2.grid(row=0, column=2, sticky="e")
        photo_container2.grid_propagate(False)

        photo_frame2 = ctk.CTkFrame(photo_container2, width=100, height=100, fg_color="#374151", corner_radius=20)
        photo_frame2.pack_propagate(False)
        photo_frame2.pack(fill="both", expand=True)

        self.photo_label = ctk.CTkLabel(
            photo_frame2,
            text="📷",
            font=("Poppins", 30),
            text_color="#CCCCCC",
            cursor="hand2"
        )
        self.photo_label.pack(fill="both", expand=True)
        self.photo_label.bind("<Button-1>", self.show_photo_menu)

        # Upload button inside the same 100x100 container, fixed width and height
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

        # Bottom row: Location + Notes + Edit in one line
        bottom_row = ctk.CTkFrame(combined_inner, fg_color="transparent")
        bottom_row.pack(fill="x")
        bottom_row.grid_columnconfigure(0, weight=0)
        bottom_row.grid_columnconfigure(1, weight=1)
        bottom_row.grid_columnconfigure(2, weight=0)

        # Location
        loc_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        loc_frame.grid(row=0, column=0, sticky="w", padx=(0, 12))

        ctk.CTkLabel(
            loc_frame,
            text="LOCATION",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", pady=(0, 5))

        self.location_entry = ctk.CTkEntry(
            loc_frame,
            textvariable=self.location_var,
            font=("Poppins", 12),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            width=120,
            state="readonly"
        )
        self.location_entry.pack()

        # Notes
        notes_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        notes_frame.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        ctk.CTkLabel(
            notes_frame,
            text="NOTES",
            font=("Poppins", 14, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", pady=(0, 5))

        self.notes_entry = ctk.CTkEntry(
            notes_frame,
            textvariable=self.notes_var,
            font=("Poppins", 12),
            fg_color="#374151",
            text_color="#FFFFFF",
            corner_radius=20,
            height=35,
            state="readonly"
        )
        self.notes_entry.pack(fill="x")

        # Edit button moved to the same line (right side)
        edit_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        edit_frame.grid(row=0, column=2, sticky="e")

        self.edit_btn = ctk.CTkButton(
            edit_frame,
            text="Edit",
            font=("Poppins", 14, "bold"),
            fg_color="#4B5563",
            hover_color="#6B7280",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=40,
            command=self.toggle_edit_mode
        )
        self.edit_btn.pack()

        self.save_status_label = ctk.CTkLabel(
            edit_frame,
            text="",
            font=("Poppins", 12, "italic"),
            text_color="#22C55E"
        )
        self.save_status_label.pack(pady=(6, 0))

        # === Transaction History Section (WITH SCROLLBAR ONLY HERE) ===
        history_section = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=40)
        history_section.pack(fill="both", expand=True)

        # Section header
        history_header = ctk.CTkFrame(history_section, fg_color="transparent")
        history_header.pack(fill="x", padx=30, pady=(30, 10))

        ctk.CTkLabel(
            history_header,
            text="TRANSACTION HISTORY",
            font=("Poppins", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        # Table container (SCROLLBAR ONLY FOR TABLE)
        table_container = ctk.CTkFrame(history_section, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        # Style the treeview to match your app
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Transaction.Treeview",
                        background="#2b2b2b",
                        foreground="#FFFFFF",
                        fieldbackground="#2b2b2b",
                        font=("Poppins", 11),
                        rowheight=35)
        style.configure("Transaction.Treeview.Heading",
                        background="#000000",
                        foreground="#D00000",
                        font=("Poppins", 11, "bold"))
        style.map("Transaction.Treeview", background=[("selected", "#374151")])
        style.map("Transaction.Treeview.Heading", background=[("active", "#111111")])

        # Create treeview
        self.tree = ttk.Treeview(
            table_container,
            columns=("date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings",
            style="Transaction.Treeview"
        )

        # Configure columns
        column_config = {
            "date": {"text": "DATE", "anchor": "center", "width": 90},
            "qty_restock": {"text": "QTY RESTOCK", "anchor": "center", "width": 100},
            "cost": {"text": "COST", "anchor": "center", "width": 80},
            "name": {"text": "NAME", "anchor": "w", "width": 200},
            "qty": {"text": "QTY SOLD", "anchor": "center", "width": 80},
            "price": {"text": "PRICE", "anchor": "center", "width": 80},
            "stock": {"text": "STOCK", "anchor": "center", "width": 80},
        }

        for col in self.tree["columns"]:
            config = column_config[col]
            self.tree.heading(col, text=config["text"])
            self.tree.column(col, anchor=config["anchor"], width=config["width"])

        # Configure tags for different transaction types
        self.tree.tag_configure("red", foreground="#EF4444")    # Sales
        self.tree.tag_configure("blue", foreground="#3B82F6")   # Restocks
        self.tree.tag_configure("green", foreground="#22C55E")  # Actual

        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

    def show_save_status(self, message="Saved!", duration=2000):
        self.save_status_label.configure(text=message)
        self.after(duration, lambda: self.save_status_label.configure(text=""))

    def set_details(self, details, main_app):
        self.details = details
        self.main_app = main_app
        self.srp_var.set(f"₱{details['price']:.2f}")
        self.image_path = self.get_existing_image_path()
        self.load_location()
        self.load_transactions()
        self.load_photo()

    def get_existing_image_path(self):
        photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
        os.makedirs(photos_dir, exist_ok=True)
        base = f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{self.details['th']}"
        for ext in [".jpg", ".jpeg", ".png"]:
            full_path = os.path.join(photos_dir, base + ext)
            if os.path.exists(full_path):
                return full_path
        return os.path.join(photos_dir, base + ".jpg")

    def toggle_edit_mode(self):
        if not self.edit_mode:
            # Enter edit mode
            self.location_entry.configure(state="normal")
            self.notes_entry.configure(state="normal")
            self.srp_display.pack_forget()
            self.srp_entry.pack(anchor="center")
            self.srp_var.set(self.srp_var.get().replace("₱", "").strip())
            self.edit_btn.configure(text="Save", fg_color="#22C55E", hover_color="#16A34A")
        else:
            # Save and exit edit mode
            self.save_location()
            self.save_srp()
            self.save_notes()
            self.location_entry.configure(state="readonly")
            self.notes_entry.configure(state="readonly")
            self.srp_entry.pack_forget()
            self.srp_display.pack(anchor="center", pady=(10, 0))
            self.edit_btn.configure(text="Edit", fg_color="#4B5563", hover_color="#6B7280")
            self.show_save_status()
        self.edit_mode = not self.edit_mode

    def load_transactions(self):
        with db_cursor() as cur:
            cur.execute("""
                SELECT t.date, t.name, t.quantity, t.price, t.is_restock, p.brand
                FROM transactions t
                JOIN products p ON t.type = p.type AND t.id_size = p.id AND t.od_size = p.od AND t.th_size = p.th
                WHERE t.type=? AND t.id_size=? AND t.od_size=? AND t.th_size=?
                ORDER BY t.date ASC
            """, (self.details["type"], self.details["id"], self.details["od"], self.details["th"]))
            rows = cur.fetchall()

        # Update header labels with LARGER and more prominent display
        self.header_label.configure(
            text=f"{self.details['type']} {self.details['id']}-{self.details['od']}-{self.details['th']} {self.details['brand']}"
        )

        part = self.details['part_no'].strip()
        country = self.details['country_of_origin'].strip()
        subtitle = f"{part} | {country}" if part else country
        self.sub_header_label.configure(text=subtitle)

        # Clear existing items
        self.tree.delete(*self.tree.get_children())

        running_stock = 0
        for row in rows:
            date, name, qty, price, is_restock, brand = row

            # Handle 'Actual' transactions correctly
            if is_restock == 2:  # 2 is for 'Actual'
                running_stock = qty  # Reset stock to this new value
            else:  # Restock (1) or Sale (0)
                running_stock += qty

            date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%y")

            qty_restock = ""
            cost = ""
            price_str = ""
            display_qty = ""
            tag = ""

            if is_restock == 1:  # Restock
                qty_restock = qty
                cost = f"₱{price:.2f}"
                tag = "blue"
            elif is_restock == 0:  # Sale
                display_qty = abs(qty)
                price_str = f"₱{price:.2f}"
                tag = "red"
            elif is_restock == 2:  # Actual
                tag = "green"

            self.tree.insert("", 0, values=(
                date_str, qty_restock, cost, name, display_qty, price_str, running_stock
            ), tags=(tag,))

        # Update stock display
        with db_cursor() as cur:
            cur.execute("""SELECT low_threshold, warn_threshold FROM products
                         WHERE type=? AND id=? AND od=? AND th=? AND brand=?""",
                         (self.details["type"], self.details["id"], self.details["od"],
                          self.details["th"], self.details["brand"]))
            thresholds = cur.fetchone()

        low = thresholds[0] if thresholds and thresholds[0] is not None else 0
        warn = thresholds[1] if thresholds and thresholds[1] is not None else 5
        stock = running_stock

        if stock <= low:
            color = "#EF4444"  # Red
        elif stock <= warn:
            color = "#F59E0B"  # Orange
        else:
            color = "#22C55E"  # Green

        self.stock_label.configure(text=f"STOCK: {stock}", text_color=color)

    def load_location(self):
        with db_cursor() as cur:
            cur.execute("""
                SELECT location, notes FROM products
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """, (self.details["type"], self.details["id"], self.details["od"],
                  self.details["th"], self.details["part_no"]))
            row = cur.fetchone()
            if row:
                self.location_var.set(row[0] or "Drawer 1")
                self.notes_var.set(row[1] or "")

    def save_location(self):
        with db_cursor() as cur:
            cur.execute("""
                UPDATE products SET location=?
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """, (self.location_var.get().strip(), self.details["type"], self.details["id"],
                  self.details["od"], self.details["th"], self.details["part_no"]))
        if self.main_app:
            self.main_app.refresh_product_list()

    def save_srp(self):
        try:
            new_price = float(self.srp_var.get())
            self.srp_var.set(f"₱{new_price:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Invalid price")
            return

        with db_cursor() as cur:
            cur.execute("""
                UPDATE products SET price=?
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """, (new_price, self.details["type"], self.details["id"], self.details["od"],
                  self.details["th"], self.details["part_no"]))
        if self.main_app:
            self.main_app.refresh_product_list()

    def save_notes(self):
        with db_cursor() as cur:
            cur.execute("""
                UPDATE products SET notes=?
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """, (self.notes_var.get().strip(), self.details["type"], self.details["id"],
                  self.details["od"], self.details["th"], self.details["part_no"]))
        if self.main_app:
            self.main_app.refresh_product_list()

    def open_stock_settings(self, event=None):
        # Create custom stock settings window matching your app style
        settings = ctk.CTkToplevel(self)
        settings.title("Stock Color Settings")
        settings.geometry("400x300")
        settings.resizable(False, False)
        settings.configure(fg_color="#000000")

        # Center the window
        settings.transient(self)
        settings.grab_set()

        # Main container
        main_frame = ctk.CTkFrame(settings, fg_color="#2b2b2b", corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        ctk.CTkLabel(
            main_frame,
            text="Stock Threshold Settings",
            font=("Poppins", 20, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=(30, 20))

        # Form container
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=(0, 20))

        low_var = tk.IntVar()
        warn_var = tk.IntVar()

        # Get current values
        with db_cursor() as cur:
            cur.execute("""
                SELECT low_threshold, warn_threshold FROM products
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """, (self.details["type"], self.details["id"], self.details["od"],
                  self.details["th"], self.details["part_no"]))
            row = cur.fetchone()

        low_var.set(row[0] if row and row[0] is not None else 0)
        warn_var.set(row[1] if row and row[1] is not None else 5)

        # Low threshold
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

        # Warning threshold
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

        # Buttons
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        def save_thresholds():
            with db_cursor() as cur:
                cur.execute("""
                    UPDATE products SET low_threshold=?, warn_threshold=?
                    WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
                """, (low_var.get(), warn_var.get(),
                      self.details["type"], self.details["id"], self.details["od"],
                      self.details["th"], self.details["part_no"]))
            settings.destroy()
            self.load_transactions()

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
            command=settings.destroy
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
            command=save_thresholds
        ).pack(side="right")

    def upload_photo(self):
        # Changed from checking type == "SPECIAL" to checking brand == "MOS"
        if self.details["brand"].upper() != "MOS":
            messagebox.showinfo("Not Allowed", "Photo upload is only allowed for MOS brand products.")
            return

        if 'brand' not in self.details:
            messagebox.showerror("Error", "Product details missing 'brand' information.")
            return

        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if not file_path:
            return  # User cancelled

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            messagebox.showerror("Invalid File", "Only .jpg, .jpeg, .png are supported.")
            return

        photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
        safe_th = self.details['th'].replace('/', 'x')
        safe_brand = self.details['brand'].replace('/', 'x').replace(' ', '_')  # Sanitize brand for filename
        filename = f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{safe_th}-{safe_brand}{ext}"
        save_path = os.path.join(photos_dir, filename)

        img = Image.open(file_path).convert("RGB")
        quality = 95
        while True:
            img.save(save_path, format="JPEG", quality=quality)
            if os.path.getsize(save_path) <= 5 * 1024 * 1024 or quality <= 60:
                break
            quality -= 5

        # Remove old photo files (without brand in filename)
        base_old = f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{self.details['th']}"
        for old_ext in [".jpg", ".jpeg", ".png"]:
            old_path = os.path.join(photos_dir, base_old + old_ext)
            if os.path.exists(old_path):
                os.remove(old_path)

        self.image_path = save_path
        self.load_photo()

    def load_photo(self):
        self.image_path = self.get_photo_path_by_type()

        if os.path.exists(self.image_path):
            img = Image.open(self.image_path)
            img.thumbnail((80, 80))

            ctk_img = CTkImage(light_image=img, size=img.size)
            self.image_thumbnail = ctk_img
            self.photo_label.configure(image=ctk_img, text="")

            # Changed from checking type == "SPECIAL" to checking brand == "MOS"
            if self.details["brand"].upper() == "MOS":
                self.upload_button.pack_forget()
            else:
                self.upload_button.pack_forget()  # No upload button for other brands
        else:
            self.photo_label.configure(image=None, text="📷")
            # Changed from checking type == "SPECIAL" to checking brand == "MOS"
            if self.details["brand"].upper() == "MOS":
                self.upload_button.pack(pady=(5, 0))
            else:
                self.upload_button.pack_forget()

    def show_photo_menu(self, event=None):
        if not os.path.exists(self.image_path):
            # If no photo exists, just show fullscreen placeholder or return
            if self.details["brand"].upper() == "MOS":
                return  # No photo to show for MOS without image
            else:
                # For other brands, show fullscreen photo (shared or placeholder)
                self.show_fullscreen_photo()
                return

        # Changed from checking type == "SPECIAL" to checking brand == "MOS"
        # If item is not MOS brand, just open photo immediately
        if self.details["brand"].upper() != "MOS":
            self.show_fullscreen_photo()
            return

        # Create custom menu popup matching your app style for MOS brand
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(fg_color="#2b2b2b")

        # Position popup near the photo
        x = self.photo_label.winfo_rootx() + self.photo_label.winfo_width() // 2 - 60
        y = self.photo_label.winfo_rooty() + self.photo_label.winfo_height() + 5
        popup.geometry(f"120x80+{x}+{y}")

        def close_menu(event=None):
            if popup and popup.winfo_exists():
                popup.destroy()

        def view():
            close_menu()
            self.show_fullscreen_photo()

        def delete():
            close_menu()
            if messagebox.askyesno("Delete Photo", "Are you sure you want to delete this photo?"):
                os.remove(self.image_path)
                self.load_photo()

        # Menu buttons
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

        # Changed from checking type == "SPECIAL" to checking brand == "MOS"
        if self.details["brand"].upper() == "MOS":
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

    def get_photo_path_by_type(self):
        photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
        # Changed from checking type == "SPECIAL" to checking brand == "MOS"
        # For MOS brand, use current product photo logic with brand
        if self.details["brand"].upper() == "MOS":
            if 'brand' not in self.details:
                return "" # Cannot find image if brand is missing in details
            safe_th = self.details['th'].replace('/', 'x')
            safe_brand = self.details['brand'].replace('/', 'x').replace(' ', '_')
            for ext in [".jpg", ".jpeg", ".png"]:
                path = os.path.join(photos_dir, f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{safe_th}-{safe_brand}{ext}")
                if os.path.exists(path):
                    return path
            return ""  # No photo found for MOS with brand
        else:
            # For other brands: shared photo by type with .jpg or .png fallback
            for ext in [".jpg", ".png"]:
                path = os.path.join(photos_dir, f"{self.details['type'].lower()}{ext}")
                if os.path.exists(path):
                    return path
            # Placeholder fallback path (adjust to your placeholder image location)
            placeholder = os.path.join(photos_dir, "placeholder.png")
            return placeholder if os.path.exists(placeholder) else ""

    def show_fullscreen_photo(self):
        if not os.path.exists(self.image_path):
            return  # No photo to show

        # Create custom fullscreen photo viewer matching your app style
        photo_viewer = ctk.CTkToplevel(self)
        photo_viewer.title("Photo Viewer")
        photo_viewer.transient(self)
        photo_viewer.grab_set()
        photo_viewer.configure(fg_color="#000000")

        # Get screen dimensions for proper sizing
        screen_width = photo_viewer.winfo_screenwidth()
        screen_height = photo_viewer.winfo_screenheight()

        # Set window size to 80% of screen dimensions
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)

        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        photo_viewer.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Main container
        container = ctk.CTkFrame(photo_viewer, fg_color="#000000")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Load and scale image to fit window while maintaining aspect ratio
        img = Image.open(self.image_path)

        # Calculate available space for image (accounting for padding and labels)
        available_width = window_width - 80  # Account for padding
        available_height = window_height - 120  # Account for padding and labels

        # Get original image dimensions
        orig_width, orig_height = img.size

        # Calculate scaling factor to fit image in available space
        width_ratio = available_width / orig_width
        height_ratio = available_height / orig_height
        scale_factor = min(width_ratio, height_ratio)

        # Calculate new dimensions
        new_width = int(orig_width * scale_factor)
        new_height = int(orig_height * scale_factor)

        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = CTkImage(light_image=img, size=img.size)

        # Image label - centered
        image_frame = ctk.CTkFrame(container, fg_color="#000000")
        image_frame.pack(fill="both", expand=True)

        label = ctk.CTkLabel(
            image_frame,
            image=photo,
            text="",
            cursor="hand2"
        )
        label.image = photo  # Keep reference so image displays
        label.pack(expand=True)  # Center the image
        label.bind("<Button-1>", lambda e: photo_viewer.destroy())  # Click photo to close

        # Instructions container
        instruction_frame = ctk.CTkFrame(container, fg_color="transparent")
        instruction_frame.pack(fill="x", pady=(10, 0))

        # Close instruction
        ctk.CTkLabel(
            instruction_frame,
            text="Click image or press ESC to close",
            font=("Poppins", 12),
            text_color="#CCCCCC"
        ).pack()

        # Close button
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

        # Bind ESC key to close
        photo_viewer.bind("<Escape>", lambda e: photo_viewer.destroy())
        photo_viewer.focus_set()