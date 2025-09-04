import customtkinter as ctk
from PIL import Image
import tkinter as tk

# Import both icon mappings
from home_page import categories, icon_mapping, subcategory_icon_mapping, ICON_PATH
from theme import theme


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.categories = categories
        self.category_buttons = {}
        theme.subscribe(self.apply_theme)

        # Create main scroll frame that fills the entire window
        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.get("bg"),
            scrollbar_fg_color=theme.get("scroll_trough"),
            scrollbar_button_color=theme.get("scroll_thumb"),
            scrollbar_button_hover_color=theme.get("scroll_thumb_hover"),
        )
        self.main_scroll.pack(fill="both", expand=True)

        def _on_mousewheel(event):
            self.main_scroll._parent_canvas.yview_scroll(int(-50 * (event.delta / 120)), "units")

        self.main_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.main_scroll.bind("<Button-1>", self.remove_search_focus)

        # ------------------ FIXED ELEMENTS ------------------
        # Search Entry - Top Left (same size as back button)
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Search",
            fg_color=theme.get("primary"),
            corner_radius=40,
            text_color="#FFFFFF",
            placeholder_text_color="#FFFFFF",
            font=("Poppins", 20, "bold"),
            width=150,
            height=50,
            border_width=0,
        )
        self.search_entry.place(x=40, y=40)

        # Always-uppercase on key release (preserves placeholder)
        self.search_entry.bind("<KeyRelease>", self._caps_and_search)

        self.search_entry.bind("<Enter>", lambda e: self.search_entry.configure(fg_color=theme.get("primary_hover")))
        self.search_entry.bind("<Leave>", lambda e: self.search_entry.configure(fg_color=theme.get("primary")))

        # Theme Toggle Button - Top Right
        self.theme_toggle_btn = ctk.CTkButton(
            self,
            text="🌙" if theme.mode == "dark" else "🌞",
            font=("Poppins", 18, "bold"),
            width=100,          # match Admin button width
            height=50,          # match Admin button height
            corner_radius=25,   # match Admin button corner radius
            fg_color=theme.get("card"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            command=self._toggle_theme,
        )
        self.theme_toggle_btn.place(x=1200, y=40)

        # Watermark - Bottom Right
        self.watermark_label = ctk.CTkLabel(
            self,
            text="developed by jethro · 2025",
            font=("Poppins", 10, "italic"),
            text_color=theme.get("muted"),
            fg_color=None
        )
        self.watermark_label.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=10)

        # MOSCO Logo - inside scroll
        self.logo_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.logo_frame.pack(pady=20)
        self.logo_frame.bind("<Button-1>", self.remove_search_focus)

        self.logo_img1 = ctk.CTkImage(
            light_image=Image.open(f"{ICON_PATH}\\mosco logo light.png"),
            dark_image=Image.open(f"{ICON_PATH}\\mosco logo.png"),
            size=(240, 240)
        )
        self.logo_img_text = ctk.CTkImage(
            light_image=Image.open(f"{ICON_PATH}\\mosco text light.png"),
            dark_image=Image.open(f"{ICON_PATH}\\mosco text.png"),
            size=(847, 240)
        )
        self.create_logo_section()

        # Category Grid
        self.grid_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.grid_frame.pack(pady=20)
        self.grid_frame.bind("<Button-1>", self.remove_search_focus)

        self.create_category_buttons()

        # Resize binding
        self.bind("<Configure>", self.on_window_resize)

    # ------------------ METHODS ------------------

    def _caps_and_search(self, event=None):
        """Force uppercase while preserving cursor + trigger search"""
        txt = self.search_entry.get()
        up = txt.upper()
        if txt != up:
            pos = self.search_entry.index("insert")
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, up)
            self.search_entry.icursor(pos)
        self.on_search_change()

    def on_window_resize(self, event=None):
        """Update absolute positioned elements on window resize"""
        if hasattr(self, 'theme_toggle_btn') and self.theme_toggle_btn.winfo_exists():
            window_width = self.winfo_width()
            if window_width > 1:
                self.theme_toggle_btn.place(x=window_width-140, y=40)  
                # 100 (button width) + 40 (margin) = 140

    def create_logo_section(self):
        for widget in self.logo_frame.winfo_children():
            widget.destroy()
        try:
            lbl1 = ctk.CTkLabel(self.logo_frame, image=self.logo_img1, text="", bg_color=theme.get("bg"))
            lbl1.pack(side="left", padx=(0, 10))
            lbl1.bind("<Button-1>", self.remove_search_focus)

            lbl2 = ctk.CTkLabel(self.logo_frame, image=self.logo_img_text, text="", bg_color=theme.get("bg"))
            lbl2.pack(side="left")
            lbl2.bind("<Button-1>", self.remove_search_focus)
        except Exception as e:
            print(f"Error loading logos: {e}")
            title_label = ctk.CTkLabel(self.logo_frame, text="MOSCO", font=("Hero", 48, "bold"), text_color=theme.get("text"))
            title_label.pack()
            title_label.bind("<Button-1>", self.remove_search_focus)

    def remove_search_focus(self, event=None):
        self.focus()

    def create_category_buttons(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.category_buttons.clear()

        cols = 3
        for idx, (label, sub_data) in enumerate(self.categories.items()):
            try:
                img_path = icon_mapping.get(label, f"{ICON_PATH}\\special.png")
                try:
                    img = Image.open(img_path).resize((150, 150))
                    tk_img = ctk.CTkImage(light_image=img, size=(150, 150))
                except:
                    img = Image.new('RGB', (150, 150), color='#444444')
                    tk_img = ctk.CTkImage(light_image=img, size=(150, 150))

                btn = ctk.CTkButton(
                    self.grid_frame,
                    text=label,
                    image=tk_img,
                    compound="top",
                    font=("Poppins", 24, "bold"),
                    fg_color=theme.get("card"),
                    hover_color=theme.get("accent_hover"),
                    text_color=theme.get("text"),
                    corner_radius=40,
                    width=504,
                    height=268,
                    border_width=0,
                    command=lambda l=label, s=sub_data: self.controller.show_subcategory(l, s)
                )
                btn.image = tk_img
                row, col = divmod(idx, cols)
                btn.grid(row=row, column=col, padx=20, pady=20)

                self.category_buttons[label] = {'button': btn, 'original_row': row, 'original_col': col}
                btn.bind("<Enter>", lambda e, b=btn: b.configure(border_width=3, border_color=theme.get("primary"), text_color=theme.get("muted")))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(border_width=0, text_color=theme.get("text"), fg_color=theme.get("card")))
                btn.bind("<Button-1>", self.remove_search_focus)
            except Exception as e:
                print(f"Error creating button for {label}: {e}")

    def _normalize(self, text: str) -> str:
        return "".join(ch.lower() for ch in text if ch.isalnum())

    def on_search_change(self, event=None):
        query = self._normalize(self.search_entry.get())
        if not query:
            # Show all categories when search is empty
            for name, btn_info in self.category_buttons.items():
                btn = btn_info['button']
                row = btn_info['original_row']
                col = btn_info['original_col']
                btn.grid(row=row, column=col, padx=20, pady=20)
            return
        
        # Hide all categories first
        for btn_info in self.category_buttons.values():
            btn_info['button'].grid_remove()
        
        matching_categories = []
        
        for name, btn_info in self.category_buttons.items():
            category_data = self.categories[name]
            
            # Check if main category name matches
            if self._normalize(name).startswith(query) or query in self._normalize(name):
                matching_categories.append((name, btn_info))
                continue
            
            # Check if any subcategory name matches
            if isinstance(category_data, dict):
                for subcategory_name in category_data.keys():
                    normalized_sub = self._normalize(subcategory_name)
                    if query in normalized_sub or normalized_sub.startswith(query):
                        matching_categories.append((name, btn_info))
                        break  # Found match in this category, no need to check more subcategories
        
        # Display matching categories
        cols = 3
        for idx, (name, btn_info) in enumerate(matching_categories):
            btn = btn_info['button']
            row, col = divmod(idx, cols)
            btn.grid(row=row, column=col, padx=20, pady=20)

    def _toggle_theme(self):
        theme.toggle()
        self.theme_toggle_btn.configure(text="🌙" if theme.mode == "dark" else "🌞")
        self.apply_theme()

    def apply_theme(self):
        try:
            self.configure(fg_color=theme.get("bg"))
            self.main_scroll.configure(
                fg_color=theme.get("bg"),
                scrollbar_fg_color=theme.get("scroll_trough"),
                scrollbar_button_color=theme.get("scroll_thumb"),
                scrollbar_button_hover_color=theme.get("scroll_thumb_hover"),
            )
            self.logo_frame.configure(fg_color=theme.get("bg"))
            self.grid_frame.configure(fg_color=theme.get("bg"))
            self.create_logo_section()
            self.search_entry.configure(
                fg_color=theme.get("primary"),
                text_color="#FFFFFF",
                placeholder_text_color="#FFFFFF",
            )
            self.theme_toggle_btn.configure(
                fg_color=theme.get("card"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text"),
                text="🌙" if theme.mode == "dark" else "🌞",
            )
            # Update watermark theme
            self.watermark_label.configure(text_color=theme.get("muted"))
            
            for btn_info in self.category_buttons.values():
                btn = btn_info['button']
                btn.configure(
                    fg_color=theme.get("card"),
                    hover_color=theme.get("accent_hover"),
                    text_color=theme.get("text"),
                )
            # Update button positions after theme change
            self.after(10, self.on_window_resize)
        except Exception as e:
            print(f"Error applying theme: {e}")


class CategoryPage(ctk.CTkFrame):
    def __init__(self, parent, controller, category_name, sub_data, return_to="HomePage"):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        theme.subscribe(self.apply_theme)

        # Create main scroll frame that fills the entire window
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=theme.get("bg"),
                                                  scrollbar_fg_color=theme.get("bg"),
                                                  scrollbar_button_color=theme.get("bg"),
                                                  scrollbar_button_hover_color=theme.get("bg"))
        self.main_scroll.pack(fill="both", expand=True)

        # ABSOLUTE POSITIONED ELEMENTS - FIXED POSITIONS
        # Back Button - Top Left
        self.back_btn = ctk.CTkButton(
            self,
            text="← Back", font=("Poppins", 20, "bold"),
            fg_color=theme.get("primary"), hover_color=theme.get("primary_hover"), text_color="#FFFFFF",
            corner_radius=40, width=120, height=50,
            command=lambda: controller.go_back(self.return_to)
        )
        self.back_btn.place(x=40, y=40)

        # Theme Toggle Button - Top Right
        self.theme_toggle_btn = ctk.CTkButton(
            self,
            text="🌙" if theme.mode == "dark" else "🌞",
            font=("Poppins", 18, "bold"),
            width=100,          # match Admin button width
            height=50,          # match Admin button height
            corner_radius=25,   # match Admin button corner radius
            fg_color=theme.get("card"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            command=self._toggle_theme,
        )
        self.theme_toggle_btn.place(x=1200, y=40)

        # Watermark - Bottom Right
        self.watermark_label = ctk.CTkLabel(
            self,
            text="developed by jethro · 2025",
            font=("Poppins", 10, "italic"),
            text_color=theme.get("muted"),
            fg_color=None
        )
        self.watermark_label.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=10)

        # MOSCO Logo - SCROLLABLE (inside main_scroll, not fixed)
        self.logo_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.logo_frame.pack(pady=20)

        # Load images with light and dark versions for mosco text image
        self.logo_img1 = ctk.CTkImage(
            light_image=Image.open(f"{ICON_PATH}\\mosco logo light.png"),
            dark_image=Image.open(f"{ICON_PATH}\\mosco logo.png"),
            size=(240, 240)
        )
        self.logo_img_text = ctk.CTkImage(
            light_image=Image.open(f"{ICON_PATH}\\mosco text light.png"),
            dark_image=Image.open(f"{ICON_PATH}\\mosco text.png"),
            size=(847, 240)
        )

        self.create_logo_section()

        # Category title - positioned below logo  
        self.title_label = ctk.CTkLabel(self.main_scroll, text=self.category_name,
                                        font=("Hero", 36, "bold"), text_color=theme.get("text"))
        self.title_label.pack(pady=(20, 40))

        self.grid_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.grid_frame.pack(pady=20)
        self.subcategory_buttons = []
        self.create_subcategory_buttons(self.grid_frame, sub_data)

        # Bind window resize to update button positions
        self.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event=None):
        """Update absolute positioned elements on window resize"""
        if hasattr(self, 'theme_toggle_btn') and self.theme_toggle_btn.winfo_exists():
            window_width = self.winfo_width()
            if window_width > 1:
                self.theme_toggle_btn.place(x=window_width-140, y=40)  
                # 100 (button width) + 40 (margin) = 140

    def create_logo_section(self):
        """Create the MOSCO logo section (SAME SIZE AS HOMEPAGE)"""
        for widget in self.logo_frame.winfo_children():
            widget.destroy()

        try:
            lbl1 = ctk.CTkLabel(self.logo_frame, image=self.logo_img1, text="", bg_color=theme.get("bg"))
            lbl1.pack(side="left", padx=(0, 10))
            lbl1.bind("<Button-1>", self.remove_focus)

            lbl2 = ctk.CTkLabel(self.logo_frame, image=self.logo_img_text, text="", bg_color=theme.get("bg"))
            lbl2.pack(side="left")
            lbl2.bind("<Button-1>", self.remove_focus)

        except Exception as e:
            print(f"Error loading logos: {e}")
            title_label = ctk.CTkLabel(self.logo_frame, text="MOSCO", font=("Hero", 48, "bold"), text_color=theme.get("text"))
            title_label.pack()
            title_label.bind("<Button-1>", self.remove_focus)

    def remove_focus(self, event=None):
        """Remove focus from any focused widget"""
        self.focus()

    def _toggle_theme(self):
        """Toggle between light and dark theme"""
        theme.toggle()
        self.theme_toggle_btn.configure(text="🌙" if theme.mode == "dark" else "🌞")
        self.apply_theme()

    def create_subcategory_buttons(self, grid_frame, sub_data):
        for btn in self.subcategory_buttons:
            btn.destroy()
        self.subcategory_buttons.clear()

        cols = 3
        idx = 0
        for name, sub in sub_data.items():
            try:
                # Try to get icon from subcategory_icon_mapping first, then fallback to generic
                img_path = subcategory_icon_mapping.get(name, None)
                if img_path:
                    try:
                        img = Image.open(img_path).resize((150, 150))
                        tk_img = ctk.CTkImage(light_image=img, size=(150, 150))
                    except Exception as e:
                        print(f"Error loading subcategory icon for {name}: {e}")
                        img = Image.new('RGB', (150, 150), color='#333333')
                        tk_img = ctk.CTkImage(light_image=img, size=(150, 150))
                else:
                    # Fallback to generic placeholder
                    img = Image.new('RGB', (150, 150), color='#333333')
                    tk_img = ctk.CTkImage(light_image=img, size=(150, 150))

                if sub is None:
                    command = lambda n=f"{self.category_name} {name}": self.controller.show_inventory_for(n)
                else:
                    command = lambda n=name, s=sub: self.controller.show_subcategory(n, s)

                btn = ctk.CTkButton(
                    grid_frame, text=name, image=tk_img, compound="top",
                    font=("Poppins", 20, "bold"), fg_color=theme.get("card"),
                    hover_color=theme.get("accent_hover"), text_color=theme.get("text"),
                    corner_radius=40, width=404, height=220,
                    border_width=0, command=command
                )
                btn.image = tk_img
                row, col = divmod(idx, cols)
                btn.grid(row=row, column=col, padx=15, pady=15)
                btn.bind("<Enter>", lambda e, b=btn: b.configure(border_width=3, border_color=theme.get("primary"), text_color=theme.get("muted")))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(border_width=0, text_color=theme.get("text")))

                self.subcategory_buttons.append(btn)
                idx += 1
            except Exception as e:
                print(f"Error creating subcategory button for {name}: {e}")

    def apply_theme(self):
        try:
            self.configure(fg_color=theme.get("bg"))
            self.main_scroll.configure(
                fg_color=theme.get("bg"),
                scrollbar_fg_color=theme.get("bg"),
                scrollbar_button_color=theme.get("bg"),
                scrollbar_button_hover_color=theme.get("bg")
            )
            self.logo_frame.configure(fg_color=theme.get("bg"))
            self.grid_frame.configure(fg_color=theme.get("bg"))

            self.back_btn.configure(
                fg_color=theme.get("primary"),
                hover_color=theme.get("primary_hover"),
                text_color="#FFFFFF"
            )

            # Update theme toggle button
            self.theme_toggle_btn.configure(
                fg_color=theme.get("card"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text"),
                text="🌙" if theme.mode == "dark" else "🌞"
            )

            # Update watermark theme
            self.watermark_label.configure(text_color=theme.get("muted"))

            # Recreate logo section with new theme (important for light/dark mode switching)
            self.create_logo_section()

            self.title_label.configure(text_color=theme.get("text"))

            for btn in self.subcategory_buttons:
                btn.configure(
                    fg_color=theme.get("card"),
                    hover_color=theme.get("accent_hover"),
                    text_color=theme.get("text")
                )
            
            # Update button positions after theme change
            self.after(10, self.on_window_resize)
        except Exception as e:
            print(f"Error applying theme to CategoryPage: {e}")


class ComingSoonPage(ctk.CTkFrame):
    def __init__(self, parent, controller, category_name, return_to="HomePage"):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        theme.subscribe(self.apply_theme)

        # Create main scroll frame that fills the entire window
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=theme.get("bg"), scrollbar_fg_color=theme.get("scroll_trough"),
                                                  scrollbar_button_color=theme.get("scroll_thumb"), scrollbar_button_hover_color=theme.get("scroll_thumb_hover"))
        self.main_scroll.pack(fill="both", expand=True)
        
        def _on_mousewheel(event):
            self.main_scroll._parent_canvas.yview_scroll(int(-20*(event.delta/120)), "units")
        self.main_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # ABSOLUTE POSITIONED ELEMENTS - FIXED POSITIONS
        # Back Button - Top Left
        self.back_btn = ctk.CTkButton(
            self,
            text="← Back", font=("Poppins", 20, "bold"),
            fg_color=theme.get("primary"), hover_color=theme.get("primary_hover"), text_color="#FFFFFF",
            corner_radius=40, width=120, height=50,
            command=lambda: controller.go_back(self.return_to)
        )
        self.back_btn.place(x=40, y=40)

        # Theme Toggle Button - Top Right  
        self.theme_toggle_btn = ctk.CTkButton(
            self,
            text="🌙" if theme.mode == "dark" else "🌞",
            font=("Poppins", 18, "bold"),
            width=100,          # match Admin button width
            height=50,          # match Admin button height
            corner_radius=25,   # match Admin button corner radius
            fg_color=theme.get("card"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            command=self._toggle_theme,
        )
        self.theme_toggle_btn.place(x=1200, y=40)

        # Watermark - Bottom Right
        self.watermark_label = ctk.CTkLabel(
            self,
            text="developed by jethro · 2025",
            font=("Poppins", 10, "italic"),
            text_color=theme.get("muted"),
            fg_color=None
        )
        self.watermark_label.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=10)

        # MOSCO Logo - SCROLLABLE (inside main_scroll, not fixed)  
        self.logo_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.logo_frame.pack(pady=20)

        # Load images with light and dark versions for mosco text image
        self.logo_img1 = ctk.CTkImage(
            light_image=Image.open(f"{ICON_PATH}\\mosco logo light.png"),
            dark_image=Image.open(f"{ICON_PATH}\\mosco logo.png"),
            size=(240, 240)
        )
        self.logo_img_text = ctk.CTkImage(
            light_image=Image.open(f"{ICON_PATH}\\mosco text light.png"),
            dark_image=Image.open(f"{ICON_PATH}\\mosco text.png"),
            size=(847, 240)
        )

        self.create_logo_section()
        
        # Content - positioned below fixed elements
        self.center_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.center_frame.pack(pady=(20, 0), fill="both", expand=True)
        
        # Create inner frame for centering content
        self.inner_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.inner_frame.place(relx=0.5, rely=0.3, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.inner_frame, text=self.category_name,
                                        font=("Hero", 36, "bold"), text_color=theme.get("text"))
        self.title_label.pack(pady=(0, 20))
        
        self.msg_label = ctk.CTkLabel(self.inner_frame, text="Coming Soon",
                                      font=("Poppins", 24), text_color=theme.get("muted_alt"))
        self.msg_label.pack()

        # Bind window resize to update button positions
        self.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event=None):
        """Update absolute positioned elements on window resize"""
        if hasattr(self, 'theme_toggle_btn') and self.theme_toggle_btn.winfo_exists():
            window_width = self.winfo_width()
            if window_width > 1:
                self.theme_toggle_btn.place(x=window_width-140, y=40)  
                # 100 (button width) + 40 (margin) = 140
                
    def create_logo_section(self):
        """Create the MOSCO logo section"""
        for widget in self.logo_frame.winfo_children():
            widget.destroy()

        try:
            lbl1 = ctk.CTkLabel(self.logo_frame, image=self.logo_img1, text="", bg_color=theme.get("bg"))
            lbl1.pack(side="left", padx=(0, 10))

            lbl2 = ctk.CTkLabel(self.logo_frame, image=self.logo_img_text, text="", bg_color=theme.get("bg"))
            lbl2.pack(side="left")

        except Exception as e:
            print(f"Error loading logos: {e}")
            title_label = ctk.CTkLabel(self.logo_frame, text="MOSCO", font=("Hero", 48, "bold"), text_color=theme.get("text"))
            title_label.pack()

    def _toggle_theme(self):
        theme.toggle()
        self.theme_toggle_btn.configure(text="🌙" if theme.mode == "dark" else "🌞")
        self.apply_theme()

    def apply_theme(self):
        try:
            # Update main frames
            self.configure(fg_color=theme.get("bg"))
            self.main_scroll.configure(
                fg_color=theme.get("bg"),
                scrollbar_fg_color=theme.get("scroll_trough"),
                scrollbar_button_color=theme.get("scroll_thumb"),
                scrollbar_button_hover_color=theme.get("scroll_thumb_hover")
            )
            self.logo_frame.configure(fg_color=theme.get("bg"))
            self.center_frame.configure(fg_color=theme.get("bg"))
            
            # Update back button
            self.back_btn.configure(
                fg_color=theme.get("primary"),
                hover_color=theme.get("primary_hover"),
                text_color="#FFFFFF"
            )

            # Update theme toggle button
            self.theme_toggle_btn.configure(
                fg_color=theme.get("card"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text"),
                text="🌙" if theme.mode == "dark" else "🌞"
            )

            # Update watermark theme
            self.watermark_label.configure(text_color=theme.get("muted"))

            # Recreate logo section
            self.create_logo_section()
            
            # Update labels
            self.title_label.configure(text_color=theme.get("text"))
            self.msg_label.configure(text_color=theme.get("muted_alt"))
            
            # Update button positions
            self.after(10, self.on_window_resize)
            
        except Exception as e:
            print(f"Error applying theme to ComingSoonPage: {e}")