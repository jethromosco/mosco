import tkinter as tk
from tkinter import ttk

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f0f0f0")

        # Categories with nested structure
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

        # Center wrapper
        center_frame = tk.Frame(self, bg="#f0f0f0")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = tk.Label(center_frame, text="MOSCO", font=("Arial", 28, "bold"), bg="#f0f0f0")
        title.pack(pady=(0, 40))

        # Button grid
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

        # Exit button
        exit_btn = ttk.Button(center_frame, text="Exit", command=self.controller.root.quit)
        exit_btn.pack(pady=(40, 10))


class CategoryPage(tk.Frame):
    def __init__(self, parent, controller, category_name, sub_data):
        super().__init__(parent)
        self.controller = controller
        self.category_name = category_name
        self.configure(bg="#f0f0f0")

        # Center wrapper
        center_frame = tk.Frame(self, bg="#f0f0f0")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(center_frame, text=category_name, font=("Arial", 28, "bold"), bg="#f0f0f0")
        title.pack(pady=(0, 40))

        for name, sub in sub_data.items():
            if sub is None:  # Final level — load inventory directly
                btn = ttk.Button(
                    center_frame,
                    text=name,
                    width=30,
                    command=lambda n=f"{self.category_name} {name}": controller.show_inventory_for(n)
                )
            else:  # Another subcategory page
                btn = ttk.Button(
                    center_frame,
                    text=name,
                    width=30,
                    command=lambda n=name, s=sub: controller.show_subcategory(n, s)
                )
            btn.pack(pady=10)

        back_btn = ttk.Button(center_frame, text="Back", width=30, command=controller.go_back)
        back_btn.pack(pady=40)
