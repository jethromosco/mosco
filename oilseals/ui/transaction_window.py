import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from PIL import Image
from customtkinter import CTkImage
from typing import Any, Dict, List, Tuple
import os
from ..database import connect_db


def get_existing_image_base(details: Dict[str, Any]) -> str:
	return f"{details['type']}-{details['id']}-{details['od']}-{details['th']}"


def load_transactions_records(details: Dict[str, Any]) -> List[Tuple[Any, ...]]:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				SELECT t.date, t.name, t.quantity, t.price, t.is_restock, p.brand
				FROM transactions t
				JOIN products p ON t.type = p.type AND t.id_size = p.id AND t.od_size = p.od AND t.th_size = p.th
				WHERE t.type=? AND t.id_size=? AND t.od_size=? AND t.th_size=?
				ORDER BY t.date ASC
			""",
			(details["type"], details["id"], details["od"], details["th"]),
		)
		rows = cur.fetchall()
	return rows


def get_thresholds(details: Dict[str, Any]) -> Tuple[int, int]:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""SELECT low_threshold, warn_threshold FROM products
				 WHERE type=? AND id=? AND od=? AND th=? AND brand=?""",
			(details["type"], details["id"], details["od"], details["th"], details["brand"]),
		)
		row = cur.fetchone()
	low = row[0] if row and row[0] is not None else 0
	warn = row[1] if row and row[1] is not None else 5
	return int(low), int(warn)


def get_location_and_notes(details: Dict[str, Any]) -> Tuple[str, str]:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				SELECT location, notes FROM products
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		row = cur.fetchone()
	if not row:
		return "Drawer 1", ""
	return (row[0] or "Drawer 1", row[1] or "")


