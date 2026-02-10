"""
Category Registry and Management

Centralized registry for all product categories, their implementations,
and their mappings. This makes it easy for future developers to:
- Understand the current category structure
- Add new categories
- Check what features are implemented
- Find the correct database and GUI modules for each category

This is a reference system - it does not change the actual behavior,
just makes it easier to understand and extend.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class CategoryInfo:
    """Information about a single product category."""
    
    # Main identifiers
    display_name: str           # Name shown in UI
    folder_path: Optional[str]  # Folder path (e.g., "oilseals", "packingseals/monoseals")
    parent: Optional[str] = None  # Parent category if nested (e.g., "PACKING SEALS")
    
    # Feature availability
    has_products_module: bool = False   # Has Products tab implementation
    has_transactions_module: bool = False  # Has Transactions tab implementation
    has_product_edit_form: bool = False  # Has add/edit product form
    has_transaction_form: bool = False   # Has add/edit transaction form
    
    # Implementation status
    is_implemented: bool = False        # Is fully functional
    is_coming_soon: bool = False        # Shows "Coming Soon"
    is_placeholder: bool = False        # Reserved for future use
    
    # Unit support
    supports_mm: bool = False
    supports_inch: bool = False
    supports_custom_units: List[str] = None  # e.g., ["VS", "VA", "VL"]
    
    def __post_init__(self):
        if self.supports_custom_units is None:
            self.supports_custom_units = []
    
    def __str__(self) -> str:
        """Human-readable representation."""
        status = "Implemented" if self.is_implemented else "Coming Soon" if self.is_coming_soon else "Placeholder"
        modules = []
        if self.has_products_module:
            modules.append("Products")
        if self.has_transactions_module:
            modules.append("Transactions")
        
        modules_str = f" ({', '.join(modules)})" if modules else " (No modules)"
        return f"{self.display_name}: {status}{modules_str}"

# ============================================================================
# CATEGORY REGISTRY
# 
# This registry documents all categories and their implementation status.
# When adding new categories, update this and CATEGORY_FOLDER_MAP in app_controller.py
# ============================================================================

CATEGORY_REGISTRY: Dict[str, CategoryInfo] = {
    # ========== IMPLEMENTED CATEGORIES ==========
    
    "OIL SEALS": CategoryInfo(
        display_name="OIL SEALS",
        folder_path="oilseals",
        has_products_module=True,
        has_transactions_module=True,
        has_product_edit_form=True,
        has_transaction_form=True,
        is_implemented=True,
        supports_mm=True,
        supports_inch=True,
    ),
    
    "PACKING SEALS": CategoryInfo(
        display_name="PACKING SEALS",
        folder_path="packingseals",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
        # Uses subcategories: monoseals, wiperseals, etc.
    ),
    
    "PACKING SEALS MONOSEALS": CategoryInfo(
        display_name="MONOSEALS",
        folder_path="packingseals/monoseals",
        parent="PACKING SEALS",
        has_products_module=True,
        has_transactions_module=True,
        has_product_edit_form=True,
        has_transaction_form=True,
        is_implemented=True,
        supports_mm=True,
        supports_inch=True,
    ),
    
    "PACKING SEALS WIPER SEALS": CategoryInfo(
        display_name="WIPER SEALS",
        folder_path="packingseals/wiperseals",
        parent="PACKING SEALS",
        has_products_module=True,
        has_transactions_module=True,
        has_product_edit_form=True,
        has_transaction_form=True,
        is_implemented=True,
        supports_mm=True,
        supports_inch=True,
    ),
    
    # ========== FUTURE CATEGORIES ==========
    
    "O-RINGS": CategoryInfo(
        display_name="O-RINGS",
        folder_path="orings",
        has_products_module=False,  # Not yet created
        has_transactions_module=False,
        is_placeholder=True,
        supports_mm=True,
        supports_inch=True,
    ),
    
    "O-CORDS": CategoryInfo(
        display_name="O-CORDS",
        folder_path="ocords",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
    ),
    
    "O-RING KITS": CategoryInfo(
        display_name="O-RING KITS",
        folder_path="oringkits",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
    ),
    
    "QUAD RINGS (AIR SEALS)": CategoryInfo(
        display_name="QUAD RINGS (AIR SEALS)",
        folder_path="quadrings",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
        supports_mm=True,
        supports_inch=True,
    ),
    
    "LOCK RINGS (CIRCLIPS)": CategoryInfo(
        display_name="LOCK RINGS (CIRCLIPS)",
        folder_path="lockrings",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
        supports_mm=True,
        supports_inch=True,
    ),
    
    "V-RINGS": CategoryInfo(
        display_name="V-RINGS",
        folder_path="vrings",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
        supports_custom_units=["VS", "VA", "VL"],
    ),
    
    "PISTON CUPS": CategoryInfo(
        display_name="PISTON CUPS",
        folder_path="pistoncups",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
    ),
    
    "VALVE SEALS": CategoryInfo(
        display_name="VALVE SEALS",
        folder_path="valveseals",
        has_products_module=False,
        has_transactions_module=False,
        is_placeholder=True,
        supports_mm=True,
        supports_inch=True,
    ),
    
    # ========== COMING SOON CATEGORIES ==========
    
    "MECHANICAL SHAFT SEALS": CategoryInfo(
        display_name="MECHANICAL SHAFT SEALS",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "RUBBER DIAPHRAGMS": CategoryInfo(
        display_name="RUBBER DIAPHRAGMS",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "COUPLING INSERTS": CategoryInfo(
        display_name="COUPLING INSERTS",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "IMPELLERS": CategoryInfo(
        display_name="IMPELLERS",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "BALL BEARINGS": CategoryInfo(
        display_name="BALL BEARINGS",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "BUSHINGS (FLAT RINGS)": CategoryInfo(
        display_name="BUSHINGS (FLAT RINGS)",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "GREASE & SEALANTS": CategoryInfo(
        display_name="GREASE & SEALANTS",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "OIL CAPS": CategoryInfo(
        display_name="OIL CAPS",
        folder_path=None,
        is_coming_soon=True,
    ),
    
    "ETC. (SPECIAL)": CategoryInfo(
        display_name="ETC. (SPECIAL)",
        folder_path=None,
        is_coming_soon=True,
    ),
}

# Helper functions for working with the registry

def get_category_info(category_name: str) -> Optional[CategoryInfo]:
    """Get category information by name."""
    return CATEGORY_REGISTRY.get(category_name)

def is_category_implemented(category_name: str) -> bool:
    """Check if a category is fully implemented."""
    info = get_category_info(category_name)
    return info.is_implemented if info else False

def get_implemented_categories() -> List[str]:
    """Get list of all implemented categories."""
    return [name for name, info in CATEGORY_REGISTRY.items() if info.is_implemented]

def get_coming_soon_categories() -> List[str]:
    """Get list of all coming soon categories."""
    return [name for name, info in CATEGORY_REGISTRY.items() if info.is_coming_soon]

def get_placeholder_categories() -> List[str]:
    """Get list of all placeholder categories."""
    return [name for name, info in CATEGORY_REGISTRY.items() if info.is_placeholder]

def get_subcategories(parent_category: str) -> List[str]:
    """Get all subcategories of a parent category."""
    return [
        name for name, info in CATEGORY_REGISTRY.items()
        if info.parent == parent_category
    ]

def category_supports_unit(category_name: str, unit: str) -> bool:
    """Check if a category supports a specific unit system."""
    info = get_category_info(category_name)
    if not info:
        return False
    
    if unit.upper() == "MM":
        return info.supports_mm
    elif unit.upper() == "INCH":
        return info.supports_inch
    else:
        return unit in info.supports_custom_units
