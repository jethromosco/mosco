import tkinter as tk
from oilseals.ui.transaction_window import TransactionWindow
from oilseals.ui.mm import InventoryApp
from home_page import HomePage, CategoryPage

CATEGORY_FOLDER_MAP = {
    "OIL SEALS": "oilseals",
    "O-RINGS": "orings",
    "O-CORDS": "ocords",
    "O-RING KITS": "oringkits",
    "QUAD RINGS (AIR SEALS)": "quadrings",
    "PACKING SEALS": "packingseals",
    "LOCK RINGS (CIRCLIPS)": "lockrings",
    "V-RINGS": "vrings",
    "PISTON CUPS": "pistoncups",
    "OIL CAPS": "oilcaps",
    "RUBBER DIAPHRAGMS": "rubberdiaphragms",
    "COUPLING INSERTS": "couplinginserts",
    "IMPELLERS": "impellers",
    "BALL BEARINGS": "ballbearings",
    "BUSHINGS (FLAT RINGS)": "bushings",
    "GREASE & SEALANTS": "grease_sealants",
    "ETC. (SPECIAL)": "etc_special",
}

class AppController:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)

        self.container = tk.Frame(root)
        self.container.grid(row=0, column=0, sticky="nsew")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        home_page = HomePage(self.container, controller=self)
        self.frames["HomePage"] = home_page
        home_page.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def add_category_page(self, name, sub_data, return_to="HomePage"):
        frame = CategoryPage(self.container, self, name, sub_data, return_to=return_to)
        self.frames[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def show_subcategory(self, name, sub_data):
        # Figure out where the Back button should go
        current_frame = self.get_current_frame_name()
        return_target = current_frame if current_frame else "HomePage"

        if not sub_data:
            self.show_inventory_for(name)
            return

        if name not in self.frames:
            self.add_category_page(name, sub_data, return_to=return_target)

        self.show_frame(name)

    def show_inventory_for(self, category_name):
        frame_name = f"{category_name}InventoryApp"
        if frame_name not in self.frames:
            try:
                parts = category_name.split()
                base_folder = parts[0].lower() + parts[1].lower()
                sub_module = parts[-1].lower()

                module_path = f"{base_folder}.ui.{sub_module}"
                module = __import__(module_path, fromlist=["InventoryApp"])
                InventoryClass = getattr(module, "InventoryApp")

                frame = InventoryClass(self.container, controller=self)
                frame.return_to = " ".join(parts[:2])  # back to category choice

                self.frames[frame_name] = frame
                frame.grid(row=0, column=0, sticky="nsew")
            except ModuleNotFoundError:
                print(f"⚠ Inventory app for '{category_name}' not yet implemented.")
                return
        self.show_frame(frame_name)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def go_back(self, page_name):
        self.show_frame(page_name)

    def get_current_frame_name(self):
        for name, frame in self.frames.items():
            if frame.winfo_ismapped():
                return name
        return None

    def show_home(self):
        self.show_frame("HomePage")

    def show_transaction_window(self, details, main_app, return_to=None):
        if "TransactionWindow" in self.frames:
            self.frames["TransactionWindow"].destroy()
        if not return_to:
            return_to = self.get_current_frame_name()

        frame = TransactionWindow(self.container, details, controller=self, return_to=return_to)
        frame.set_details(details, main_app)
        self.frames["TransactionWindow"] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        frame.tkraise()
