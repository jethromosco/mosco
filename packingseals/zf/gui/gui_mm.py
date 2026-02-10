import customtkinter as ctk

class InventoryApp(ctk.CTkFrame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        label = ctk.CTkLabel(self, text="ZF Packing MM - Coming Soon", font=("Arial", 24))
        label.pack(expand=True, fill="both")
