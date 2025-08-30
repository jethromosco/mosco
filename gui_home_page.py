import customtkinter as ctk
from PIL import Image
import tkinter as tk


from home_page import categories, icon_mapping, ICON_PATH
from theme import theme



class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.categories = categories
        self.category_buttons = {}
        theme.subscribe(self.apply_theme)


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


        self.top_row = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.top_row.pack(fill="x", padx=40, pady=(40, 0))
        self.top_row.grid_columnconfigure(0, weight=1)
        self.top_row.grid_columnconfigure(1, weight=0)


        self.search_entry = ctk.CTkEntry(
            self.top_row,
            placeholder_text="🔍 Search",
            fg_color=theme.get("primary"),
            corner_radius=40,
            text_color="#FFFFFF",
            placeholder_text_color="#FFFFFF",
            font=("Poppins", 24, "bold"),
            width=176,
            height=56,
            border_width=0,
        )
        self.search_entry.grid(row=0, column=0, sticky="e")
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        self.search_entry.bind("<Enter>", lambda e: self.search_entry.configure(fg_color=theme.get("primary_hover")))
        self.search_entry.bind("<Leave>", lambda e: self.search_entry.configure(fg_color=theme.get("primary")))


        self.logo_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.logo_frame.pack(pady=20)
        self.logo_frame.bind("<Button-1>", self.remove_search_focus)


        # Load images with light and dark versions for mosco text image
        self.logo_img1 = ctk.CTkImage(Image.open(f"{ICON_PATH}\\mosco logo.png"), size=(240, 240))
        self.logo_img_text = ctk.CTkImage(
            light_image=Image.open(f"{ICON_PATH}\\mosco text light.png"),
            dark_image=Image.open(f"{ICON_PATH}\\mosco text.png"),
            size=(847, 240)
        )


        self.create_logo_section()


        self.grid_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.grid_frame.pack(pady=20)
        self.grid_frame.bind("<Button-1>", self.remove_search_focus)


        self.create_category_buttons()


        self.theme_toggle_btn = ctk.CTkButton(
            self.top_row,
            text="🌙" if theme.mode == "dark" else "🌞",
            font=("Poppins", 18, "bold"),
            width=56,
            height=56,
            corner_radius=28,
            fg_color=theme.get("card"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            command=self._toggle_theme,
        )
        self.theme_toggle_btn.grid(row=0, column=1, padx=(10, 0))


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
            for name, btn_info in self.category_buttons.items():
                btn = btn_info['button']
                row = btn_info['original_row']
                col = btn_info['original_col']
                btn.grid(row=row, column=col, padx=20, pady=20)
            return
        for btn_info in self.category_buttons.values():
            btn_info['button'].grid_remove()
        matching_categories = []
        for name, btn_info in self.category_buttons.items():
            if self._normalize(name).startswith(query):
                matching_categories.append((name, btn_info))
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
            for btn_info in self.category_buttons.values():
                btn = btn_info['button']
                btn.configure(
                    fg_color=theme.get("card"),
                    hover_color=theme.get("accent_hover"),
                    text_color=theme.get("text"),
                )
        except Exception as e:
            print(f"Error applying theme: {e}")
    
    def _normalize(self, text: str) -> str:
        return "".join(ch.lower() for ch in text if ch.isalnum())
    
    def on_search_change(self, event=None):
        query = self._normalize(self.search_entry.get())
        if not query:
            for name, btn_info in self.category_buttons.items():
                btn = btn_info['button']
                row = btn_info['original_row']
                col = btn_info['original_col']
                btn.grid(row=row, column=col, padx=20, pady=20)
            return
        for btn_info in self.category_buttons.values():
            btn_info['button'].grid_remove()
        matching_categories = []
        for name, btn_info in self.category_buttons.items():
            if self._normalize(name).startswith(query):
                matching_categories.append((name, btn_info))
        cols = 3
        for idx, (name, btn_info) in enumerate(matching_categories):
            btn = btn_info['button']
            row, col = divmod(idx, cols)
            btn.grid(row=row, column=col, padx=20, pady=20)


    def _toggle_theme(self):
        theme.toggle()
        # Update toggle button text immediately
        self.theme_toggle_btn.configure(text="🌙" if theme.mode == "dark" else "🌞")


    def apply_theme(self):
        """Apply theme changes to all widgets"""
        try:
            # Update main frame
            self.configure(fg_color=theme.get("bg"))
            
            # Update scrollable frame
            self.main_scroll.configure(
                fg_color=theme.get("bg"),
                scrollbar_fg_color=theme.get("scroll_trough"),
                scrollbar_button_color=theme.get("scroll_thumb"),
                scrollbar_button_hover_color=theme.get("scroll_thumb_hover")
            )
            
            # Update logo frame
            self.logo_frame.configure(fg_color=theme.get("bg"))
            
            # Update grid frame
            self.grid_frame.configure(fg_color=theme.get("bg"))
            
            # Recreate logo section with new theme
            self.create_logo_section()
            
            # Update search entry (keep white text on red background)
            self.search_entry.configure(
                fg_color=theme.get("primary"),
                text_color="#FFFFFF",  # Always white
                placeholder_text_color="#FFFFFF"  # Always white
            )
            
            # Update theme toggle button
            self.theme_toggle_btn.configure(
                fg_color=theme.get("card"),
                hover_color=theme.get("accent_hover"),
                text_color=theme.get("text"),
                text="🌙" if theme.mode == "dark" else "🌞"
            )
            
            # Update all category buttons with new theme
            for btn_info in self.category_buttons.values():
                btn = btn_info['button']
                btn.configure(
                    fg_color=theme.get("card"),
                    hover_color=theme.get("accent_hover"),
                    text_color=theme.get("text")
                )
                
        except Exception as e:
            print(f"Error applying theme: {e}")



class CategoryPage(ctk.CTkFrame):
    def __init__(self, parent, controller, category_name, sub_data, return_to="HomePage"):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        theme.subscribe(self.apply_theme)

        # Header frame outside & above scrollable frame to fix back button movement
        self.header_frame = ctk.CTkFrame(self, fg_color=theme.get("bg"), height=120)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 0))
        self.header_frame.pack_propagate(False)
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.back_btn = ctk.CTkButton(
            self.header_frame,
            text="← Back", font=("Poppins", 20, "bold"),
            fg_color=theme.get("primary"), hover_color=theme.get("primary_hover"), text_color="#FFFFFF",
            corner_radius=40, width=120, height=50,
            command=lambda: controller.go_back(self.return_to)
        )
        self.back_btn.grid(row=0, column=0, sticky="w", padx=(40, 10), pady=35)

        # Add theme toggle button (same as HomePage)
        self.theme_toggle_btn = ctk.CTkButton(
            self.header_frame,
            text="🌙" if theme.mode == "dark" else "🌞",
            font=("Poppins", 18, "bold"),
            width=56,
            height=56,
            corner_radius=28,
            fg_color=theme.get("card"),
            hover_color=theme.get("accent_hover"),
            text_color=theme.get("text"),
            command=self._toggle_theme,
        )
        self.theme_toggle_btn.grid(row=0, column=1, padx=(10, 20), pady=32)
        
        # Now create the scrollable frame for content below header
        # Scrollbar colors set to background colors => scrollbar hidden visually
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=theme.get("bg"),
                                                  scrollbar_fg_color=theme.get("bg"),
                                                  scrollbar_button_color=theme.get("bg"),
                                                  scrollbar_button_hover_color=theme.get("bg"))
        self.main_scroll.pack(fill="both", expand=True)

        self.title_label = ctk.CTkLabel(self.main_scroll, text=self.category_name,
                                        font=("Hero", 36, "bold"), text_color=theme.get("text"))
        self.title_label.pack(pady=40)

        self.grid_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.grid_frame.pack(pady=20)
        self.subcategory_buttons = []
        self.create_subcategory_buttons(self.grid_frame, sub_data)

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
            self.header_frame.configure(fg_color=theme.get("bg"))
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

            self.title_label.configure(text_color=theme.get("text"))

            for btn in self.subcategory_buttons:
                btn.configure(
                    fg_color=theme.get("card"),
                    hover_color=theme.get("accent_hover"),
                    text_color=theme.get("text")
                )
        except Exception as e:
            print(f"Error applying theme to CategoryPage: {e}")

