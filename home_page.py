import customtkinter as ctk
from PIL import Image
import tkinter as tk

# === File Paths ===
ICON_PATH = r"C:\Users\MOS-PC2\Desktop\figma icons"

# Category structure
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

# Icon mapping
icon_mapping = {
    "OIL SEALS": f"{ICON_PATH}\\oilseals.png",
    "O-RINGS": f"{ICON_PATH}\\orings.png",
    "O-CORDS": f"{ICON_PATH}\\o-ring cords.png",
    "O-RING KITS": f"{ICON_PATH}\\o-ring kits.png",
    "QUAD RINGS (AIR SEALS)": f"{ICON_PATH}\\quad rings.png",
    "PACKING SEALS": f"{ICON_PATH}\\packing seals.png",
    "MECHANICAL SHAFT SEALS": f"{ICON_PATH}\\mechanical shaft seals.png",
    "LOCK RINGS (CIRCLIPS)": f"{ICON_PATH}\\lock rings.png",
    "V-RINGS": f"{ICON_PATH}\\v-rings.png",
    "PISTON CUPS": f"{ICON_PATH}\\piston cups.png",
    "OIL CAPS": f"{ICON_PATH}\\oil caps.png",
    "RUBBER DIAPHRAGMS": f"{ICON_PATH}\\rubber diaphragms.png",
    "COUPLING INSERTS": f"{ICON_PATH}\\coupling inserts.png",
    "IMPELLERS": f"{ICON_PATH}\\impellers.png",
    "BALL BEARINGS": f"{ICON_PATH}\\ball bearings.png",
    "BUSHINGS (FLAT RINGS)": f"{ICON_PATH}\\bushings.png",
    "GREASE & SEALANTS": f"{ICON_PATH}\\grease and sealants.png",
    "ETC. (SPECIAL)": f"{ICON_PATH}\\special.png"
}


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#000000")
        self.controller = controller
        self.categories = categories
        self.category_buttons = {}
        
        # === Scrollable main container with faster scroll speed ===
        main_scroll = ctk.CTkScrollableFrame(self, fg_color="#000000", scrollbar_fg_color="#111827",
                                           scrollbar_button_color="#D00000", scrollbar_button_hover_color="#FF0000")
        main_scroll.pack(fill="both", expand=True)
        
        # Configure faster scroll speed (20x faster)
        def _on_mousewheel(event):
            # Original scroll speed multiplied by 20
            main_scroll._parent_canvas.yview_scroll(int(-50*(event.delta/120)), "units")
        
        main_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Make the entire frame clickable to remove focus from search
        main_scroll.bind("<Button-1>", self.remove_search_focus)
        
        # === Search box (top-right) - NOW RED ===
        self.search_entry = ctk.CTkEntry(
            main_scroll,
            placeholder_text="🔍 Search",
            fg_color="#D00000",  # Red background
            corner_radius=40,
            text_color="#FFFFFF",  # White text
            placeholder_text_color="#FFFFFF",  # White placeholder
            font=("Poppins", 24, "bold"),
            width=176,
            height=56,
            border_width=0
        )
        self.search_entry.pack(anchor="ne", padx=40, pady=(40, 0))
        
        # Search functionality
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        # Enhanced hover effect for search bar - darker red on hover
        def on_search_enter(e):
            self.search_entry.configure(fg_color="#B71C1C")  # Darker red on hover
        def on_search_leave(e):
            self.search_entry.configure(fg_color="#D00000")  # Back to original red

        self.search_entry.bind("<Enter>", on_search_enter)
        self.search_entry.bind("<Leave>", on_search_leave)

        # === Logo row ===
        logo_frame = ctk.CTkFrame(main_scroll, fg_color="#000000")
        logo_frame.pack(pady=20)
        logo_frame.bind("<Button-1>", self.remove_search_focus)

        try:
            logo_img1 = ctk.CTkImage(Image.open(f"{ICON_PATH}\\mosco logo.png"), size=(240, 240))
            logo_img2 = ctk.CTkImage(Image.open(f"{ICON_PATH}\\mosco text.png"), size=(847, 240))

            lbl1 = ctk.CTkLabel(logo_frame, image=logo_img1, text="", bg_color="#000000")
            lbl2 = ctk.CTkLabel(logo_frame, image=logo_img2, text="", bg_color="#000000")

            lbl1.pack(side="left", padx=(0, 10))
            lbl2.pack(side="left")
            
            lbl1.bind("<Button-1>", self.remove_search_focus)
            lbl2.bind("<Button-1>", self.remove_search_focus)
        except Exception as e:
            print(f"Error loading logos: {e}")
            # Fallback text logo with Hero font
            title_label = ctk.CTkLabel(logo_frame, text="MOSCO", 
                                     font=("Hero", 48, "bold"),
                                     text_color="#FFFFFF")
            title_label.pack()
            title_label.bind("<Button-1>", self.remove_search_focus)

        # === Grid of category buttons ===
        self.grid_frame = ctk.CTkFrame(main_scroll, fg_color="#000000")
        self.grid_frame.pack(pady=20)
        self.grid_frame.bind("<Button-1>", self.remove_search_focus)

        self.create_category_buttons()
    
    def remove_search_focus(self, event=None):
        """Remove focus from search entry when clicking elsewhere"""
        self.focus()
    
    def create_category_buttons(self):
        """Create category buttons with 150x150 images"""
        cols = 3
        for idx, (label, sub_data) in enumerate(self.categories.items()):
            try:
                # Try to load icon with larger size (150x150), fallback to default if not found
                img_path = icon_mapping.get(label, f"{ICON_PATH}\\special.png")
                try:
                    img = Image.open(img_path).resize((150, 150))
                    tk_img = ctk.CTkImage(light_image=img, size=(150, 150))
                except:
                    # Create a simple colored rectangle as fallback
                    img = Image.new('RGB', (150, 150), color='#444444')
                    tk_img = ctk.CTkImage(light_image=img, size=(150, 150))

                btn = ctk.CTkButton(
                    self.grid_frame,
                    text=label,
                    image=tk_img,
                    compound="top",
                    font=("Poppins", 24, "bold"),
                    fg_color="#0b0d1a",
                    hover_color="#050510",
                    text_color="#FFFFFF",
                    corner_radius=40,
                    width=504,
                    height=268,  # Slightly increased height to accommodate larger image
                    border_width=0,
                    command=lambda l=label, s=sub_data: self.controller.show_subcategory(l, s)
                )
                btn.image = tk_img  # keep reference

                row, col = divmod(idx, cols)
                btn.grid(row=row, column=col, padx=20, pady=20)

                # Store button reference and grid info for search functionality
                self.category_buttons[label] = {
                    'button': btn,
                    'original_row': row,
                    'original_col': col
                }

                # Hover glow effect (only red highlight on hover)
                def on_enter(e, b=btn):
                    b.configure(border_width=3, border_color="#D00000", text_color="lightgrey")
                def on_leave(e, b=btn):
                    b.configure(border_width=0, text_color="#FFFFFF")

                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
                btn.bind("<Button-1>", self.remove_search_focus)

            except Exception as e:
                print(f"Error creating button for {label}: {e}")
    
    def _normalize(self, text: str) -> str:
        """Lowercase and strip non-alphanumeric"""
        return "".join(ch.lower() for ch in text if ch.isalnum())
    
    def on_search_change(self, event=None):
        """Handle search input changes"""
        query = self._normalize(self.search_entry.get())
        
        if not query:
            # Show all categories in original positions if search is empty
            for name, btn_info in self.category_buttons.items():
                btn = btn_info['button']
                row = btn_info['original_row']
                col = btn_info['original_col']
                btn.grid(row=row, column=col, padx=20, pady=20)
            return
        
        # First, hide all categories
        for btn_info in self.category_buttons.values():
            btn_info['button'].grid_remove()
        
        # Find matching categories
        matching_categories = []
        for name, btn_info in self.category_buttons.items():
            norm_name = self._normalize(name)
            if norm_name.startswith(query):
                matching_categories.append((name, btn_info))
        
        # Rearrange matching categories at the top in 3-column grid
        cols = 3
        for idx, (name, btn_info) in enumerate(matching_categories):
            btn = btn_info['button']
            row, col = divmod(idx, cols)
            btn.grid(row=row, column=col, padx=20, pady=20)


