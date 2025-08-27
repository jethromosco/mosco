import customtkinter as ctk
from oilseals.gui.gui_transaction_window import TransactionWindow
from oilseals.gui.gui_mm import InventoryApp
from home_page import HomePage, CategoryPage, ComingSoonPage
from theme_manager import ThemeManager


CATEGORY_FOLDER_MAP = {
    "OIL SEALS": "oilseals",
    "O-RINGS": "orings",
    "O-CORDS": "ocords",
    "O-RING KITS": "oringkits",
    "QUAD RINGS (AIR SEALS)": "quadrings",
    "PACKING SEALS": "packingseals",
    "MECHANICAL SHAFT SEALS": None,  # placeholder
    "LOCK RINGS (CIRCLIPS)": "lockrings",
    "V-RINGS": "vrings",
    "PISTON CUPS": "pistoncups",
    "OIL CAPS": None,
    "RUBBER DIAPHRAGMS": None,
    "COUPLING INSERTS": None,
    "IMPELLERS": None,
    "BALL BEARINGS": None,
    "BUSHINGS (FLAT RINGS)": None,
    "GREASE & SEALANTS": None,
    "ETC. (SPECIAL)": None,
}


class AppController:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#000000")

        # Create container frame using CustomTkinter
        self.container = ctk.CTkFrame(root, fg_color="#000000")
        self.container.pack(fill="both", expand=True)

        self.frames = {}

        # Create and add home page
        home_page = HomePage(self.container, controller=self)
        self.frames["HomePage"] = home_page
        home_page.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_frame("HomePage")

    def apply_theme_to_all(self):
        # Refresh colors for current mode
        for name, frame in list(self.frames.items()):
            try:
                if hasattr(frame, "update_theme"):
                    frame.update_theme()
            except Exception:
                continue
        # Re-show current frame to ensure it repaints
        current = self.get_current_frame_name()
        if current:
            self.show_frame(current)

    def add_category_page(self, name, sub_data, return_to="HomePage"):
        frame = CategoryPage(self.container, self, name, sub_data, return_to=return_to)
        self.frames[name] = frame
        frame.place(x=0, y=0, relwidth=1, relheight=1)

    def show_subcategory(self, name, sub_data):
        current_frame = self.get_current_frame_name()
        return_target = current_frame if current_frame else "HomePage"

        if sub_data == "COMING_SOON":
            self.show_coming_soon(name)
            return

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

                module_path = f"{base_folder}.gui.gui_{sub_module}"
                module = __import__(module_path, fromlist=["InventoryApp"])
                InventoryClass = getattr(module, "InventoryApp")

                frame = InventoryClass(self.container, controller=self)
                frame.return_to = " ".join(parts[:2])  # back to category choice

                self.frames[frame_name] = frame
                frame.place(x=0, y=0, relwidth=1, relheight=1)
            except ModuleNotFoundError:
                # instead of printing, show "Coming Soon"
                self.show_coming_soon(category_name)
                return
        self.show_frame(frame_name)

    def show_frame(self, page_name):
        # Hide all frames
        for frame in self.frames.values():
            frame.place_forget()
        
        # Show the requested frame
        if page_name in self.frames:
            frame = self.frames[page_name]
            frame.place(x=0, y=0, relwidth=1, relheight=1)
            frame.lift()

    def go_back(self, page_name):
        self.show_frame(page_name)

    def get_current_frame_name(self):
        for name, frame in self.frames.items():
            try:
                if frame.winfo_viewable():
                    return name
            except:
                continue
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
        frame.place(x=0, y=0, relwidth=1, relheight=1)
        frame.lift()

    def show_coming_soon(self, category_name):
        frame_name = f"{category_name}ComingSoon"
        if frame_name not in self.frames:
            frame = ComingSoonPage(self.container, self, category_name, return_to="HomePage")
            self.frames[frame_name] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.show_frame(frame_name)