class ComingSoonPage(ctk.CTkFrame):
    def __init__(self, parent, controller, category_name, return_to="HomePage"):
        super().__init__(parent, fg_color=theme.get("bg"))
        self.controller = controller
        self.category_name = category_name
        self.return_to = return_to
        theme.subscribe(self.apply_theme)
        
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=theme.get("bg"), scrollbar_fg_color=theme.get("scroll_trough"),
                                                  scrollbar_button_color=theme.get("scroll_thumb"), scrollbar_button_hover_color=theme.get("scroll_thumb_hover"))
        self.main_scroll.pack(fill="both", expand=True)
        
        def _on_mousewheel(event):
            self.main_scroll._parent_canvas.yview_scroll(int(-20*(event.delta/120)), "units")
        self.main_scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        self.back_btn = ctk.CTkButton(
            self.main_scroll, text="← Back", font=("Poppins", 20, "bold"),
            fg_color=theme.get("primary"), hover_color=theme.get("primary_hover"), text_color="#FFFFFF",
            corner_radius=40, width=120, height=50,
            command=lambda: controller.go_back(self.return_to)
        )
        self.back_btn.pack(anchor="nw", padx=40, pady=(40, 0))
        
        self.center_frame = ctk.CTkFrame(self.main_scroll, fg_color=theme.get("bg"))
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.center_frame, text=self.category_name,
                                        font=("Hero", 36, "bold"), text_color=theme.get("text"))
        self.title_label.pack(pady=(0, 20))
        
        self.msg_label = ctk.CTkLabel(self.center_frame, text="Coming Soon",
                                      font=("Poppins", 24), text_color=theme.get("muted_alt"))
        self.msg_label.pack()


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
            self.center_frame.configure(fg_color=theme.get("bg"))
            
            # Update back button
            self.back_btn.configure(
                fg_color=theme.get("primary"),
                hover_color=theme.get("primary_hover"),
                text_color="#FFFFFF"
            )
            
            # Update labels
            self.title_label.configure(text_color=theme.get("text"))
            self.msg_label.configure(text_color=theme.get("muted_alt"))
            
        except Exception as e:
            print(f"Error applying theme to ComingSoonPage: {e}")
