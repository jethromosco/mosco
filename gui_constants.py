"""
GUI Constants and Configuration

Centralized store for hardcoded GUI values like fonts, dimensions, colors, and spacing.
This makes it easy to maintain consistent UI across all modules and allows future
changes to styling without touching multiple files.

All values can be imported and overridden by theme colors without breaking the app.
"""

from typing import Tuple

# ========== FONT CONFIGURATION ==========
# Main application fonts
FONT_MAIN_TITLE = ("Hero", 48, "bold")           # MOSCO logo
FONT_CATEGORY_TITLE = ("Poppins", 20, "bold")    # Category page titles
FONT_BUTTON_PRIMARY = ("Poppins", 24, "bold")    # Primary action buttons
FONT_BUTTON_SECONDARY = ("Poppins", 14, "bold")  # Secondary buttons
FONT_TAB_LABEL = ("Poppins", 16, "bold")         # Tab headers
FONT_LABEL_DEFAULT = ("Poppins", 14)             # Default label text
FONT_LABEL_SMALL = ("Poppins", 12)               # Small labels
FONT_TABLE_HEADER = ("Poppins", 12, "bold")      # Table column headers
FONT_TABLE_CELL = ("Poppins", 11)                # Table cell contents
FONT_INPUT_PLACEHOLDER = ("Poppins", 10, "italic")  # Placeholder text
FONT_THEME_TOGGLE = ("Poppins", 18, "bold")     # Theme toggle button

# ========== BUTTON DIMENSIONS ==========
# Primary large buttons (main category buttons)
BUTTON_PRIMARY_LARGE_WIDTH = 504
BUTTON_PRIMARY_LARGE_HEIGHT = 268
BUTTON_PRIMARY_CORNER_RADIUS = 40

# Secondary larger buttons (grid items)
BUTTON_SECONDARY_GRID_WIDTH = 150
BUTTON_SECONDARY_GRID_HEIGHT = 140

# Compact buttons (dialogs, toolbars)
BUTTON_COMPACT_WIDTH = 100
BUTTON_COMPACT_HEIGHT = 50
BUTTON_COMPACT_CORNER_RADIUS = 25

# Minimal buttons (icon buttons, toggles)
BUTTON_MINIMAL_WIDTH = 150
BUTTON_MINIMAL_HEIGHT = 50
BUTTON_MINIMAL_CORNER_RADIUS = 40

# Admin panel buttons
BUTTON_ADMIN_WIDTH = 100
BUTTON_ADMIN_HEIGHT = 40
BUTTON_ADMIN_CORNER_RADIUS = 20

# ========== DROPDOWN/COMBOBOX DIMENSIONS ==========
DROPDOWN_WIDTH = 150
DROPDOWN_HEIGHT = 40
DROPDOWN_CORNER_RADIUS = 40

DROPDOWN_SUBCATEGORY_WIDTH = 140
DROPDOWN_UNIT_WIDTH = 120

# ========== ENTRY FIELD DIMENSIONS ==========
ENTRY_SEARCH_WIDTH = 150
ENTRY_SEARCH_HEIGHT = 40
ENTRY_SEARCH_CORNER_RADIUS = 40

# ========== SPACING AND PADDING ==========
# Standard padding amounts
PADDING_LARGE = 20
PADDING_MEDIUM = 15
PADDING_SMALL = 10
PADDING_TINY = 5

# Standard margins
MARGIN_OUTER = (20, 20)  # (x, y) padding for outer frames
MARGIN_INNER = (15, 15)  # Inner frame padding
MARGIN_NONE = (0, 0)

# Vertical spacing (pady for pack/grid)
SPACING_ITEM_VERTICAL = 10
SPACING_SECTION_VERTICAL = 20
SPACING_ELEMENT_VERTICAL = 5

# Horizontal spacing (padx for pack)
SPACING_ITEM_HORIZONTAL = 10
SPACING_SECTION_HORIZONTAL = 20

