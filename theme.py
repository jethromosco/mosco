from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Dict, List

DarkPalette: Dict[str, str] = {
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
    "table_selected": "#505760",   # updated grey (was #374151)
    "heading_fg": "#D00000",
    "heading_bg": "#000000",
    "scroll_trough": "#111111",
    "scroll_thumb": "#3A3A3A",
    "scroll_thumb_hover": "#4A4A4A",
    "combo_hover": "#4B5563",
}

LightPalette: Dict[str, str] = {
    "bg": "#FFFFFF",
    "card": "#F5F5F5",
    "card_alt": "#EAEAEA",
    "input": "#E0E0E0",
    "input_focus": "#CCCCCC",
    "text": "#000000",
    "muted": "#4B4B4B",
    "muted_alt": "#6E6E6E",
    "border": "#BDBDBD",
    "primary": "#D00000",
    "primary_hover": "#B71C1C",
    "accent": "#E0E0E0",
    "accent_hover": "#D5D5D5",
    "table_selected": "#D1D1D1",    # updated grey (was #EAEAEA)
    "heading_fg": "#D00000",
    "heading_bg": "#FFFFFF",
    "scroll_trough": "#F0F0F0",
    "scroll_thumb": "#C4C4C4",
    "scroll_thumb_hover": "#AFAFAF",
    "combo_hover": "#D5D5D5",
}

class ThemeManager:
    def __init__(self) -> None:
        self._mode: str = "dark"  # default
        self._palette: Dict[str, str] = DarkPalette.copy()
        self._listeners: List[Callable[[], None]] = []

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def palette(self) -> Dict[str, str]:
        return self._palette

    def get(self, key: str, default: str | None = None) -> str:
        return self._palette.get(key, default or "#000000")

    def subscribe(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def set_mode(self, mode: str) -> None:
        mode_lower = mode.lower()
        if mode_lower not in ("dark", "light"):
            return
        self._mode = mode_lower
        self._palette = DarkPalette.copy() if mode_lower == "dark" else LightPalette.copy()
        ctk.set_appearance_mode("dark" if mode_lower == "dark" else "light")
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass

    def toggle(self) -> None:
        self.set_mode("light" if self._mode == "dark" else "dark")

# Singleton instance
theme = ThemeManager()
