import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from ..database import connect_db
from PIL import Image, ImageTk
from contextlib import contextmanager
import os

@contextmanager
def db_cursor():
    conn = connect_db()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        conn.close()

class TransactionWindow(tk.Frame):
    def __init__(self, parent, details, controller, return_to):
        super().__init__(parent)
        self.controller = controller
        self.return_to = return_to  # ← store the page we came from
        self.main_app = None

        self.configure(bg="white")

        self.srp_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.edit_mode = False
        self.image_path = ""
        self.image_thumbnail = None

        self._build_ui()

    def _build_ui(self):
        # Back button (aligned with InventoryApp)
        back_btn = tk.Button(self, text="← Back", anchor="w", padx=10, pady=5)
        if self.controller:
            back_btn.config(command=lambda: self.controller.show_frame(self.return_to))

        else:
            back_btn.config(command=self.master.destroy)
        back_btn.pack(anchor="nw", padx=10, pady=(10, 0))

        # Header layout: title block | photo + stock
        header = tk.Frame(self, bg="white")
        header.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Title + subtitle container (centered)
        title_frame = tk.Frame(header, bg="white")
        title_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.header_label = tk.Label(title_frame, font=("Arial", 20, "bold"), bg="white", anchor="center")
        self.header_label.pack()

        self.sub_header_label = tk.Label(title_frame, font=("Arial", 16), bg="white", anchor="center")
        self.sub_header_label.pack()

        # Right section: thumbnail + stock
        right_section = tk.Frame(header, bg="white")
        right_section.pack(side=tk.RIGHT)

        photo_frame = tk.Frame(right_section, width=80, height=80, bg="#eee")
        photo_frame.pack_propagate(False)
        photo_frame.pack()

        self.photo_label = tk.Label(photo_frame, bg="#ddd", relief="ridge", cursor="hand2")
        self.photo_label.pack(fill=tk.BOTH, expand=True)
        self.photo_label.bind("<Button-1>", self.show_photo_menu)

        self.upload_button = tk.Button(photo_frame, text="Upload", command=self.upload_photo)
        self.upload_button.pack()

        self.stock_label = tk.Label(right_section, font=("Arial", 14, "bold underline"), cursor="hand2", bg="white")
        self.stock_label.pack(pady=(5, 0))
        self.stock_label.bind("<Button-1>", self.open_stock_settings)

        # Next section
        sub = tk.Frame(self, bg="white")
        sub.pack(fill=tk.X, padx=10, pady=(0, 5))

        tk.Label(sub, text="LOC:", bg="white").pack(side=tk.LEFT, padx=(0, 2))
        self.location_entry = tk.Entry(sub, textvariable=self.location_var, width=12, state="readonly", relief="flat")
        self.location_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(sub, text="NOTES:", bg="white").pack(side=tk.LEFT, padx=(0, 2))
        self.notes_entry = tk.Entry(sub, textvariable=self.notes_var, state="readonly", relief="flat")
        self.notes_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        right_frame = tk.Frame(sub, bg="white")
        right_frame.pack(side=tk.RIGHT)

        self.edit_btn = tk.Button(right_frame, text="Edit", command=self.toggle_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.save_status_label = tk.Label(right_frame, text="", fg="green", bg="white", font=("Arial", 10, "italic"))
        self.save_status_label.pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(right_frame, text="SRP:", font=("Arial", 14, "bold"), bg="white").pack(side=tk.LEFT, padx=(0, 2))
        self.srp_display = tk.Label(right_frame, textvariable=self.srp_var, font=("Arial", 14, "bold"), bg="white")
        self.srp_display.pack(side=tk.LEFT)

        self.srp_entry = tk.Entry(right_frame, textvariable=self.srp_var, width=10)

        self.tree = ttk.Treeview(
            self,
            columns=("date", "qty_restock", "cost", "name", "qty", "price", "stock"),
            show="headings",
            height=20
        )

        column_config = {
            "date": {"anchor": "center", "width": 90},
            "qty_restock": {"anchor": "center", "width": 60},
            "cost": {"anchor": "center", "width": 80},
            "name": {"anchor": "w", "width": 200},
            "qty": {"anchor": "center", "width": 60},
            "price": {"anchor": "center", "width": 80},
            "stock": {"anchor": "center", "width": 80},
        }

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.upper().replace("_", " "))
            self.tree.column(col, **column_config[col])

        self.tree.tag_configure("red", foreground="red")
        self.tree.tag_configure("blue", foreground="blue")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


    def show_save_status(self, message="Saved!", duration=2000):
        self.save_status_label.config(text=message)
        self.after(duration, lambda: self.save_status_label.config(text=""))

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
            self.location_entry.config(state="normal", relief="sunken")
            self.notes_entry.config(state="normal", relief="sunken")
            self.srp_display.pack_forget()
            self.srp_entry.pack(side=tk.LEFT)
            self.srp_var.set(self.srp_var.get().replace("₱", "").strip())
            self.edit_btn.config(text="Save")
        else:
            self.save_location()
            self.save_srp()
            self.save_notes()
            self.location_entry.config(state="readonly", relief="flat")
            self.notes_entry.config(state="readonly", relief="flat")
            self.srp_entry.pack_forget()
            self.srp_display.pack(side=tk.LEFT)
            self.edit_btn.config(text="Edit")
            self.show_save_status()  # ← Show the "Saved!" message
        self.edit_mode = not self.edit_mode

    def load_transactions(self):
        with db_cursor() as cur:
            cur.execute("""SELECT date, name, quantity, price, is_restock FROM transactions
                        WHERE type=? AND id_size=? AND od_size=? AND th_size=?
                        ORDER BY date ASC""",
                        (self.details["type"], self.details["id"], self.details["od"], self.details["th"]))
            rows = cur.fetchall()

        self.header_label.config(
            text=f"{self.details['type']} {self.details['id']}-{self.details['od']}-{self.details['th']} {self.details['brand']}"
        )

        part = self.details['part_no'].strip()
        country = self.details['country_of_origin'].strip()
        subtitle = f"{part} | {country}" if part else country
        self.sub_header_label.config(text=subtitle)

        stock_by_row = []
        running_stock = 0
        for row in rows:
            qty = row[2]
            running_stock += qty
            stock_by_row.append((row, running_stock))

        self.tree.delete(*self.tree.get_children())

        for row, stock in reversed(stock_by_row):
            date, name, qty, price, is_restock = row
            date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%y")
            qty_restock = qty if is_restock else ""
            cost = f"₱{price:.2f}" if is_restock else ""
            price_str = f"₱{price:.2f}" if not is_restock else ""
            display_qty = abs(qty) if not is_restock else ""
            tag = "blue" if is_restock else "red"

            self.tree.insert("", tk.END, values=(date_str, qty_restock, cost, name, display_qty, price_str, abs(stock)), tags=(tag,))

        with db_cursor() as cur:
            cur.execute("""SELECT low_threshold, warn_threshold FROM products
                        WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                        (self.details["type"], self.details["id"], self.details["od"],
                        self.details["th"], self.details["part_no"]))
            thresholds = cur.fetchone()

        low = thresholds[0] if thresholds else 0
        warn = thresholds[1] if thresholds else 5
        stock = abs(running_stock)

        color = "green"
        if stock <= low:
            color = "red"
        elif stock <= warn:
            color = "orange"

        self.stock_label.config(text=f"STOCK: {stock}", fg=color)

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
        settings = tk.Toplevel(self)
        settings.title("Stock Color Settings")
        settings.geometry("250x150")
        settings.resizable(False, False)

        tk.Label(settings, text="Low Threshold (Red):").pack(pady=(10, 0))
        low_var = tk.IntVar()
        warn_var = tk.IntVar()

        with db_cursor() as cur:
            cur.execute("""
                SELECT low_threshold, warn_threshold FROM products
                WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
            """, (self.details["type"], self.details["id"], self.details["od"],
                  self.details["th"], self.details["part_no"]))
            row = cur.fetchone()

        low_var.set(row[0] if row else 0)
        warn_var.set(row[1] if row else 5)

        tk.Entry(settings, textvariable=low_var).pack()
        tk.Label(settings, text="Warning Threshold (Orange):").pack(pady=(10, 0))
        tk.Entry(settings, textvariable=warn_var).pack()

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

        tk.Button(settings, text="Save", command=save_thresholds).pack(pady=10)

    def upload_photo(self):
        if self.details["type"].upper() != "SPECIAL":
            messagebox.showinfo("Not Allowed", "Photo upload is only allowed for SPECIAL type products.")
            return

        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if not file_path:
            return  # User cancelled

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            messagebox.showerror("Invalid File", "Only .jpg, .jpeg, .png are supported.")
            return

        photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
        filename = f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{self.details['th']}{ext}"
        save_path = os.path.join(photos_dir, filename)

        img = Image.open(file_path).convert("RGB")
        quality = 95
        while True:
            img.save(save_path, format="JPEG", quality=quality)
            if os.path.getsize(save_path) <= 5 * 1024 * 1024 or quality <= 60:
                break
            quality -= 5

        for old_ext in [".jpg", ".jpeg", ".png"]:
            old_path = os.path.join(photos_dir, f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{self.details['th']}{old_ext}")
            if old_path != save_path and os.path.exists(old_path):
                os.remove(old_path)

        self.image_path = save_path
        self.load_photo()

    def load_photo(self):
        self.image_path = self.get_photo_path_by_type()

        if os.path.exists(self.image_path):
            img = Image.open(self.image_path)
            img.thumbnail((60, 60))
            self.image_thumbnail = ImageTk.PhotoImage(img)
            self.photo_label.config(image=self.image_thumbnail)
            if self.details["type"].upper() == "SPECIAL":
                self.upload_button.pack_forget()
            else:
                self.upload_button.pack_forget()  # No upload button for other types
        else:
            self.photo_label.config(image="", bg="#ddd")
            if self.details["type"].upper() == "SPECIAL":
                self.upload_button.pack()
            else:
                self.upload_button.pack_forget()

    def show_photo_menu(self, event=None):
        if not os.path.exists(self.image_path):
            return

        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.geometry(f"+{event.x_root}+{event.y_root}")
        popup.attributes("-topmost", True)

        def view():
            popup.destroy()
            self.show_fullscreen_photo()

        def delete():
            popup.destroy()
            if messagebox.askyesno("Delete Photo", "Are you sure you want to delete this photo?"):
                os.remove(self.image_path)
                self.load_photo()

        tk.Button(popup, text="🔍 View", command=view, width=10).pack()

        if self.details["type"].upper() == "SPECIAL":
            tk.Button(popup, text="🗑 Delete", command=delete, width=10).pack()

    def get_photo_path_by_type(self):
        photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
        # For special type, use current product photo logic
        if self.details["type"].upper() == "SPECIAL":
            # Return current product photo path
            for ext in [".jpg", ".jpeg", ".png"]:
                path = os.path.join(photos_dir, f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{self.details['th']}{ext}")
                if os.path.exists(path):
                    return path
            return ""  # No photo found for special
        else:
            # For other types: shared photo by type with .jpg or .png fallback
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

        top = tk.Toplevel(self)
        top.title("Photo Viewer")
        top.transient(self)
        top.grab_set()
        top.resizable(False, False)

        img = Image.open(self.image_path)
        img.thumbnail((800, 800))
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(top, image=photo)
        label.image = photo  # Keep reference so image displays
        label.pack(padx=10, pady=10)
        label.bind("<Button-1>", lambda e: top.destroy())  # Click photo to close

        top.update_idletasks()
        w = top.winfo_width()
        h = top.winfo_height()
        ws = top.winfo_screenwidth()
        hs = top.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        top.geometry(f"{w}x{h}+{x}+{y}")