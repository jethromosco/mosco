import tkinter as tk
from tkinter import ttk

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f0f0f0")

        categories = {
            "OIL SEALS": {"MM": None, "INCH": None},
            "O-RINGS": {
                "NITRILE (NBR)": {"MM": None, "INCH": None},
                "SILICONE": {"MM": None, "INCH": None},
                "VITON (FKM)": {"MM": None, "INCH": None}
            },
            "O-CORDS": {
                "NITRILE (NBR)": {},
                "SILICONE": {},
                "VITON (FKM)": {},
                "POLYCORD": {}
            },
            "O-RING KITS": {},
            "QUAD RINGS (AIR SEALS)": {"MM": None, "INCH": None},
            "PACKING SEALS": {
                "MONOSEALS": {"MM": None, "INCH": None},
                "WIPER SEALS": {"MM": None, "INCH": None},
                "WIPERMONO": {},
                "VEE PACKING": {"MM": None, "INCH": None},
                "ZF PACKING": {}
            },
            "LOCK RINGS (CIRCLIPS)": {
                "INTERNAL": {"MM": None, "INCH": None},
                "EXTERNAL": {"MM": None, "INCH": None},
                "E-RINGS": {}
            },
            "V-RINGS": {"VS": {}, "VA": {}, "VL": {}},
            "PISTON CUPS": {"PISTON CUPS": {}, "DOUBLE ACTION": {}},
            "OIL CAPS": {},
            "RUBBER DIAPHRAGMS": {},
            "COUPLING INSERTS": {},
            "IMPELLERS": {},
            "BALL BEARINGS": {},
            "BUSHINGS (FLAT RINGS)": {},
            "GREASE & SEALANTS": {},
            "ETC. (SPECIAL)": {}
        }

        center_frame = tk.Frame(self, bg="#f0f0f0")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(center_frame, text="MOSCO", font=("Arial", 28, "bold"), bg="#f0f0f0")
        title.pack(pady=(0, 40))

        button_frame = tk.Frame(center_frame, bg="#f0f0f0")
        button_frame.pack()

        for i, name in enumerate(categories.keys()):
            btn = ttk.Button(
                button_frame,
                text=name,
                width=30,
                command=lambda n=name, s=categories[name]: controller.show_subcategory(n, s)
            )
            btn.grid(row=i // 2, column=i % 2, padx=20, pady=10)

        exit_btn = ttk.Button(center_frame, text="Exit", command=self.controller.root.quit)
        exit_btn.pack(pady=(40, 10))


class CategoryPage(tk.Frame):
    def __init__(self, parent, controller, category_name, sub_data, return_to="HomePage"):
        super().__init__(parent)
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        self.configure(bg="#f0f0f0")

        # 🔹 Back button at top-left (like in InventoryApp)
        back_btn = tk.Button(self, text="← Back", anchor="w", padx=10, pady=5)
        back_btn.config(command=lambda: controller.go_back(self.return_to))
        back_btn.pack(anchor="nw", padx=10, pady=(10, 0))

        center_frame = tk.Frame(self, bg="#f0f0f0")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(center_frame, text=category_name, font=("Arial", 28, "bold"), bg="#f0f0f0")
        title.pack(pady=(0, 40))

        # Subcategory buttons
        for name, sub in sub_data.items():
            if sub is None:
                btn = ttk.Button(
                    center_frame,
                    text=name,
                    width=30,
                    command=lambda n=f"{self.category_name} {name}": controller.show_inventory_for(n)
                )
            else:
                btn = ttk.Button(
                    center_frame,
                    text=name,
                    width=30,
                    command=lambda n=name, s=sub: controller.show_subcategory(n, s)
                )
            btn.pack(pady=10)
