import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from ..database import connect_db
from fractions import Fraction
from datetime import datetime
import ast
from oilseals.gui.gui_prod_aed import ProductFormHandler  # re-export GUI handler


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