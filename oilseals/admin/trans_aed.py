import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
from ..database import connect_db
from oilseals.gui.gui_trans_aed import TransactionFormHandler  # re-export GUI handler


def center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def format_currency(val):
    return f"\u20B1{val:.2f}"


def parse_date(text):
    return datetime.strptime(text, "%m/%d/%y")