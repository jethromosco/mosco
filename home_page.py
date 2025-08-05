import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f0f0f0")

        # Center wrapper for everything
        center_frame = tk.Frame(self, bg="#f0f0f0")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = tk.Label(center_frame, text="MOSCO", font=("Arial", 28, "bold"), bg="#f0f0f0")
        title.pack(pady=(0, 40))

        # Button grid
        button_frame = tk.Frame(center_frame, bg="#f0f0f0")
        button_frame.pack()

        button_labels = [
            "OIL SEALS (mm)", "O-RINGS",
            "MECHANICAL SHAFT SEALS", "V-RINGS",
            "MONO/WIPER", "COUPLING",
            "FLAT RINGS", "BEARINGS",
            "ENGINE SUPPORT", "P.U. RAW MATERIALS"
        ]

        for i, label in enumerate(button_labels):
            btn = ttk.Button(button_frame, text=label, width=30)
            btn.grid(row=i // 2, column=i % 2, padx=20, pady=10)

            if label == "OIL SEALS (mm)":
                btn.config(command=lambda: self.controller.show_inventory_app())

        # Admin Button
        manage_btn = ttk.Button(center_frame, text="Admin", command=self.open_admin_panel)
        manage_btn.pack(pady=(10, 0))

        # Exit button
        exit_btn = ttk.Button(center_frame, text="Exit", command=self.controller.root.quit)
        exit_btn.pack(pady=(40, 10))

    def open_admin_panel(self):
        password = simpledialog.askstring("Admin Access", "Enter password:", show="*")
        if password == "569656":  # Change this password as needed
            from admin.admin_panel import AdminPanel
            AdminPanel(self.controller.root, self.controller.frames["InventoryApp"])
        else:
            messagebox.showerror("Access Denied", "Incorrect password.")
