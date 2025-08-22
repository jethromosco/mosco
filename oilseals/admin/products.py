import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
# TransactionTab moved to gui; imported within oilseals.gui.gui_products
from ..database import connect_db
from fractions import Fraction
# ProductFormHandler moved to gui; imported within oilseals.gui.gui_products
from oilseals.gui.gui_products import AdminPanel  # re-export GUI class


# Only the utility functions needed by this file remain here
def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def parse_measurement(value):
    """Convert a string (fraction or decimal) to float for sorting, keep original for display."""
    try:
        if "/" in value:
            return float(Fraction(value))
        return float(value)
    except ValueError:
        raise ValueError(f"Invalid measurement: {value}")