class CategoryPage(ctk.CTkFrame):
    def __init__(self, parent, controller, category_name, sub_data, return_to="HomePage"):
        super().__init__(parent, fg_color="#000000")
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        
        # === Scrollable main container with red scrollbar (hidden) ===
        main_scroll = ctk.CTkScrollableFrame(self, fg_color="#000000", scrollbar_fg_color="#000000",
                                           scrollbar_button_color="#000000", scrollbar_button_hover_color="#000000")
        main_scroll.pack(fill="both", expand=True)
        
        # Configure faster scroll speed (20x faster)
        def _on_mousewheel(event):
            main_scroll._parent_canvas.yview_scroll(int(-20*(event.delta/120)), "units")
        
        main_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # === Back button (top-left) - NOW RED ===
        back_btn = ctk.CTkButton(
            main_scroll,
            text="← Back",
            font=("Poppins", 20, "bold"),
            fg_color="#D00000",  # Red background
            hover_color="#B71C1C",  # Darker red on hover
            text_color="#FFFFFF",  # White text
            corner_radius=40,
            width=120,
            height=50,
            command=lambda: controller.go_back(self.return_to)
        )
        back_btn.pack(anchor="nw", padx=40, pady=(40, 0))
        
        # === Title with Hero font ===
        title_label = ctk.CTkLabel(main_scroll, text=self.category_name,
                                 font=("Hero", 36, "bold"),
                                 text_color="#FFFFFF")
        title_label.pack(pady=40)
        
        # === Grid of subcategory buttons ===
        grid_frame = ctk.CTkFrame(main_scroll, fg_color="#000000")
        grid_frame.pack(pady=20)
        
        self.create_subcategory_buttons(grid_frame, sub_data)
    
    def create_subcategory_buttons(self, grid_frame, sub_data):
        """Create subcategory buttons with 150x150 images"""
        cols = 3
        idx = 0
        
        for name, sub in sub_data.items():
            try:
                # Create a simple icon for subcategories with larger size
                img = Image.new('RGB', (150, 150), color='#333333')
                tk_img = ctk.CTkImage(light_image=img, size=(150, 150))
                
                if sub is None:
                    # End point - show inventory
                    command = lambda n=f"{self.category_name} {name}": self.controller.show_inventory_for(n)
                else:
                    # Has more subcategories
                    command = lambda n=name, s=sub: self.controller.show_subcategory(n, s)

                btn = ctk.CTkButton(
                    grid_frame,
                    text=name,
                    image=tk_img,
                    compound="top",
                    font=("Poppins", 20, "bold"),
                    fg_color="#0b0d1a",
                    hover_color="#050510",
                    text_color="#FFFFFF",
                    corner_radius=40,
                    width=404,
                    height=220,  # Slightly increased for larger image
                    border_width=0,
                    command=command
                )
                btn.image = tk_img

                row, col = divmod(idx, cols)
                btn.grid(row=row, column=col, padx=15, pady=15)

                # Hover effect
                def on_enter(e, b=btn):
                    b.configure(border_width=3, border_color="#D00000", text_color="lightgrey")
                def on_leave(e, b=btn):
                    b.configure(border_width=0, text_color="#FFFFFF")

                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
                
                idx += 1

            except Exception as e:
                print(f"Error creating subcategory button for {name}: {e}")


