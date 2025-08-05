# main.py
import tkinter as tk
from oilseals.main import OilSealPage

class HomePage(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, bg="#f0f0f0")
        self.controller = controller

        button_labels = [
            "OIL SEALS (mm)", "O-RINGS",
            "MECHANICAL SHAFT SEALS", "V-RINGS",
            "MONO/WIPER", "COUPLING",
            "FLAT RINGS", "BEARINGS",
            "ENGINE SUPPORT", "P.U. RAW MATERIALS"
        ]

        tk.Label(self, text="Manila Oil Seal Marketing", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=20)

        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack()

        for i, label in enumerate(button_labels):
            btn = tk.Button(button_frame, text=label, width=30, height=2, font=("Arial", 12))
            btn.grid(row=i % 5, column=i // 5, padx=20, pady=15)
            if label == "OIL SEALS (mm)":
                btn.config(command=lambda: controller.show_frame("OilSealPage"))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manila Oil Seal Marketing")
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", lambda e: self.attributes('-fullscreen', False))

        self.frames = {}

        # Initialize all frames
        for F in (HomePage, OilSealPage):
            page_name = F.__name__
            frame = F(self, self)
            self.frames[page_name] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()