# ========== FRAME DIMENSIONS ==========
# Tab header frame
TAB_HEADER_HEIGHT = 60

# Card/panel corner radius
CARD_CORNER_RADIUS = 40

# Main window minimum size
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700

# Admin panel minimum size
ADMIN_PANEL_MIN_WIDTH = 900
ADMIN_PANEL_MIN_HEIGHT = 600
ADMIN_PANEL_MIN_WIDTH_IMPROVED = 1000
ADMIN_PANEL_MIN_HEIGHT_IMPROVED = 700

# ========== TABLE STYLING ==========
TABLE_ROW_HEIGHT = 25
TABLE_HEADER_HEIGHT = 30
TABLE_ALTERNATING_ROWS = True

# ========== BORDER STYLES ==========
BORDER_DEFAULT_WIDTH = 1
BORDER_HIGHLIGHT_WIDTH = 2
BORDER_NONE = 0

# ========== ANIMATION/DELAYS ==========
# Delays for animations and UI updates (in milliseconds)
DELAY_AUTO_REFRESH = 50       # Auto-refresh after dropdown change
DELAY_CONTEXT_APPLY = 100     # Context application delay
DELAY_WINDOW_RESTORE = 50     # Window geometry restore delay
DELAY_THEME_UPDATE = 1         # Theme update delay

# ========== SCALING/RESPONSIVE DESIGN ==========
# Grid layout configuration
GRID_COLS_MAIN = 3
GRID_COLS_ADMIN_SELECTOR = 10

# Grid gap/spacing
GRID_GAP = 20

# ========== UTILITY FUNCTIONS ==========
def get_button_dimensions(button_type: str) -> Tuple[int, int, int]:
    """
    Get button dimensions (width, height, corner_radius) by type.
    
    Args:
        button_type: One of 'primary_large', 'secondary_grid', 'compact', 'minimal', 'admin'
    
    Returns:
        Tuple of (width, height, corner_radius)
    """
    dimension_map = {
        "primary_large": (BUTTON_PRIMARY_LARGE_WIDTH, BUTTON_PRIMARY_LARGE_HEIGHT, BUTTON_PRIMARY_CORNER_RADIUS),
        "secondary_grid": (BUTTON_SECONDARY_GRID_WIDTH, BUTTON_SECONDARY_GRID_HEIGHT, 10),
        "compact": (BUTTON_COMPACT_WIDTH, BUTTON_COMPACT_HEIGHT, BUTTON_COMPACT_CORNER_RADIUS),
        "minimal": (BUTTON_MINIMAL_WIDTH, BUTTON_MINIMAL_HEIGHT, BUTTON_MINIMAL_CORNER_RADIUS),
        "admin": (BUTTON_ADMIN_WIDTH, BUTTON_ADMIN_HEIGHT, BUTTON_ADMIN_CORNER_RADIUS),
    }
    return dimension_map.get(button_type, (BUTTON_ADMIN_WIDTH, BUTTON_ADMIN_HEIGHT, BUTTON_ADMIN_CORNER_RADIUS))

def get_font(font_type: str) -> Tuple[str, int, str] | Tuple[str, int]:
    """
    Get font configuration by type.
    
    Args:
        font_type: One of the FONT_* constants
    
    Returns:
        Tuple of (family, size) or (family, size, style)
    """
    font_map = {
        "title": FONT_MAIN_TITLE,
        "category": FONT_CATEGORY_TITLE,
        "button_primary": FONT_BUTTON_PRIMARY,
        "button_secondary": FONT_BUTTON_SECONDARY,
        "tab": FONT_TAB_LABEL,
        "label": FONT_LABEL_DEFAULT,
        "label_small": FONT_LABEL_SMALL,
        "table_header": FONT_TABLE_HEADER,
        "table_cell": FONT_TABLE_CELL,
        "placeholder": FONT_INPUT_PLACEHOLDER,
        "theme_toggle": FONT_THEME_TOGGLE,
    }
    return font_map.get(font_type, FONT_LABEL_DEFAULT)
