import tkinter as tk
from tkinter import ttk


class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bg_color = "#f0f0f0"
        self.highlight_color = "#ffec7a"  # soft yellow
        self.configure(bg=self.bg_color)

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
            "MECHANICAL SHAFT SEALS": "COMING_SOON",
            "LOCK RINGS (CIRCLIPS)": {
                "INTERNAL": {"MM": None, "INCH": None},
                "EXTERNAL": {"MM": None, "INCH": None},
                "E-RINGS": {}
            },
            "V-RINGS": {"VS": {}, "VA": {}, "VL": {}},
            "PISTON CUPS": {"PISTON CUPS": {}, "DOUBLE ACTION": {}},
            "OIL CAPS": "COMING_SOON",
            "RUBBER DIAPHRAGMS": "COMING_SOON",
            "COUPLING INSERTS": "COMING_SOON",
            "IMPELLERS": "COMING_SOON",
            "BALL BEARINGS": "COMING_SOON",
            "BUSHINGS (FLAT RINGS)": "COMING_SOON",
            "GREASE & SEALANTS": "COMING_SOON",
            "ETC. (SPECIAL)": "COMING_SOON"
        }
        self.categories = categories  # keep reference
        # Store per-category widgets so we can highlight their container "box"
        # { name: {"box": Frame, "btn": ttk.Button} }
        self.category_widgets = {}

        # 🔍 Search bar (top right)
        search_frame = tk.Frame(self, bg=self.bg_color)
        search_frame.pack(anchor="ne", padx=20, pady=10)

        tk.Label(search_frame, text="Search:", bg=self.bg_color).pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side="left")

        # Live update while typing
        self.search_var.trace_add("write", lambda *args: self.search_category())

        # Center content
        self.center_frame = tk.Frame(self, bg=self.bg_color)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.title = tk.Label(self.center_frame, text="MOSCO", font=("Arial", 28, "bold"), bg=self.bg_color)
        self.title.pack(pady=(0, 40))

        self.button_frame = tk.Frame(self.center_frame, bg=self.bg_color)
        self.button_frame.pack()

        # render all categories
        self.render_buttons(categories)

        exit_btn = ttk.Button(self.center_frame, text="Exit", command=self.controller.root.quit)
        exit_btn.pack(pady=(40, 10))

    def render_buttons(self, categories):
        """Render all category buttons (wrapped in a small frame to show highlight as a box)."""
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        self.category_widgets.clear()

        for i, name in enumerate(categories.keys()):
            sub = categories[name]

            # container frame acts as the "highlight box"
            box = tk.Frame(self.button_frame, bg=self.bg_color)
            box.grid(row=i // 2, column=i % 2, padx=20, pady=10, sticky="nsew")

            if sub == "COMING_SOON":
                btn = ttk.Button(
                    box,
                    text=name,
                    width=30,
                    command=lambda n=name: self.controller.show_coming_soon(n)
                )
            else:
                btn = ttk.Button(
                    box,
                    text=name,
                    width=30,
                    command=lambda n=name, s=categories[name]: self.controller.show_subcategory(n, s)
                )

            # add a little inner padding so the box color shows as a border
            btn.pack(padx=3, pady=3)

            self.category_widgets[name] = {"box": box, "btn": btn}

    def _normalize(self, text: str) -> str:
        """Lowercase and strip non-alphanumeric so 'O-RINGS' -> 'orings'."""
        return "".join(ch.lower() for ch in text if ch.isalnum())

    def search_category(self):
        """Highlight categories matching the search query (live search, prefix only, normalized)."""
        raw_query = self.search_var.get()
        query = self._normalize(raw_query)

        # Reset all boxes to default background
        for w in self.category_widgets.values():
            w["box"].configure(bg=self.bg_color)

        if not query:
            return

        # Highlight only if the *normalized name* starts with the normalized query
        for name, w in self.category_widgets.items():
            norm_name = self._normalize(name)
            if norm_name.startswith(query):
                w["box"].configure(bg=self.highlight_color)


class CategoryPage(tk.Frame):
    def __init__(self, parent, controller, category_name, sub_data, return_to="HomePage"):
        super().__init__(parent)
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        self.configure(bg="#f0f0f0")

        # Back button
        back_btn = tk.Button(self, text="← Back", anchor="w", padx=10, pady=5,
                             command=lambda: controller.go_back(self.return_to))
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


class ComingSoonPage(tk.Frame):
    def __init__(self, parent, controller, category_name, return_to="HomePage"):
        super().__init__(parent)
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        self.configure(bg="#f0f0f0")

        back_btn = tk.Button(self, text="← Back", anchor="w", padx=10, pady=5,
                             command=lambda: controller.go_back(self.return_to))
        back_btn.pack(anchor="nw", padx=10, pady=(10, 0))

        center_frame = tk.Frame(self, bg="#f0f0f0")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(center_frame, text=category_name,
                         font=("Arial", 28, "bold"), bg="#f0f0f0")
        title.pack(pady=(0, 20))

        msg = tk.Label(center_frame, text="Coming Soon",
                       font=("Arial", 20), fg="gray", bg="#f0f0f0")
        msg.pack()
