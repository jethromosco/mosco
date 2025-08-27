import customtkinter as ctk


class ThemeManager:
    current_mode = "dark"

    # Core palettes for light and dark. Keep primary red consistent.
    palettes = {
        "dark": {
            "bg": "#000000",
            "card": "#2b2b2b",
            "card_alt": "#111111",
            "input": "#374151",
            "input_focus": "#1F2937",
            "text": "#FFFFFF",
            "muted": "#CCCCCC",
            "muted_alt": "#A3A3A3",
            "border": "#4B5563",
            "primary": "#D00000",
            "primary_hover": "#B71C1C",
            "accent": "#4B5563",
            "accent_hover": "#6B7280",
            "table_selected": "#374151",
            "heading_fg": "#D00000",
            "heading_bg": "#000000",
            "scroll_trough": "#111111",
            "scroll_thumb": "#3A3A3A",
            "scroll_thumb_hover": "#4A4A4A",
            "combo_hover": "#4B5563",
        },
        "light": {
            "bg": "#FFFFFF",
            "card": "#F3F4F6",
            "card_alt": "#E5E7EB",
            "input": "#F9FAFB",
            "input_focus": "#E0E7FF",
            "text": "#000000",
            "muted": "#4B5563",
            "muted_alt": "#6B7280",
            "border": "#D1D5DB",
            "primary": "#D00000",
            "primary_hover": "#B71C1C",
            "accent": "#E5E7EB",
            "accent_hover": "#D1D5DB",
            "table_selected": "#E5E7EB",
            "heading_fg": "#D00000",
            "heading_bg": "#FFFFFF",
            "scroll_trough": "#F3F4F6",
            "scroll_thumb": "#D1D5DB",
            "scroll_thumb_hover": "#9CA3AF",
            "combo_hover": "#E5E7EB",
        },
    }

    @classmethod
    def set_mode(cls, mode: str):
        mode = mode.lower()
        if mode not in ("light", "dark"):
            return
        cls.current_mode = mode
        ctk.set_appearance_mode("light" if mode == "light" else "dark")

    @classmethod
    def toggle_mode(cls):
        cls.set_mode("light" if cls.current_mode == "dark" else "dark")

    @classmethod
    def colors(cls):
        return cls.palettes[cls.current_mode]

