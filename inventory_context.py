"""
Inventory Context Management

Single source of truth for the current inventory selection (category/subcategory/unit).
This object encapsulates what's available, what's Coming Soon, and what can be accessed.

This is the **authoritative state** for deciding:
- Which tabs should exist
- Which tabs should be enabled
- Whether to show Coming Soon
- Which database to connect to
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InventoryContext:
    """Represents the current inventory selection and what's available for it.
    
    This is the single source of truth that controls:
    - What GUI elements are visible
    - What operations are allowed
    - Whether Coming Soon should be shown
    
    Attributes:
        category: The selected category (e.g., "OIL SEALS")
        subcategory: Optional subcategory (e.g., "MONOSEALS")
        unit: Selected unit system (e.g., "MM" or "INCH")
        
        products_available: bool - Products tab can be shown and used
        transactions_available: bool - Transactions tab can be shown and used
        coming_soon: bool - Show Coming Soon overlay instead of tables
        
        reason: str - Human-readable explanation (for logging/debugging)
        module_path: str - Path to the InventoryApp class (if available)
        error: str - Error message if loading failed
    """
    
    category: str
    subcategory: Optional[str] = None
    unit: Optional[str] = None
    
    # Availability flags (these control what the GUI shows)
    products_available: bool = False
    transactions_available: bool = False
    coming_soon: bool = False
    
    # Debug/logging information
    reason: str = ""
    module_path: str = ""
    error: str = ""
    
    def __str__(self) -> str:
        """Human-readable representation for logging."""
        parts = [self.category]
        if self.subcategory:
            parts.append(self.subcategory)
        if self.unit:
            parts.append(self.unit)
        context_str = " ".join(parts)
        
        if self.coming_soon:
            return f"{context_str} (COMING SOON: {self.reason})"
        elif self.products_available and self.transactions_available:
            return f"{context_str} (FULLY AVAILABLE)"
        elif self.products_available:
            return f"{context_str} (PRODUCTS ONLY)"
        elif self.transactions_available:
            return f"{context_str} (TRANSACTIONS ONLY)"
        else:
            return f"{context_str} (NO TABS AVAILABLE)"
    
    def is_valid(self) -> bool:
        """Returns True if at least one tab can be shown."""
        return self.products_available or self.transactions_available or self.coming_soon
    
    def can_show_products(self) -> bool:
        """Returns True if Products tab should be shown and enabled."""
        return self.products_available and not self.coming_soon
    
    def can_show_transactions(self) -> bool:
        """Returns True if Transactions tab should be shown and enabled."""
        return self.transactions_available and not self.coming_soon
    
    def should_show_coming_soon(self) -> bool:
        """Returns True if Coming Soon overlay should be shown."""
        return self.coming_soon


# Sentinel for invalid context (when nothing can be loaded)
INVALID_CONTEXT = InventoryContext(
    category="INVALID",
    coming_soon=True,
    reason="No inventory selected"
)


def create_context(
    category: str,
    subcategory: Optional[str] = None,
    unit: Optional[str] = None,
    products_available: bool = False,
    transactions_available: bool = False,
    coming_soon: bool = False,
    reason: str = "",
    module_path: str = "",
    error: str = ""
) -> InventoryContext:
    """Factory function to create a context with validation."""
    
    return InventoryContext(
        category=category,
        subcategory=subcategory,
        unit=unit,
        products_available=products_available,
        transactions_available=transactions_available,
        coming_soon=coming_soon,
        reason=reason,
        module_path=module_path,
        error=error
    )
