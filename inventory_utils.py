"""
Inventory Utilities

Safe helper functions for:
- Category validation
- Module path resolution
- Optional debug logging (can be enabled/disabled without breaking anything)
- Error reporting

These utilities improve maintainability and debugging without changing
existing functionality.
"""

import sys
import os
from typing import Optional, Dict, Tuple

# Optional logging support - can be toggled without breaking the app
ENABLE_DEBUG_LOGGING = False

def enable_debug_logging(enabled: bool = True) -> None:
    """Enable or disable debug logging. Safe to call anytime."""
    global ENABLE_DEBUG_LOGGING
    ENABLE_DEBUG_LOGGING = enabled

def debug_log(message: str, module: str = "") -> None:
    """
    Log debug messages if enabled.
    
    Safe to call - does nothing if logging is disabled.
    Does not affect any app functionality.
    """
    if not ENABLE_DEBUG_LOGGING:
        return
    
    prefix = f"[{module}] " if module else "[DEBUG] "
    print(f"{prefix}{message}")

def log_error(message: str, exception: Optional[Exception] = None, module: str = "") -> None:
    """
    Log error messages for debugging.
    
    Safe to call - only prints, doesn't affect app state.
    """
    prefix = f"[{module}] " if module else "[ERROR] "
    print(f"{prefix}{message}", file=sys.stderr)
    if exception and ENABLE_DEBUG_LOGGING:
        print(f"  Exception: {type(exception).__name__}: {exception}", file=sys.stderr)

def validate_category_exists(category_name: str, category_map: Dict) -> bool:
    """
    Check if a category exists in the category map.
    
    Args:
        category_name: Category name to check
        category_map: Dictionary of categories (e.g., CATEGORY_FOLDER_MAP)
    
    Returns:
        True if category exists in map
    """
    if not category_name or not isinstance(category_name, str):
        return False
    return category_name in category_map

def validate_category_has_implementation(category_name: str, category_map: Dict) -> bool:
    """
    Check if a category exists AND has a folder mapping (not None).
    
    Args:
        category_name: Category name to check
        category_map: Dictionary of categories mapped to folder paths
    
    Returns:
        True if category exists and has a non-None folder mapping
    """
    if not validate_category_exists(category_name, category_map):
        return False
    return category_map.get(category_name) is not None

def resolve_module_path(
    category: str,
    subcategory: Optional[str] = None,
    category_map: Optional[Dict] = None
) -> Optional[str]:
    """
    Resolve the Python module path for a category/subcategory.
    
    This implements the logic for finding the correct module without
    duplicating it across multiple files.
    
    Args:
        category: Main category name
        subcategory: Optional subcategory name
        category_map: CATEGORY_FOLDER_MAP to use (if None, must be passed externally)
    
    Returns:
        Module path (e.g., "packingseals.monoseals") or None if not found
    """
    if not category_map:
        return None
    
    # Try direct mapping if both category and subcategory are provided
    if subcategory:
        # Check for explicit compound mapping (e.g., "PACKING SEALS MONOSEALS")
        compound_key = f"{category} {subcategory}"
        if compound_key in category_map:
            base_folder = category_map.get(compound_key)
            if base_folder:
                return base_folder.replace("/", ".")
    
    # Try base category mapping
    base_folder = category_map.get(category)
    if base_folder:
        return base_folder.replace("/", ".")
    
    return None

def get_category_display_name(category: str, subcategory: Optional[str] = None) -> str:
    """
    Get human-readable category name for display/logging.
    
    Args:
        category: Main category
        subcategory: Optional subcategory
    
    Returns:
        Formatted display name
    """
    if subcategory and subcategory != "-":
        return f"{category} - {subcategory}"
    return category

def safe_get_attribute(obj, attr_name: str, default=None):
    """
    Safe attribute access that won't crash if attribute doesn't exist.
    
    Args:
        obj: Object to get attribute from
        attr_name: Name of attribute
        default: Default value if attribute missing
    
    Returns:
        Attribute value or default
    """
    try:
        return getattr(obj, attr_name, default)
    except Exception:
        return default

def validate_context_state(context) -> Tuple[bool, str]:
    """
    Validate that a context object has required attributes.
    
    Args:
        context: InventoryContext object to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_attrs = ['category', 'products_available', 'transactions_available', 'coming_soon']
    missing = []
    
    for attr in required_attrs:
        if not hasattr(context, attr):
            missing.append(attr)
    
    if missing:
        return False, f"Context missing attributes: {', '.join(missing)}"
    
    if not hasattr(context, 'is_valid') or not callable(context.is_valid):
        return False, "Context missing is_valid() method"
    
    return True, ""

def safe_import_module(module_path: str):
    """
    Safely import a module without crashing the app if import fails.
    
    Args:
        module_path: Python module path (e.g., "packingseals.monoseals.database")
    
    Returns:
        Module object or None if import failed
    """
    try:
        import importlib
        module = importlib.import_module(module_path)
        debug_log(f"Successfully imported {module_path}", "safe_import_module")
        return module
    except ImportError as e:
        log_error(f"Failed to import {module_path}: {e}", e, "safe_import_module")
        return None
    except Exception as e:
        log_error(f"Unexpected error importing {module_path}: {e}", e, "safe_import_module")
        return None
