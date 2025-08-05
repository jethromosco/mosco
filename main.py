import tkinter as tk
from tkinter import ttk
import subprocess
import os

class HomePage(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manila Oil Seal Marketing - Homepage")
        self.attributes('-fullscreen', True)
        self.configure(bg="#f0f0f0")

        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self.create_buttons()

    def create_buttons(self):
        button_labels = [
            "OIL SEALS (mm)", "O-RINGS",
            "MECHANICAL SHAFT SEALS", "V-RINGS",
            "MONO/WIPER", "COUPLING",
            "FLAT RINGS", "BEARINGS",
            "ENGINE SUPPORT", "P.U. RAW MATERIALS"
        ]

        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(expand=True)

        for i, label in enumerate(button_labels):
            btn = ttk.Button(button_frame, text=label, width=30)
            btn.grid(row=i % 5, column=i // 5, padx=20, pady=15)

            if label == "OIL SEALS (mm)":
                btn.config(command=self.open_oil_seals)

    def open_oil_seals(self):
        try:
            script_path = os.path.join(os.path.dirname(__file__), "oilseals", "main.py")
            subprocess.Popen(["python", script_path])
            self.destroy()  # optional: closes homepage after launching
        except Exception as e:
            print("Error opening inventory_app.py:", e)

if __name__ == "__main__":
    app = HomePage()
    app.mainloop()