def update_location(details: Dict[str, Any], new_location: str) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET location=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(new_location.strip(), details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def update_price(details: Dict[str, Any], new_price: float) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET price=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(new_price, details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def update_notes(details: Dict[str, Any], new_notes: str) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET notes=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(new_notes.strip(), details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def update_thresholds(details: Dict[str, Any], low: int, warn: int) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET low_threshold=?, warn_threshold=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(low, warn, details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def summarize_running_stock(rows: List[Tuple[Any, ...]]) -> List[Tuple[str, Any, Any, Any, Any, Any, int]]:
	"""Return list of tuples for display, computing running stock with reset on Actual (is_restock==2)."""
	running_stock = 0
	result = []
	for row in rows:
		date, name, qty, price, is_restock, brand = row
		if is_restock == 2:
			running_stock = int(qty)
		else:
			running_stock += int(qty)
		date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%y")
		qty_restock = ""
		cost = ""
		price_str = ""
		display_qty = ""
		if is_restock == 1:
			qty_restock = qty
			cost = f"₱{float(price):.2f}"
		elif is_restock == 0:
			display_qty = abs(int(qty))
			price_str = f"₱{float(price):.2f}"
		result.append((date_str, qty_restock, cost, name, display_qty, price_str, running_stock))
	return list(reversed(result))


class TransactionWindow(ctk.CTkFrame):
	def __init__(self, parent, details: Dict[str, Any], controller, return_to):
		super().__init__(parent, fg_color="#000000")
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

	def _build_ui(self):
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
			command=lambda: self.controller.show_frame(self.return_to) if self.controller and self.return_to else self.master.destroy()
		)
		back_btn.grid(row=0, column=0, sticky="w", padx=(40, 10), pady=35)

		main_container = ctk.CTkFrame(self, fg_color="#000000")
		main_container.pack(fill="both", expand=True, padx=20, pady=10)

		combined_section = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=40)
		combined_section.pack(fill="x", pady=(0, 10))

		combined_inner = ctk.CTkFrame(combined_section, fg_color="transparent")
		combined_inner.pack(fill="x", padx=20, pady=20)

		top_grid = ctk.CTkFrame(combined_inner, fg_color="transparent")
		top_grid.pack(fill="x", pady=(0, 10))
		top_grid.grid_columnconfigure(0, weight=0)
		top_grid.grid_columnconfigure(1, weight=1)
		top_grid.grid_columnconfigure(2, weight=0)

		title_left = ctk.CTkFrame(top_grid, fg_color="transparent")
		title_left.grid(row=0, column=0, sticky="w")

		self.header_label = ctk.CTkLabel(title_left, text="", font=("Poppins", 20, "bold"), text_color="#FFFFFF")
		self.header_label.pack(anchor="w")
		self.sub_header_label = ctk.CTkLabel(title_left, text="", font=("Poppins", 20), text_color="#CCCCCC")
		self.sub_header_label.pack(anchor="w", pady=(5, 0))

		stock_srp_frame = ctk.CTkFrame(top_grid, fg_color="transparent")
		stock_srp_frame.grid(row=0, column=1)

		self.stock_label = ctk.CTkLabel(stock_srp_frame, text="", font=("Poppins", 28, "bold"), text_color="#FFFFFF", cursor="hand2")
		self.stock_label.pack(anchor="center")
		self.stock_label.bind("<Button-1>", self.open_stock_settings)

		self.srp_display = ctk.CTkLabel(stock_srp_frame, textvariable=self.srp_var, font=("Poppins", 24, "bold"), text_color="#FFFFFF")
		self.srp_display.pack(anchor="center", pady=(10, 0))
		self.srp_entry = ctk.CTkEntry(stock_srp_frame, textvariable=self.srp_var, font=("Poppins", 16), fg_color="#374151", text_color="#FFFFFF", corner_radius=20, height=40, width=150, justify="center")

		photo_container2 = ctk.CTkFrame(top_grid, fg_color="transparent", width=100, height=100)
		photo_container2.grid(row=0, column=2, sticky="e")
		photo_container2.grid_propagate(False)
		photo_frame2 = ctk.CTkFrame(photo_container2, width=100, height=100, fg_color="#374151", corner_radius=20)
		photo_frame2.pack_propagate(False)
		photo_frame2.pack(fill="both", expand=True)
		self.photo_label = ctk.CTkLabel(photo_frame2, text="📷", font=("Poppins", 30), text_color="#CCCCCC", cursor="hand2")
		self.photo_label.pack(fill="both", expand=True)
		self.photo_label.bind("<Button-1>", self.show_photo_menu)
		self.upload_button = ctk.CTkButton(photo_container2, text="Upload", font=("Poppins", 12, "bold"), fg_color="#4B5563", hover_color="#6B7280", text_color="#FFFFFF", corner_radius=20, height=30, width=80, command=self.upload_photo)

		bottom_row = ctk.CTkFrame(combined_inner, fg_color="transparent")
		bottom_row.pack(fill="x")
		bottom_row.grid_columnconfigure(0, weight=0)
		bottom_row.grid_columnconfigure(1, weight=1)
		bottom_row.grid_columnconfigure(2, weight=0)

		loc_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
		loc_frame.grid(row=0, column=0, sticky="w", padx=(0, 12))
		ctk.CTkLabel(loc_frame, text="LOCATION", font=("Poppins", 14, "bold"), text_color="#FFFFFF").pack(anchor="w", pady=(0, 5))
		self.location_entry = ctk.CTkEntry(loc_frame, textvariable=self.location_var, font=("Poppins", 12), fg_color="#374151", text_color="#FFFFFF", corner_radius=20, height=35, width=120, state="readonly")
		self.location_entry.pack()

		notes_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
		notes_frame.grid(row=0, column=1, sticky="ew", padx=(0, 12))
		ctk.CTkLabel(notes_frame, text="NOTES", font=("Poppins", 14, "bold"), text_color="#FFFFFF").pack(anchor="w", pady=(0, 5))
		self.notes_entry = ctk.CTkEntry(notes_frame, textvariable=self.notes_var, font=("Poppins", 12), fg_color="#374151", text_color="#FFFFFF", corner_radius=20, height=35, state="readonly")
		self.notes_entry.pack(fill="x")

		edit_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
		edit_frame.grid(row=0, column=2, sticky="e")
		self.edit_btn = ctk.CTkButton(edit_frame, text="Edit", font=("Poppins", 14, "bold"), fg_color="#4B5563", hover_color="#6B7280", text_color="#FFFFFF", corner_radius=25, width=100, height=40, command=self.toggle_edit_mode)
		self.edit_btn.pack()
		self.save_status_label = ctk.CTkLabel(edit_frame, text="", font=("Poppins", 12, "italic"), text_color="#22C55E")
		self.save_status_label.pack(pady=(6, 0))

		history_section = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=40)
		history_section.pack(fill="both", expand=True)
		history_header = ctk.CTkFrame(history_section, fg_color="transparent")
		history_header.pack(fill="x", padx=30, pady=(30, 10))
		ctk.CTkLabel(history_header, text="TRANSACTION HISTORY", font=("Poppins", 18, "bold"), text_color="#FFFFFF").pack(anchor="w")
		table_container = ctk.CTkFrame(history_section, fg_color="transparent")
		table_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

		style = ttk.Style()
		style.theme_use("clam")
		style.configure("Transaction.Treeview", background="#2b2b2b", foreground="#FFFFFF", fieldbackground="#2b2b2b", font=("Poppins", 11), rowheight=35)
		style.configure("Transaction.Treeview.Heading", background="#000000", foreground="#D00000", font=("Poppins", 11, "bold"))
		style.map("Transaction.Treeview", background=[("selected", "#374151")])
		style.map("Transaction.Treeview.Heading", background=[("active", "#111111")])

		self.tree = ttk.Treeview(table_container, columns=("date", "qty_restock", "cost", "name", "qty", "price", "stock"), show="headings", style="Transaction.Treeview")
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
		for col in self.tree["columns"]:
			config = column_config[col]
			self.tree.heading(col, text=config["text"])
			self.tree.column(col, anchor=config["anchor"], width=config["width"])
		tree_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
		self.tree.configure(yscrollcommand=tree_scrollbar.set)
		self.tree.pack(side="left", fill="both", expand=True)
		tree_scrollbar.pack(side="right", fill="y")

	def show_save_status(self, message="Saved!", duration=2000):
		self.save_status_label.configure(text=message)
		self.after(duration, lambda: self.save_status_label.configure(text=""))

	def set_details(self, details: Dict[str, Any], main_app):
		self.details = details
		self.main_app = main_app
		self.srp_var.set(f"₱{details['price']:.2f}")
		self.image_path = self.get_photo_path_by_type()
		self._load_location()
		self._load_transactions()
		self.load_photo()

	def _load_transactions(self):
		rows = load_transactions_records(self.details)
		self.header_label.configure(text=f"{self.details['type']} {self.details['id']}-{self.details['od']}-{self.details['th']} {self.details['brand']}")
		part = self.details['part_no'].strip()
		country = self.details['country_of_origin'].strip()
		subtitle = f"{part} | {country}" if part else country
		self.sub_header_label.configure(text=subtitle)
		self.tree.delete(*self.tree.get_children())
		for values in summarize_running_stock(rows):
			date_str, qty_restock, cost, name, display_qty, price_str, running_stock = values
			tag = "green" if qty_restock == "" and price_str == "" else ("blue" if qty_restock != "" else "red")
			self.tree.insert("", 0, values=(date_str, qty_restock, cost, name, display_qty, price_str, running_stock), tags=(tag,))
		low, warn = get_thresholds(self.details)
		stock = summarize_running_stock(rows)[0][6] if rows else 0
		color = "#22C55E"
		if stock <= low:
			color = "#EF4444"
		elif stock <= warn:
			color = "#F59E0B"
		self.stock_label.configure(text=f"STOCK: {stock}", text_color=color)

	def _load_location(self):
		location, notes = get_location_and_notes(self.details)
		self.location_var.set(location)
		self.notes_var.set(notes)

	def toggle_edit_mode(self):
		if not self.edit_mode:
			self.location_entry.configure(state="normal")
			self.notes_entry.configure(state="normal")
			self.srp_display.pack_forget()
			self.srp_entry.pack(anchor="center")
			self.srp_var.set(self.srp_var.get().replace("₱", "").strip())
			self.edit_btn.configure(text="Save", fg_color="#22C55E", hover_color="#16A34A")
		else:
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

	def save_location(self):
		update_location(self.details, self.location_var.get())
		if self.main_app:
			self.main_app.refresh_product_list()

	def save_srp(self):
		try:
			new_price = float(self.srp_var.get())
			self.srp_var.set(f"₱{new_price:.2f}")
		except ValueError:
			messagebox.showerror("Error", "Invalid price")
			return
		update_price(self.details, new_price)
		if self.main_app:
			self.main_app.refresh_product_list()

	def save_notes(self):
		update_notes(self.details, self.notes_var.get())
		if self.main_app:
			self.main_app.refresh_product_list()

	def open_stock_settings(self, event=None):
		settings = ctk.CTkToplevel(self)
		settings.title("Stock Color Settings")
		settings.geometry("400x300")
		settings.resizable(False, False)
		settings.configure(fg_color="#000000")
		settings.transient(self)
		settings.grab_set()

		main_frame = ctk.CTkFrame(settings, fg_color="#2b2b2b", corner_radius=40)
		main_frame.pack(fill="both", expand=True, padx=20, pady=20)
		ctk.CTkLabel(main_frame, text="Stock Threshold Settings", font=("Poppins", 20, "bold"), text_color="#FFFFFF").pack(pady=(30, 20))
		form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
		form_frame.pack(fill="x", padx=30, pady=(0, 20))
		low_var = tk.IntVar()
		warn_var = tk.IntVar()
		low, warn = get_thresholds(self.details)
		low_var.set(low)
		warn_var.set(warn)
		ctk.CTkLabel(form_frame, text="LOW THRESHOLD (Red)", font=("Poppins", 14, "bold"), text_color="#FFFFFF").pack(anchor="w", pady=(0, 5))
		low_entry = ctk.CTkEntry(form_frame, textvariable=low_var, font=("Poppins", 12), fg_color="#374151", text_color="#FFFFFF", corner_radius=20, height=35)
		low_entry.pack(fill="x", pady=(0, 15))
		ctk.CTkLabel(form_frame, text="WARNING THRESHOLD (Orange)", font=("Poppins", 14, "bold"), text_color="#FFFFFF").pack(anchor="w", pady=(0, 5))
		warn_entry = ctk.CTkEntry(form_frame, textvariable=warn_var, font=("Poppins", 12), fg_color="#374151", text_color="#FFFFFF", corner_radius=20, height=35)
		warn_entry.pack(fill="x", pady=(0, 20))
		button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
		button_frame.pack(fill="x")
		ctk.CTkButton(button_frame, text="Cancel", font=("Poppins", 14, "bold"), fg_color="#6B7280", hover_color="#4B5563", text_color="#FFFFFF", corner_radius=25, width=100, height=40, command=settings.destroy).pack(side="left", padx=(0, 10))
		ctk.CTkButton(button_frame, text="Save", font=("Poppins", 14, "bold"), fg_color="#22C55E", hover_color="#16A34A", text_color="#FFFFFF", corner_radius=25, width=100, height=40, command=lambda: self._save_thresholds(settings, low_var.get(), warn_var.get())).pack(side="right")

	def _save_thresholds(self, settings, low: int, warn: int):
		update_thresholds(self.details, low, warn)
		settings.destroy()
		self._load_transactions()

	def upload_photo(self):
		if self.details["brand"].upper() != "MOS":
			messagebox.showinfo("Not Allowed", "Photo upload is only allowed for MOS brand products.")
			return
		file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
		if not file_path:
			return
		ext = os.path.splitext(file_path)[1].lower()
		if ext not in [".jpg", ".jpeg", ".png"]:
			messagebox.showerror("Invalid File", "Only .jpg, .jpeg, .png are supported.")
			return
		photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
		safe_th = self.details['th'].replace('/', 'x')
		safe_brand = self.details['brand'].replace('/', 'x').replace(' ', '_')
		filename = f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{safe_th}-{safe_brand}{ext}"
		save_path = os.path.join(photos_dir, filename)
		img = Image.open(file_path).convert("RGB")
		quality = 95
		while True:
			img.save(save_path, format="JPEG", quality=quality)
			if os.path.getsize(save_path) <= 5 * 1024 * 1024 or quality <= 60:
				break
			quality -= 5
		base_old = get_existing_image_base(self.details)
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
			if self.details["brand"].upper() == "MOS":
				self.upload_button.pack_forget()
			else:
				self.upload_button.pack_forget()
		else:
			self.photo_label.configure(image=None, text="📷")
			if self.details["brand"].upper() == "MOS":
				self.upload_button.pack(pady=(5, 0))
			else:
				self.upload_button.pack_forget()

	def show_photo_menu(self, event=None):
		if not os.path.exists(self.image_path):
			if self.details["brand"].upper() == "MOS":
				return
			else:
				self.show_fullscreen_photo()
				return
		if self.details["brand"].upper() != "MOS":
			self.show_fullscreen_photo()
			return
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
		def delete():
			close_menu()
			if messagebox.askyesno("Delete Photo", "Are you sure you want to delete this photo?"):
				os.remove(self.image_path)
				self.load_photo()
		ctk.CTkButton(popup, text="🔍 View", font=("Poppins", 12), fg_color="#4B5563", hover_color="#6B7280", text_color="#FFFFFF", corner_radius=15, height=30, command=view).pack(padx=5, pady=(5, 2))
		if self.details["brand"].upper() == "MOS":
			ctk.CTkButton(popup, text="🗑 Delete", font=("Poppins", 12), fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF", corner_radius=15, height=30, command=delete).pack(padx=5, pady=(2, 5))
		popup.bind("<FocusOut>", lambda e: close_menu())
		popup.focus_set()

	def get_photo_path_by_type(self) -> str:
		photos_dir = os.path.join(os.path.dirname(__file__), "..", "photos")
		if self.details["brand"].upper() == "MOS":
			if 'brand' not in self.details:
				return ""
			safe_th = self.details['th'].replace('/', 'x')
			safe_brand = self.details['brand'].replace('/', 'x').replace(' ', '_')
			for ext in [".jpg", ".jpeg", ".png"]:
				path = os.path.join(photos_dir, f"{self.details['type']}-{self.details['id']}-{self.details['od']}-{safe_th}-{safe_brand}{ext}")
				if os.path.exists(path):
					return path
			return ""
		else:
			for ext in [".jpg", ".png"]:
				path = os.path.join(photos_dir, f"{self.details['type'].lower()}{ext}")
				if os.path.exists(path):
					return path
			placeholder = os.path.join(photos_dir, "placeholder.png")
			return placeholder if os.path.exists(placeholder) else ""

	def show_fullscreen_photo(self):
		if not os.path.exists(self.image_path):
			return
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
		container = ctk.CTkFrame(photo_viewer, fg_color="#000000")
		container.pack(fill="both", expand=True, padx=20, pady=20)
		img = Image.open(self.image_path)
		available_width = window_width - 80
		available_height = window_height - 120
		orig_width, orig_height = img.size
		width_ratio = available_width / orig_width
		height_ratio = available_height / orig_height
		scale_factor = min(width_ratio, height_ratio)
		new_width = int(orig_width * scale_factor)
		new_height = int(orig_height * scale_factor)
		img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
		photo = CTkImage(light_image=img, size=img.size)
		image_frame = ctk.CTkFrame(container, fg_color="#000000")
		image_frame.pack(fill="both", expand=True)
		label = ctk.CTkLabel(image_frame, image=photo, text="", cursor="hand2")
		label.image = photo
		label.pack(expand=True)
		label.bind("<Button-1>", lambda e: photo_viewer.destroy())
		instruction_frame = ctk.CTkFrame(container, fg_color="transparent")
		instruction_frame.pack(fill="x", pady=(10, 0))
		ctk.CTkLabel(instruction_frame, text="Click image or press ESC to close", font=("Poppins", 12), text_color="#CCCCCC").pack()
		close_btn = ctk.CTkButton(instruction_frame, text="Close", font=("Poppins", 12, "bold"), fg_color="#D00000", hover_color="#B71C1C", text_color="#FFFFFF", corner_radius=20, width=100, height=30, command=photo_viewer.destroy)
		close_btn.pack(pady=(10, 0))
		photo_viewer.bind("<Escape>", lambda e: photo_viewer.destroy())
		photo_viewer.focus_set()
