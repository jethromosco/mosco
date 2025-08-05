import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from database import connect_db
from PIL import Image, ImageTk
import os

class TransactionWindow(tk.Frame):
    def __init__(self, parent, details, controller):
        super().__init__(parent)
        self.controller = controller
        self.details = None
        self.main_app = None

        self.configure(bg="white")

        self.srp_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.edit_mode = False
        self.image_path = ""
        self.image_ext = ""
        self.image_thumbnail = None

        # Header
        header = tk.Frame(self, bg="white")
        header.pack(fill=tk.X, pady=5, padx=10)

        # Static Back to InventoryApp
        if self.controller:
            back_button = tk.Button(header, text="← Back", command=self.controller.show_inventory_app)
        else:
            back_button = tk.Button(header, text="← Back", command=self.master.destroy)

        back_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stock_label = tk.Label(header, font=("Arial", 14, "bold underline"), cursor="hand2", bg="white")
        self.stock_label.pack(side=tk.RIGHT, padx=(0, 10))
        self.stock_label.bind("<Button-1>", self.open_stock_settings)

        photo_frame = tk.Frame(header, width=60, height=60, bg="white")
        photo_frame.pack_propagate(False)
        photo_frame.pack(side=tk.RIGHT, padx=(0, 5))

        self.photo_label = tk.Label(photo_frame, bg="#ddd", relief="ridge", cursor="hand2")
        self.photo_label.pack(fill=tk.BOTH, expand=True)
        self.photo_label.bind("<Button-1>", self.show_photo_menu)

        self.upload_button = tk.Button(photo_frame, text="Upload", command=self.upload_photo)
        self.upload_button.pack()

        self.header_label = tk.Label(header, font=("Arial", 16, "bold"), bg="white")
        self.header_label.pack(side=tk.LEFT)

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
        self.image_path, self.image_ext = self.get_existing_image_path()
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
                return full_path, ext
        return os.path.join(photos_dir, base + ".jpg"), ".jpg"

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

    def load_location(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""SELECT location, notes FROM products WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                    (self.details["type"], self.details["id"], self.details["od"], self.details["th"], self.details["part_no"]))
        row = cur.fetchone()
        if row:
            self.location_var.set(row[0] or "Drawer 1")
            self.notes_var.set(row[1] or "")
        conn.close()

    def save_location(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""UPDATE products SET location=? WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                    (self.location_var.get().strip(), self.details["type"], self.details["id"],
                     self.details["od"], self.details["th"], self.details["part_no"]))
        conn.commit()
        conn.close()
        self.main_app.refresh_product_list()

    def save_srp(self):
        try:
            new_price = float(self.srp_var.get())
            self.srp_var.set(f"₱{new_price:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Invalid price")
            return
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""UPDATE products SET price=? WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                    (new_price, self.details["type"], self.details["id"], self.details["od"], self.details["th"], self.details["part_no"]))
        conn.commit()
        conn.close()
        self.main_app.refresh_product_list()

    def save_notes(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""UPDATE products SET notes=? WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                    (self.notes_var.get().strip(), self.details["type"], self.details["id"], self.details["od"],
                     self.details["th"], self.details["part_no"]))
        conn.commit()
        conn.close()
        self.main_app.refresh_product_list()

    def load_transactions(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""SELECT date, name, quantity, price, is_restock FROM transactions
                       WHERE type=? AND id_size=? AND od_size=? AND th_size=?
                       ORDER BY date ASC""",
                    (self.details["type"], self.details["id"], self.details["od"], self.details["th"]))
        rows = cur.fetchall()
        conn.close()

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

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""SELECT low_threshold, warn_threshold FROM products
                       WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                    (self.details["type"], self.details["id"], self.details["od"],
                     self.details["th"], self.details["part_no"]))
        thresholds = cur.fetchone()
        conn.close()

        low = thresholds[0] if thresholds else 0
        warn = thresholds[1] if thresholds else 5
        stock = abs(running_stock)

        color = "green"
        if stock <= low:
            color = "red"
        elif stock <= warn:
            color = "orange"

        self.stock_label.config(text=f"STOCK: {stock}", fg=color)
        self.header_label.config(
            text=f"{self.details['type']} {self.details['id']}-{self.details['od']}-{self.details['th']} | "
                 f"{self.details['brand']} | {self.details['part_no']} | {self.details['country_of_origin']}")

    def open_stock_settings(self, event=None):
        settings = tk.Toplevel(self)
        settings.title("Stock Color Settings")
        settings.geometry("250x150")
        settings.resizable(False, False)

        tk.Label(settings, text="Low Threshold (Red):").pack(pady=(10, 0))
        low_var = tk.IntVar()
        warn_var = tk.IntVar()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""SELECT low_threshold, warn_threshold FROM products
                       WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                    (self.details["type"], self.details["id"], self.details["od"],
                     self.details["th"], self.details["part_no"]))
        row = cur.fetchone()
        conn.close()

        low_var.set(row[0] if row else 0)
        warn_var.set(row[1] if row else 5)

        tk.Entry(settings, textvariable=low_var).pack()
        tk.Label(settings, text="Warning Threshold (Orange):").pack(pady=(10, 0))
        tk.Entry(settings, textvariable=warn_var).pack()

        def save_thresholds():
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""UPDATE products SET low_threshold=?, warn_threshold=?
                           WHERE type=? AND id=? AND od=? AND th=? AND part_no=?""",
                        (low_var.get(), warn_var.get(),
                         self.details["type"], self.details["id"], self.details["od"],
                         self.details["th"], self.details["part_no"]))
            conn.commit()
            conn.close()
            settings.destroy()
            self.load_transactions()

        tk.Button(settings, text="Save", command=save_thresholds).pack(pady=10)

    def load_photo(self):
        if os.path.exists(self.image_path):
            img = Image.open(self.image_path)
            img.thumbnail((60, 60))
            self.image_thumbnail = ImageTk.PhotoImage(img)
            self.photo_label.config(image=self.image_thumbnail)
            self.upload_button.pack_forget()
        else:
            self.photo_label.config(image="", bg="#ddd")
            self.upload_button.pack()

    def upload_photo(self):
        file = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if not file:
            return

        ext = os.path.splitext(file)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            messagebox.showerror("Invalid File", "Only .jpg, .jpeg, .png are supported.")
            return

        photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
        filename = f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{self.details['th']}{ext}"
        save_path = os.path.join(photos_dir, filename)

        img = Image.open(file).convert("RGB")
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

    def show_fullscreen_photo(self):
        if not os.path.exists(self.image_path):
            return

        top = tk.Toplevel(self)
        top.title("Photo Viewer")
        top.transient(self)
        top.grab_set()
        top.resizable(False, False)

        # Load and resize the image
        img = Image.open(self.image_path)
        img.thumbnail((800, 800))
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(top, image=photo)
        label.image = photo
        label.pack(padx=10, pady=10)
        label.bind("<Button-1>", lambda e: top.destroy())

        # Center the window on the screen
        top.update_idletasks()
        w = top.winfo_width()
        h = top.winfo_height()
        ws = top.winfo_screenwidth()
        hs = top.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        top.geometry(f"{w}x{h}+{x}+{y}")

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
        tk.Button(popup, text="🗑 Delete", command=delete, width=10).pack()
