import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from app_controller import AppController
from theme import theme

if __name__ == "__main__":
    # Initialize theme (default dark) and CTk appearance
    theme.set_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("MOS Inventory")
    
    # Set minimum window size to prevent shrinking too much during dragging
    root.minsize(800, 600)
    
    # Start the app in a maximized (windowed-fullscreen) state by default
    # to improve the first-launch experience.
    def maximize_window():
        try:
            root.state('zoomed')
        except Exception:
            try:
                w = root.winfo_screenwidth()
                h = root.winfo_screenheight()
                root.geometry(f"{w}x{h}")
            except Exception:
                pass
    
    # Schedule maximization after window is created
    root.after(100, maximize_window)

    app = AppController(root)
    root.mainloop()