class ComingSoonPage(ctk.CTkFrame):
    def __init__(self, parent, controller, category_name, return_to="HomePage"):
        super().__init__(parent, fg_color="#000000")
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        
        # === Scrollable main container with red scrollbar (hidden) ===
        main_scroll = ctk.CTkScrollableFrame(self, fg_color="#000000", scrollbar_fg_color="#000000",
                                           scrollbar_button_color="#000000", scrollbar_button_hover_color="#000000")
        main_scroll.pack(fill="both", expand=True)
        
        # Configure faster scroll speed (20x faster)
        def _on_mousewheel(event):
            main_scroll._parent_canvas.yview_scroll(int(-20*(event.delta/120)), "units")
        
        main_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # === Back button (top-left) - NOW RED ===
        back_btn = ctk.CTkButton(
            main_scroll,
            text="← Back",
            font=("Poppins", 20, "bold"),
            fg_color="#D00000",  # Red background
            hover_color="#B71C1C",  # Darker red on hover
            text_color="#FFFFFF",  # White text
            corner_radius=40,
            width=120,
            height=50,
            command=lambda: controller.go_back(self.return_to)
        )
        back_btn.pack(anchor="nw", padx=40, pady=(40, 0))
        
        # Center content
        center_frame = ctk.CTkFrame(main_scroll, fg_color="#000000")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title with Hero font
        title_label = ctk.CTkLabel(center_frame, text=self.category_name,
                                 font=("Hero", 36, "bold"),
                                 text_color="#FFFFFF")
        title_label.pack(pady=(0, 20))
        
        # Coming soon message with Poppins font
        msg_label = ctk.CTkLabel(center_frame, text="Coming Soon",
                               font=("Poppins", 24),
                               text_color="#A3A3A3")
        msg_label.pack()