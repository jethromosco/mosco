import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from ..admin.prod_aed import ProductFormLogic


def center_window(win, width, height):
    """Center a window on the screen."""
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


class ProductFormHandler:
    """Handles product form GUI interactions and delegates logic to ProductFormLogic."""
    
    def __init__(self, parent_window, treeview, on_refresh_callback=None):
        self.parent_window = parent_window
        self.prod_tree = treeview
        self.on_refresh_callback = on_refresh_callback
        
        # Initialize logic handler
        self.logic = ProductFormLogic()

    def add_product(self):
        """Show add product form."""
        self._product_form("Add Product")

    def edit_product(self):
        """Show edit product form with current values."""
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to edit", parent=self.parent_window)

        values = self.prod_tree.item(item)["values"]
        
        if not values:
            messagebox.showerror("Error", "Invalid selection data.", parent=self.parent_window)
            return

        # Use logic to extract values
        edit_values = self.logic.extract_values_from_tree_selection(values)
        self._product_form("Edit Product", edit_values)

    def delete_product(self):
        """Show delete confirmation dialog."""
        item = self.prod_tree.focus()
        if not item:
            return messagebox.showwarning("Select", "Select a product to delete", parent=self.parent_window)

        values = self.prod_tree.item(item)["values"]
        if not values:
            messagebox.showerror("Error", "Invalid selection data.", parent=self.parent_window)
            return

        # Extract values for deletion
        extracted_values = self.logic.extract_values_from_tree_selection(values)
        type_, id_str, od_str, th_str, brand = extracted_values[:5]
        
        item_str = values[0]
        self._show_delete_confirmation(type_, id_str, od_str, th_str, brand, item_str)

    def _show_delete_confirmation(self, type_, id_str, od_str, th_str, brand, item_str):
        """Show delete confirmation dialog."""
        confirm_window = ctk.CTkToplevel(self.parent_window)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x200")
        confirm_window.resizable(False, False)
        confirm_window.configure(fg_color="#000000")
        
        confirm_window.transient(self.parent_window)
        confirm_window.grab_set()
        
        # Center the dialog
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
            text=f"Delete {item_str} {brand}?",
            font=("Poppins", 16, "bold"),
            text_color="#FFFFFF"
        )
        question_label.pack(pady=(30, 40))
        
        button_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_container.pack(pady=(0, 20))
        
        def confirm_delete():
            # Use logic to delete product
            success, message = self.logic.delete_product(type_, id_str, od_str, th_str, brand)
            if success:
                if self.on_refresh_callback:
                    self.on_refresh_callback()
                confirm_window.destroy()
            else:
                messagebox.showerror("Delete Error", message, parent=confirm_window)
        
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
        """Create and show the product form dialog."""
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

        # Create form variables
        vars = {field: tk.StringVar(value=(str(values[idx]) if values else "")) for idx, field in enumerate(self.logic.FIELDS)}

        # Show current item being edited
        if title.startswith("Edit") and values:
            item_str = f"{values[0]} {values[1]}-{values[2]}-{values[3]}"
            current_item_label = ctk.CTkLabel(
                inner_container,
                text=f"Editing: {item_str}",
                font=("Poppins", 14, "bold"),
                text_color="#CCCCCC"
            )
            current_item_label.pack(pady=(0, 20))

        # Text field formatting callbacks
        def force_uppercase(*args):
            current_data = [vars[field].get() for field in self.logic.FIELDS]
            formatted_data = self.logic.format_text_fields(current_data)
            
            vars["TYPE"].set(formatted_data[0])
            vars["BRAND"].set(formatted_data[4])
            vars["ORIGIN"].set(formatted_data[6])

        def validate_numbers(*args):
            current_data = [vars[field].get() for field in self.logic.FIELDS]
            formatted_data = self.logic.format_number_fields(current_data)
            
            for idx, field in enumerate(self.logic.FIELDS):
                if field in ["ID", "OD", "TH", "PRICE"]:
                    vars[field].set(formatted_data[idx])

        # Create form fields
        form_fields_frame = ctk.CTkFrame(inner_container, fg_color="transparent")
        form_fields_frame.pack(fill="x", pady=(0, 25))

        entries = {}
        for idx, field in enumerate(self.logic.FIELDS):
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
            entries[field] = entry
            
            # Add hover and focus effects
            self._add_entry_effects(entry)

        # Bind validation callbacks
        vars["TYPE"].trace_add("write", force_uppercase)
        vars["BRAND"].trace_add("write", force_uppercase)
        vars["ORIGIN"].trace_add("write", force_uppercase)
        for key in ["ID", "OD", "TH", "PRICE"]:
            vars[key].trace_add("write", validate_numbers)

        # Save function
        def save(event=None):
            data = [vars[field].get().strip() for field in self.logic.FIELDS]
            
            if title.startswith("Add"):
                success, message = self.logic.add_product(data)
            else:
                success, message = self.logic.update_product(data, values)
            
            if success:
                if self.on_refresh_callback:
                    self.on_refresh_callback()
                form.destroy()
            else:
                messagebox.showerror("Error", message, parent=form)

        # Create buttons
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

        # Size and center the form
        form.update_idletasks()
        form_width = max(500, container.winfo_reqwidth() + 40)
        form_height = max(400, container.winfo_reqheight() + 40)
        center_window(form, form_width, form_height)
        
        form.focus_force()
        form.lift()

    def _add_entry_effects(self, entry):
        """Add hover and focus effects to entry widgets."""
        def on_entry_enter(event):
            if entry.focus_get() != entry:
                entry.configure(border_color="#D00000", border_width=2, fg_color="#4B5563")
        
        def on_entry_leave(event):
            if entry.focus_get() != entry:
                entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        def on_entry_focus_in(event):
            entry.configure(border_color="#D00000", border_width=2, fg_color="#1F2937")
        
        def on_entry_focus_out(event):
            entry.configure(border_color="#4B5563", border_width=1, fg_color="#374151")
        
        entry.bind("<Enter>", on_entry_enter)
        entry.bind("<Leave>", on_entry_leave)
        entry.bind("<FocusIn>", on_entry_focus_in)
        entry.bind("<FocusOut>", on_entry_focus_out)