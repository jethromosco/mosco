import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from ..ui.mm import (
	LOW_STOCK_THRESHOLD,
	OUT_OF_STOCK,
	convert_mm_to_inches_display,
	build_products_display_data,
	parse_number,
	format_display_value,
	stock_filter_matches,
)
from ..ui.transaction_window import TransactionWindow
from .gui_products import AdminPanel


class InventoryApp(ctk.CTkFrame):
	def __init__(self, master, controller=None):
		super().__init__(master, fg_color="#000000")
		self.controller = controller
		self.root = controller.root if controller else self.winfo_toplevel()

		self.root.title("Oil Seal Inventory Manager")
		self.root.attributes("-fullscreen", True)

		self.search_vars = {
			"type": tk.StringVar(),
			"id": tk.StringVar(),
			"od": tk.StringVar(),
			"th": tk.StringVar(),
			"brand": tk.StringVar(),
			"part_no": tk.StringVar()
		}

		self.sort_by = tk.StringVar(value="Size")
		self.stock_filter = tk.StringVar(value="All")

		self.inch_labels = {}
		self.entry_widgets = {}

		self.create_widgets()
		self.refresh_product_list()
		self.root.bind("<Escape>", lambda e: self.clear_filters())
		self.root.bind("<Return>", lambda e: self.remove_focus())

	def on_key_press(self, event, field_type):
		if event.char.isalpha():
			event.widget.insert(tk.INSERT, event.char.upper())
			self.root.after_idle(self.refresh_product_list)
			return "break"
		return None

	def get_var(self, key):
		return self.search_vars[key].get().strip()

	def create_widgets(self):
		self.bind("<Button-1>", self.remove_focus)

		header_frame = ctk.CTkFrame(self, fg_color="#000000", height=120)
		header_frame.pack(fill="x", padx=20, pady=(20, 0))
		header_frame.pack_propagate(False)
		header_frame.grid_columnconfigure(0, weight=1)
		header_frame.grid_columnconfigure(1, weight=0)

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
			command=lambda: self.controller.go_back(self.return_to) if self.controller else self.master.destroy()
		)
		back_btn.grid(row=0, column=0, sticky="w", padx=(40, 10), pady=35)

		search_section = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=40)
		search_section.pack(fill="x", padx=20, pady=(20, 10))

		search_inner = ctk.CTkFrame(search_section, fg_color="transparent")
		search_inner.pack(fill="both", expand=True, padx=20, pady=20)

		main_container = ctk.CTkFrame(search_inner, fg_color="transparent")
		main_container.pack(fill="x", expand=True)

		for i in range(8):
			main_container.grid_columnconfigure(i, weight=1, uniform="fields")

		search_fields = [
			("TYPE", "type"),
			("ID", "id"),
			("OD", "od"),
			("TH", "th"),
			("Brand", "brand"),
			("Part No.", "part_no")
		]

		def on_entry_enter(event, entry):
			if entry.focus_get() != entry:
				entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")

		def on_entry_leave(event, entry):
			if entry.focus_get() != entry:
				entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

		def on_entry_focus_in(event, entry):
			entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")

		def on_entry_focus_out(event, entry):
			entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")

		for idx, (display_name, key) in enumerate(search_fields):
			field_frame = ctk.CTkFrame(main_container, fg_color="transparent", height=90)
			field_frame.grid(row=0, column=idx, padx=5, sticky="ew")
			field_frame.grid_propagate(False)
			field_frame.grid_columnconfigure(0, weight=1)

			label = ctk.CTkLabel(field_frame, text=display_name,
							  font=("Poppins", 14, "bold"),
							  text_color="#FFFFFF")
			label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

			var = self.search_vars[key]
			entry = ctk.CTkEntry(
				field_frame,
				textvariable=var,
				width=120,
				height=32,
				fg_color="#374151",
				text_color="#FFFFFF",
				font=("Poppins", 13),
				corner_radius=40,
				border_width=1,
				border_color="#4B5563",
				placeholder_text=f"Enter {display_name}"
			)
			entry.grid(row=1, column=0, pady=(0, 5), sticky="ew")

			entry.bind("<Enter>", lambda e, ent=entry: on_entry_enter(e, ent))
			entry.bind("<Leave>", lambda e, ent=entry: on_entry_leave(e, ent))
			entry.bind("<FocusIn>", lambda e, ent=entry: on_entry_focus_in(e, ent))
			entry.bind("<FocusOut>", lambda e, ent=entry: on_entry_focus_out(e, ent))
			self.entry_widgets[key] = entry

			if key in ["type", "brand", "part_no"]:
				entry.bind("<KeyPress>", lambda e, field=key: self.on_key_press(e, field))

			var.trace_add("write", lambda *args: self.refresh_product_list())

			if key in ["id", "od", "th"]:
				inch_label = ctk.CTkLabel(
					field_frame,
					text="",
					font=("Poppins", 12, "bold"),
					text_color="#FFFFFF"
				)
				inch_label.grid(row=2, column=0, pady=(2, 0), sticky="ew")
				self.inch_labels[key] = inch_label

				text, is_err = convert_mm_to_inches_display(self.get_var(key))
				inch_label.configure(text=text, text_color="#FF4444" if is_err else "#FFFFFF")
				var.trace_add("write", lambda *args, k=key: self._update_inch_label(k))

		sort_frame = ctk.CTkFrame(main_container, fg_color="transparent", height=90)
		sort_frame.grid(row=0, column=6, padx=5, sticky="ew")
		sort_frame.grid_propagate(False)
		sort_frame.grid_columnconfigure(0, weight=1)

		sort_label = ctk.CTkLabel(sort_frame, text="Sort By",
							 font=("Poppins", 16, "bold"),
							 text_color="#FFFFFF")
		sort_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

		sort_combo = ctk.CTkComboBox(
			sort_frame,
			variable=self.sort_by,
			values=["Size", "Quantity"],
			state="readonly",
			width=120,
			height=32,
			fg_color="#374151",
			button_color="#374151",
			button_hover_color="#D00000",
			dropdown_hover_color="#4B5563",
			text_color="#FFFFFF",
			font=("Poppins", 13),
			corner_radius=40,
			border_width=1,
			border_color="#4B5563"
		)
		sort_combo.grid(row=1, column=0, pady=(0, 5), sticky="ew")
		sort_combo.bind("<Enter>", lambda e: sort_combo.configure(border_color="#D00000", border_width=2, fg_color="#4B5563"))
		sort_combo.bind("<Leave>", lambda e: sort_combo.configure(border_color="#4B5563", border_width=1, fg_color="#374151"))
		self.sort_by.trace_add("write", lambda *args: self.refresh_product_list())

		stock_frame = ctk.CTkFrame(main_container, fg_color="transparent", height=90)
		stock_frame.grid(row=0, column=7, padx=5, sticky="ew")
		stock_frame.grid_propagate(False)
		stock_frame.grid_columnconfigure(0, weight=1)

		stock_label = ctk.CTkLabel(stock_frame, text="Stock Filter",
							   font=("Poppins", 16, "bold"),
							   text_color="#FFFFFF")
		stock_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

		stock_combo = ctk.CTkComboBox(
			stock_frame,
			variable=self.stock_filter,
			values=["All", "In Stock", "Low Stock", "Out of Stock"],
			state="readonly",
			width=120,
			height=32,
			fg_color="#374151",
			button_color="#374151",
			button_hover_color="#D00000",
			dropdown_hover_color="#4B5563",
			text_color="#FFFFFF",
			font=("Poppins", 13),
			corner_radius=40,
			border_width=1,
			border_color="#4B5563"
		)
		stock_combo.grid(row=1, column=0, pady=(0, 5), sticky="ew")
		stock_combo.bind("<Enter>", lambda e: stock_combo.configure(border_color="#D00000", border_width=2, fg_color="#4B5563"))
		stock_combo.bind("<Leave>", lambda e: stock_combo.configure(border_color="#4B5563", border_width=1, fg_color="#374151"))
		self.stock_filter.trace_add("write", lambda *args: self.refresh_product_list())

		table_section = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=40)
		table_section.pack(fill="both", expand=True, padx=20, pady=(0, 0))

		table_inner = ctk.CTkFrame(table_section, fg_color="transparent")
		table_inner.pack(fill="both", expand=True, padx=20, pady=20)

		style = ttk.Style()
		style.theme_use("clam")
		style.configure("Custom.Treeview",
					background="#2b2b2b",
					foreground="#FFFFFF",
					fieldbackground="#2b2b2b",
					font=("Poppins", 13),
					rowheight=35)
		style.configure("Custom.Treeview.Heading",
					background="#000000",
					foreground="#D00000",
					font=("Poppins", 13, "bold"))
		style.map("Custom.Treeview", background=[("selected", "#2b2b2b")])
		style.map("Custom.Treeview.Heading", background=[("active", "#111111")])

		columns = ("type", "size", "brand", "part_no", "origin", "notes", "qty", "price")
		self.tree = ttk.Treeview(table_inner, columns=columns, show="headings", style="Custom.Treeview")
		self.tree.tag_configure("low", background="#8B4513", foreground="#FFFFFF")
		self.tree.tag_configure("out", background="#8B0000", foreground="#FFFFFF")
		self.tree.tag_configure("normal", background="#2b2b2b", foreground="#FFFFFF")

		display_names = {
			"type": "Type",
			"size": "Size",
			"brand": "Brand",
			"part_no": "Part No.",
			"origin": "Origin",
			"notes": "Notes",
			"qty": "Qty",
			"price": "Price"
		}

		for col in columns:
			self.tree.heading(col, text=display_names[col])
			self.tree.column(col, anchor="center", width=120)

		tree_scrollbar = ttk.Scrollbar(table_inner, orient="vertical", command=self.tree.yview)
		self.tree.configure(yscrollcommand=tree_scrollbar.set)
		self.tree.pack(side="left", fill="both", expand=True)
		tree_scrollbar.pack(side="right", fill="y")

		self.tree.bind("<<TreeviewSelect>>", lambda e: self.tree.selection_remove(self.tree.selection()))
		self.tree.bind("<Double-1>", self.open_transaction_page)

		bottom_frame = ctk.CTkFrame(self, fg_color="#000000", height=60)
		bottom_frame.pack(fill="x", padx=20, pady=(10, 20))
		bottom_frame.pack_propagate(False)

		self.status_label = ctk.CTkLabel(bottom_frame, text="",
										 font=("Poppins", 16),
										 text_color="#CCCCCC")
		self.status_label.pack(side="left", pady=15)

		admin_btn = ctk.CTkButton(
			bottom_frame,
			text="Admin",
			font=("Poppins", 20, "bold"),
			fg_color="#D00000",
			hover_color="#B71C1C",
			text_color="#FFFFFF",
			corner_radius=40,
			width=120,
			height=50,
			command=self.open_admin_panel
		)
		admin_btn.pack(side="right", pady=15, padx=40)

	def _update_inch_label(self, key: str):
		text, is_err = convert_mm_to_inches_display(self.get_var(key))
		self.inch_labels[key].configure(text=text, text_color="#FF4444" if is_err else "#FFFFFF")

	def remove_focus(self, event=None):
		self.focus()

	def create_password_window(self, callback=None):
		password_window = ctk.CTkToplevel(self.root)
		password_window.title("Admin Access")
		password_window.geometry("450x350")
		password_window.resizable(False, False)
		password_window.configure(fg_color="#000000")
		password_window.transient(self.root)
		password_window.grab_set()
		password_window.update_idletasks()
		parent_x = self.root.winfo_rootx()
		parent_y = self.root.winfo_rooty()
		parent_width = self.root.winfo_width()
		parent_height = self.root.winfo_height()
		x = parent_x + (parent_width - 450) // 2
		y = parent_y + (parent_height - 350) // 2
		password_window.geometry(f"450x350+{x}+{y}")

		main_frame = ctk.CTkFrame(password_window, fg_color="#000000", corner_radius=0)
		main_frame.pack(fill="both", expand=True)
		content_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b", corner_radius=40, border_width=1, border_color="#4B5563")
		content_frame.pack(fill="both", expand=True, padx=30, pady=30)

		title_label = ctk.CTkLabel(content_frame, text="Admin Access", font=("Poppins", 28, "bold"), text_color="#D00000")
		title_label.pack(pady=(40, 20))
		subtitle_label = ctk.CTkLabel(content_frame, text="Enter admin password to continue", font=("Poppins", 16), text_color="#FFFFFF")
		subtitle_label.pack(pady=(0, 40))

		entry_container = ctk.CTkFrame(content_frame, fg_color="transparent")
		entry_container.pack(pady=(0, 30))
		password_label = ctk.CTkLabel(entry_container, text="Password", font=("Poppins", 16, "bold"), text_color="#FFFFFF")
		password_label.pack(pady=(0, 10))
		password_entry = ctk.CTkEntry(entry_container, width=280, height=40, fg_color="#374151", text_color="#FFFFFF", font=("Poppins", 14), corner_radius=40, border_width=2, border_color="#4B5563", placeholder_text="Enter password", show="*")
		password_entry.pack(pady=(0, 10))

		def on_entry_enter(event):
			if password_entry.focus_get() != password_entry:
				password_entry.configure(border_color="#D00000", fg_color="#4B5563")
		def on_entry_leave(event):
			if password_entry.focus_get() != password_entry:
				password_entry.configure(border_color="#4B5563", fg_color="#374151")
		def on_entry_focus_in(event):
			password_entry.configure(border_color="#D00000", fg_color="#1F2937")
		def on_entry_focus_out(event):
			password_entry.configure(border_color="#4B5563", fg_color="#374151")
		password_entry.bind("<Enter>", on_entry_enter)
		password_entry.bind("<Leave>", on_entry_leave)
		password_entry.bind("<FocusIn>", on_entry_focus_in)
		password_entry.bind("<FocusOut>", on_entry_focus_out)

		error_label = ctk.CTkLabel(entry_container, text="", font=("Poppins", 12), text_color="#FF4444")
		error_label.pack()

		button_container = ctk.CTkFrame(content_frame, fg_color="transparent")
		button_container.pack(pady=(20, 30))
		cancel_btn = ctk.CTkButton(button_container, text="Cancel", font=("Poppins", 16, "bold"), fg_color="#6B7280", hover_color="#4B5563", text_color="#FFFFFF", corner_radius=40, width=120, height=45, command=lambda: self.close_password_window(password_window, callback, False))
		cancel_btn.pack(side="left", padx=(0, 20))
		submit_btn = ctk.CTkButton(button_container, text="Submit", font=("Poppins", 16, "bold"), fg_color="#D00000", hover_color="#B71C1C", text_color="#FFFFFF", corner_radius=40, width=120, height=45, command=lambda: self.check_password(password_entry, error_label, password_window, callback))
		submit_btn.pack(side="right", padx=(20, 0))
		password_window.bind('<Return>', lambda e: self.check_password(password_entry, error_label, password_window, callback))
		password_window.bind('<Escape>', lambda e: self.close_password_window(password_window, callback, False))
		password_entry.focus()
		return password_window

	def check_password(self, entry, error_label, window, callback):
		password = entry.get().strip()
		if password == "1":
			self.close_password_window(window, callback, True)
		else:
			error_label.configure(text="❌ Incorrect password. Please try again.")
			entry.delete(0, tk.END)
			entry.focus()
			window.after(3000, lambda: error_label.configure(text=""))

	def close_password_window(self, window, callback, success):
		window.destroy()
		if callback:
			callback(success)

	def open_admin_panel(self, return_to=None):
		def on_password_result(success):
			if success:
				current_frame_name = self.controller.get_current_frame_name()
				current_frame = self.controller.frames[current_frame_name]
				AdminPanel(self.controller.root, current_frame, self.controller, on_close_callback=self.refresh_product_list)
		self.create_password_window(callback=on_password_result)

	def clear_filters(self):
		for var in self.search_vars.values():
			var.set("")
		self.sort_by.set("Size")
		self.stock_filter.set("All")
		self.refresh_product_list()

	def refresh_product_list(self, clear_filters=False):
		if clear_filters:
			for var in self.search_vars.values():
				var.set("")
			self.sort_by.set("Size")
			self.stock_filter.set("All")

		self.tree.delete(*self.tree.get_children())

		filters = {k: v.get().strip() for k, v in self.search_vars.items()}
		display_data = build_products_display_data(filters, self.sort_by.get(), self.stock_filter.get())

		for item in display_data:
			qty = item[6]
			if qty == OUT_OF_STOCK:
				tag = "out"
			elif qty <= LOW_STOCK_THRESHOLD:
				tag = "low"
			else:
				tag = "normal"
			self.tree.insert("", tk.END, values=item[:8], tags=(tag,))

		self.status_label.configure(text=f"Total products: {len(display_data)}")

	def open_transaction_page(self, event):
		item_id = self.tree.identify_row(event.y)
		if not item_id:
			return
		self.tree.selection_set(item_id)
		item = self.tree.item(item_id)["values"]
		if not item:
			return
		try:
			size_str = item[1].replace("×", "-").replace("x", "-")
			parts = size_str.split("-")
			id_, od, th = [p.strip() for p in parts]
		except Exception:
			return
		details = {
			"type": item[0],
			"id": id_,
			"od": od,
			"th": th,
			"brand": item[2],
			"part_no": item[3],
			"country_of_origin": item[4],
			"notes": item[5],
			"quantity": item[6],
			"price": float(item[7].replace("₱", ""))
		}
		if self.controller:
			self.controller.show_transaction_window(details, self)
		else:
			win = tk.Toplevel(self)
			TransactionWindow(win, details, self)