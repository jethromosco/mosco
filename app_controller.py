import tkinter as tk
from oilseals.ui.transaction_window import TransactionWindow
from oilseals.ui.inventory_app import InventoryApp
from home_page import HomePage

class AppController:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)

        # Main container using grid for proper layout
        self.container = tk.Frame(root)
        self.container.grid(row=0, column=0, sticky="nsew")

        # Allow container to expand properly
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.history = []  # ← Tracks navigation history

        # Preload HomePage and InventoryApp
        for F in (HomePage, InventoryApp):
            page_name = F.__name__
            frame = F(self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        current = self.get_current_frame_name()
        if current and current != page_name:
            self.history.append(current)  # Save current to history
        frame = self.frames[page_name]
        frame.tkraise()

    def go_back(self):
        if self.history:
            previous = self.history.pop()
            self.show_frame(previous)

    def get_current_frame_name(self):
        for name, frame in self.frames.items():
            if frame.winfo_ismapped():
                return name
        return None

    def show_home(self):
        self.show_frame("HomePage")

    def show_inventory_app(self):
        self.show_frame("InventoryApp")

    def show_transaction_window(self, details, main_app):
        # Remove old TransactionWindow if it exists
        if "TransactionWindow" in self.frames:
            self.frames["TransactionWindow"].destroy()

        frame = TransactionWindow(self.container, details, controller=self)
        frame.set_details(details, main_app)
        self.frames["TransactionWindow"] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("TransactionWindow")
