"""
Safe Category Operations

Helper functions for safely switching categories, managing GUI state,
and handling transitions between different inventory modules.

These functions are designed to be safe to use and can help prevent 
bugs during category switching without affecting current functionality.
"""

from typing import Optional, Callable
from app_controller import CATEGORY_FOLDER_MAP
from category_registry import get_category_info, is_category_implemented

class SafeCategorySwitch:
    """
    Context manager for safe category switching.
    
    Usage:
        with SafeCategorySwitch(controller, new_category) as switch:
            if switch.is_valid():
                # Proceed with switch
                switch.apply()
            else:
                switch.show_error()
    """
    
    def __init__(self, controller, category: str, subcategory: Optional[str] = None, unit: Optional[str] = None):
        self.controller = controller
        self.category = category
        self.subcategory = subcategory
        self.unit = unit
        
        self._is_valid = False
        self._error_message = ""
        self._validate()
    
    def _validate(self):
        """Validate that category can be switched to."""
        # Check category exists
        if not self.category or self.category not in CATEGORY_FOLDER_MAP:
            self._error_message = f"Category not found: {self.category}"
            return
        
        # Check category has implementation
        if not CATEGORY_FOLDER_MAP.get(self.category):
            self._error_message = f"Category not yet available: {self.category}"
            return
        
        # Check category info
        info = get_category_info(self.category)
        if not info:
            self._error_message = f"No category info available: {self.category}"
            return
        
        if info.is_coming_soon:
            self._error_message = f"Category coming soon: {self.category}"
            return
        
        self._is_valid = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def is_valid(self) -> bool:
        """True if category switch is safe to perform."""
        return self._is_valid
    
    def get_error_message(self) -> str:
        """Get error message if validation failed."""
        return self._error_message
    
    def apply(self) -> bool:
        """
        Apply the category switch.
        
        Returns:
            True if successful, False if failed
        """
        if not self.is_valid():
            return False
        
        try:
            if self.controller:
                self.controller.set_inventory_context(
                    self.category,
                    self.subcategory,
                    self.unit
                )
            return True
        except Exception as e:
            self._error_message = f"Failed to apply switch: {str(e)}"
            return False


def validate_category_switch(
    from_category: Optional[str],
    to_category: str,
    subcategory: Optional[str] = None
) -> tuple[bool, str]:
    """
    Validate that switching from one category to another is safe.
    
    Args:
        from_category: Current category (can be None)
        to_category: Desired new category
        subcategory: Optional subcategory
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check to_category exists
    if not to_category or to_category not in CATEGORY_FOLDER_MAP:
        return False, f"Category not found: {to_category}"
    
    # Check it has a folder mapping
    folder = CATEGORY_FOLDER_MAP.get(to_category)
    if not folder:
        return False, f"Category has no implementation: {to_category}"
    
    # Check via registry
    info = get_category_info(to_category)
    if not info:
        return False, f"Category not in registry: {to_category}"
    
    if info.is_coming_soon:
        return False, f"Category is coming soon: {to_category}"
    
    return True, ""

def reset_category_state(controller) -> bool:
    """
    Reset category state to defaults.
    Useful after error recovery.
    
    Returns:
        True if reset successful
    """
    try:
        if controller:
            controller.current_category = None
            controller.current_subcategory = None
            controller.current_unit = None
            # Don't clear context - let it be set by set_inventory_context
        return True
    except Exception:
        return False

def get_valid_categories() -> list[str]:
    """
    Get list of all categories that have implementations.
    
    Returns:
        List of category names with folder mappings
    """
    valid = []
    for name, folder in CATEGORY_FOLDER_MAP.items():
        if folder is not None:  # Only include categories with implementations
            valid.append(name)
    return sorted(valid)

def get_category_folder(category: str) -> Optional[str]:
    """
    Safely get the folder path for a category.
    
    Args:
        category: Category name
    
    Returns:
        Folder path (e.g., "oilseals", "packingseals/monoseals") or None
    """
    return CATEGORY_FOLDER_MAP.get(category)

def resolve_category_module_path(category: str, subcategory: Optional[str] = None) -> Optional[str]:
    """
    Resolve the Python module path for a category.
    
    Args:
        category: Main category name
        subcategory: Optional subcategory
    
    Returns:
        Module path (e.g., "packingseals.monoseals") or None
    """
    # Try compound key first if subcategory provided
    if subcategory:
        compound_key = f"{category} {subcategory}"
        if compound_key in CATEGORY_FOLDER_MAP:
            folder = CATEGORY_FOLDER_MAP.get(compound_key)
            if folder:
                return folder.replace("/", ".")
    
    # Try base category
    folder = CATEGORY_FOLDER_MAP.get(category)
    if folder:
        return folder.replace("/", ".")
    
    return None
