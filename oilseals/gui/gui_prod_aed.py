import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from ..database import connect_db
from fractions import Fraction
import ast


def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def parse_measurement(value):
    try:
        if "/" in value:
            return float(Fraction(value))
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid measurement: {value}")


def safe_str_extract(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return ", ".join(str(v) for v in parsed)
    except Exception:
        pass
    return str(value)


class ProductFormHandler:
    FIELDS = ["TYPE", "ID", "OD", "TH", "BRAND", "PART_NO", "ORIGIN", "NOTES", "PRICE"]

    def __init__(self, parent_window, treeview, on_refresh_callback=None):
        self.parent_window = parent_window
        self.prod_tree = treeview
        self.on_refresh_callback = on_refresh_callback

    def add_product(self):
        self._product_form("Add Product")

    def edit_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to edit", parent=self.parent_window)

        values = self.prod_tree.item(item)["values"]

        try:
            item_str = values[0]
        except IndexError:
            messagebox.showerror("Error", "Invalid selection data.", parent=self.parent_window)
            return

        try:
            type_, size = item_str.split(" ", 1)
            id_str, od_str, th_str = size.split("-")
        except ValueError:
            type_, id_str, od_str, th_str = "", "", "", ""

        brand = values[1] if len(values) > 1 else ""
        part_no = values[2] if len(values) > 2 else ""
        origin = safe_str_extract(values[3]) if len(values) > 3 else ""
        notes = safe_str_extract(values[4]) if len(values) > 4 else ""
        price = values[5] if len(values) > 5 else "0"

        edit_values = (type_, id_str, od_str, th_str, brand, part_no, origin, notes, price.replace("₱", ""))

        self._product_form("Edit Product", edit_values)

    def delete_product(self):
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to delete", parent=self.parent_window)

        values = self.prod_tree.item(item)["values"]
        try:
            item_str = values[0]
            brand = values[1]
        except IndexError:
            messagebox.showerror("Error", "Invalid selection data.", parent=self.parent_window)
            return

        try:
            type_, size = item_str.split(" ", 1)
            id_str, od_str, th_str = size.split("-")
        except ValueError:
            type_, id_str, od_str, th_str = "", "", "", ""

        confirm_window = ctk.CTkToplevel(self.parent_window)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x200")
        confirm_window.resizable(False, False)
        confirm_window.configure(fg_color="#000000")
        
        confirm_window.transient(self.parent_window)
        confirm_window.grab_set()
        
        confirm_window.update_idletasks()
        parent_x = self.parent_window.winfo_rootx()
        parent_y = self.parent_window.winfo_rooty()
        parent_width = self.parent_window.winfo_width()
        parent_height = self.parent_window.winfo_height()
        
        x = parent_x + (parent_width - 400) // 2
        y = parent_y + (parent_height - 200) // 2
        confirm_window.geometry(f"400x200+{x}+{y}")
        
        main_frame = ctk.CTkFrame(confirm_window, fg_color="#2b2b2b", corner_radius=40)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        question_label = ctk.CTkLabel(
            main_frame,
            text=f"Delete {type_} {size} {brand}?",
            font=("Poppins", 16, "bold"),
            text_color="#FFFFFF"
        )
        question_label.pack(pady=(30, 40))
        
        button_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_container.pack(pady=(0, 20))
        
        def confirm_delete():
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM products WHERE type=? AND id=? AND od=? AND th=? AND brand=?",
                (type_, id_str, od_str, th_str, brand)
            )
            conn.commit()
            conn.close()
            if self.on_refresh_callback:
                self.on_refresh_callback()
            confirm_window.destroy()
        
        def cancel_delete():
            confirm_window.destroy()
        
        cancel_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            font=("Poppins", 14, "bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=40,
            command=cancel_delete
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        confirm_btn = ctk.CTkButton(
            button_container,
            text="Delete",
            font=("Poppins", 14, "bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            corner_radius=25,
            width=100,
            height=40,
            command=confirm_delete
        )
        confirm_btn.pack(side="right")
        
        confirm_window.bind('<Escape>', lambda e: cancel_delete())
        confirm_window.bind('<Return>', lambda e: confirm_delete())
        confirm_window.focus()

    def _product_form(self, title, values=None):
        form = ctk.CTkToplevel(self.parent_window)
        form.title(title)
        form.resizable(False, False)
        form.configure(fg_color="#000000")
        form.transient(self.parent_window)
        form.grab_set()
        form.bind("<Escape>", lambda e: form.destroy())

        container = ctk.CTkFrame(form, fg_color="#2b2b2b", corner_radius=40)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        inner_container = ctk.CTkFrame(container, fg_color="transparent")
        inner_container.pack(fill="both", expand=True, padx=30, pady=30)

        title_label = ctk.CTkLabel(
            inner_container,
            text=title,
            font=("Poppins", 20, "bold"),
            text_color="#D00000"
        )
        title_label.pack(pady=(0, 20))

        vars = {field: tk.StringVar(value=(str(values[idx]) if values else "")) for idx, field in enumerate(self.FIELDS)}

        if title.startswith("Edit") and values:
            item_str = f"{values[0]} {values[1]}-{values[2]}-{values[3]}"
            current_item_label = ctk.CTkLabel(
                inner_container,
                text=f"Editing: {item_str}",
                font=("Poppins", 14, "bold"),
                text_color="#CCCCCC"
            )
            current_item_label.pack(pady=(0, 20))

        def force_uppercase(*args):
            vars["TYPE"].set(''.join(filter(str.isalpha, vars["TYPE"].get())).upper())
            vars["BRAND"].set(''.join(filter(str.isalpha, vars["BRAND"].get())).upper())
            origin_txt = vars["ORIGIN"].get()
            vars["ORIGIN"].set(origin_txt.capitalize())

        def validate_numbers(*args):
            for key in ["ID", "OD", "TH"]:
                val = vars[key].get().strip()
                allowed_chars = "0123456789./"
                vars[key].set(''.join(c for c in val if c in allowed_chars))
            price_val = ''.join(c for c in vars["PRICE"].get() if c in '0123456789.')
            vars["PRICE"].set(price_val)

        form_fields_frame = ctk.CTkFrame(inner_container, fg_color="transparent")
        form_fields_frame.pack(fill="x", pady=(0, 25))

        for idx, field in enumerate(self.FIELDS):
            field_frame = ctk.CTkFrame(form_fields_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=8)
            field_frame.grid_columnconfigure(1, weight=1)
            
            label = ctk.CTkLabel(
                field_frame,
                text=f"{field.replace('_', ' ')}:",
                font=("Poppins", 14, "bold"),
                text_color="#FFFFFF",
                width=80,
                anchor="w"
            )
            label.grid(row=0, column=0, sticky="w", padx=(0, 15))
            
            entry = ctk.CTkEntry(
                field_frame,
                textvariable=vars[field],
                font=("Poppins", 13),
                fg_color="#374151",
                text_color="#FFFFFF",
                corner_radius=20,
                height=35,
                border_width=1,
                border_color="#4B5563"
            )
            entry.grid(row=0, column=1, sticky="ew")
            
            def on_entry_enter(event, ent=entry):
                if ent.focus_get() != ent:
                    ent.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
            
            def on_entry_leave(event, ent=entry):
                if ent.focus_get() != ent:
                    ent.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
            
            def on_entry_focus_in(event, ent=entry):
                ent.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
            
            def on_entry_focus_out(event, ent=entry):
                ent.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
            
            entry.bind("<Enter>", on_entry_enter)
            entry.bind("<Leave>", on_entry_leave)
            entry.bind("<FocusIn>", on_entry_focus_in)
            entry.bind("<FocusOut>", on_entry_focus_out)

        vars["TYPE"].trace_add("write", force_uppercase)
        vars["BRAND"].trace_add("write", force_uppercase)
        vars["ORIGIN"].trace_add("write", force_uppercase)
        for key in ["ID", "OD", "TH", "PRICE"]:
            vars[key].trace_add("write", validate_numbers)

        def save(event=None):
            try:
                data = [vars[field].get().strip() for field in self.FIELDS]
                if not all(data[i] for i in range(5)):
                    messagebox.showerror("Missing Fields", "Please fill all required fields (TYPE, ID, OD, TH, BRAND)", parent=form)
                    return
                for field in ["ID", "OD", "TH"]:
                    parse_measurement(data[self.FIELDS.index(field)])
                try:
                    data[self.FIELDS.index("PRICE")] = float(data[self.FIELDS.index("PRICE")])
                except ValueError:
                    messagebox.showerror("Invalid Price", "Please enter a valid price", parent=form)
                    return

                conn = connect_db()
                cur = conn.cursor()

                if title.startswith("Add"):
                    cur.execute("""
                        INSERT INTO products (type, id, od, th, brand, part_no, country_of_origin, notes, price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, data)
                else:
                    cur.execute("""
                        UPDATE products
                        SET type=?, id=?, od=?, th=?, brand=?, part_no=?, country_of_origin=?, notes=?, price=?
                        WHERE type=? AND id=? AND od=? AND th=? AND brand=?
                    """, data + [values[0], values[1], values[2], values[3], values[4]])
                conn.commit()
                conn.close()

                if self.on_refresh_callback:
                    self.on_refresh_callback()
                form.destroy()

            except ValueError as ve:
                messagebox.showerror("Invalid Input", str(ve), parent=form)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred:\n{e}", parent=form)

        button_container = ctk.CTkFrame(inner_container, fg_color="transparent")
        button_container.pack(pady=10)
        
        cancel_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            font=("Poppins", 16, "bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=45,
            command=form.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        save_btn = ctk.CTkButton(
            button_container,
            text="Save",
            font=("Poppins", 16, "bold"),
            fg_color="#22C55E",
            hover_color="#16A34A",
            text_color="#FFFFFF",
            corner_radius=25,
            width=120,
            height=45,
            command=save
        )
        save_btn.pack(side="right")
        
        form.bind("<Return>", save)

        form.update_idletasks()
        form_width = max(500, container.winfo_reqwidth() + 40)
        form_height = max(400, container.winfo_reqheight() + 40)
        center_window(form, form_width, form_height)
        
        form.focus_force()
        form.lift()