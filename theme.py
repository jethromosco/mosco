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
    "table_selected": "#505760",   # Grey for selected rows
    "unknown_stock_bg": "#6B3FA0",  # Purple for unknown stock (dark)
    "heading_fg": "#D00000",
    "heading_bg": "#000000",
    "scroll_trough": "#111111",
    "scroll_thumb": "#3A3A3A",
    "scroll_thumb_hover": "#4A4A4A",
    "combo_hover": "#4B5563",
}

LightPalette: Dict[str, str] = {
    "bg": "#E8E8E8",           # Softer off-white background
    "card": "#D8D8D8",         # Light grey card background
    "card_alt": "#C0C0C0",     # Slightly darker card alternative
    "input": "#C0C0C0",        # Softer grey input background
    "input_focus": "#A8A8A8",  # Softer focus color
    "text": "#1A1A1A",         # Very dark grey text instead of pure black
    "muted": "#3A3A3A",        # Muted text darker for contrast
    "muted_alt": "#525252",    # Alternative muted a bit lighter
    "border": "#9A9A9A",       # Softer border grey
    "primary": "#D00000",      # Keep primary red as is
    "primary_hover": "#B71C1C",# Keep hover red as is
    "accent": "#C0C0C0",       # Sofmer accents
    "accent_hover": "#A8A8A8", # Softer hover accents
    "table_selected": "#D0D0D0",    # Grey for selected rows
    "unknown_stock_bg": "#D9C4E8",  # Light purple for unknown stock (light)
    "heading_fg": "#D00000",   # Keep heading foreground red
    "heading_bg": "#E8E8E8",   # Softer heading background
    "scroll_trough": "#D0D0D0",# Scrollbar trough softer grey
    "scroll_thumb": "#A8A8A8", # Scrollbar thumb soft grey
    "scroll_thumb_hover": "#909090", # Scrollbar thumb hover slight darker
    "combo_hover": "#A8A8A8",  # Combo hover soft grey
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

    def set_mode(self, mode: str, root_window=None) -> None:
        mode_lower = mode.lower()
        if mode_lower not in ("dark", "light"):
            return
        
        # Store current geometry to restore after theme change
        current_geometry = None
        if root_window and hasattr(root_window, 'geometry'):
            try:
                current_geometry = root_window.geometry()
            except Exception:
                pass
        
        self._mode = mode_lower
        self._palette = DarkPalette.copy() if mode_lower == "dark" else LightPalette.copy()
        
        # Don't immediately call set_appearance_mode; let it be called after callbacks
        # This prevents window resizing during theme switch
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass
        
        # Now set appearance mode after callbacks complete
        ctk.set_appearance_mode("dark" if mode_lower == "dark" else "light")
        
        # Restore geometry if it was saved
        if root_window and current_geometry and hasattr(root_window, 'geometry'):
            try:
                root_window.after(50, lambda: root_window.geometry(current_geometry))
            except Exception:
                pass

    def toggle(self, root_window=None) -> None:
        self.set_mode("light" if self._mode == "dark" else "dark", root_window)

# Singleton instance
theme = ThemeManager()
