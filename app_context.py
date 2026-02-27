"""
Centralized Application Context

Single source of truth for:
- Active category/subcategory/unit
- Database connection and paths
- Photo folder paths
- All mutable application state

This eliminates the need for patching modules and ensures consistency across all categories.
"""

from dataclasses import dataclass
from typing import Optional
import sqlite3
import os
from debug import DEBUG_MODE


@dataclass
class AppContext:
    """
    Centralized application state container.
    
    All modules (GUI, Admin, UI) should read from and write to this single instance.
    This eliminates state fragmentation and simplifies debugging.
    """
    
    # Active selection
    active_category: str = ""
    active_subcategory: Optional[str] = None
    active_unit: Optional[str] = None
    
    # Database
    db_connection: Optional[sqlite3.Connection] = None
    db_path: str = ""
    
    # Photos
    photo_folder: str = ""
    
    # UI state
    current_section: Optional[str] = None  # PRODUCTS, TRANSACTIONS, ADMIN
    current_action: Optional[str] = None   # ADD PRODUCT, EDIT PRODUCT, DELETE PRODUCT
    
    def __post_init__(self):
        """Validate state on creation."""
        if DEBUG_MODE:
            self._log_state("AppContext initialized")
    
    def _log_state(self, event: str = "State change"):
        """Log context state for debugging."""
        if DEBUG_MODE:
            cat_display = f"{self.active_category}"
            if self.active_subcategory:
                cat_display += f" | {self.active_subcategory}"
            if self.active_unit:
                cat_display += f" | {self.active_unit}"
            
            print(f"[DEBUG-CONTEXT] {event}")
            print(f"  Category: {cat_display}")
            print(f"  DB: {self.db_path}")
            print(f"  Photos: {self.photo_folder}")
    
    def set_active_category(
        self,
        category: str,
        subcategory: Optional[str] = None,
        unit: Optional[str] = None
    ) -> None:
        """
        Set active category and related paths.
        
        Args:
            category: Category name (e.g., "OIL SEALS")
            subcategory: Optional subcategory (e.g., "MONOSEALS")
            unit: Optional unit (e.g., "MM")
        """
        self.active_category = category
        self.active_subcategory = subcategory
        self.active_unit = unit
        
        if DEBUG_MODE:
            self._log_state(f"Active category set to {category}")
    
    def set_database(self, db_path: str, connection: Optional[sqlite3.Connection] = None) -> None:
        """
        Set database path and optionally create/set connection.
        
        Args:
            db_path: Full path to database file
            connection: Optional pre-created connection (reuses if provided)
        """
        if self.db_connection and self.db_connection != connection:
            try:
                self.db_connection.close()
            except Exception:
                pass
        
        self.db_path = db_path
        
        if connection:
            self.db_connection = connection
        elif db_path:
            try:
                self.db_connection = sqlite3.connect(db_path)
            except Exception as e:
                print(f"[ERROR] Failed to connect to {db_path}: {e}")
                self.db_connection = None
        
        if DEBUG_MODE:
            self._log_state(f"Database set to {db_path}")
    
    def set_photo_folder(self, folder_path: str) -> None:
        """
        Set photo folder path.
        
        Args:
            folder_path: Full path to photos directory
        """
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception as e:
                print(f"[ERROR] Failed to create photo folder {folder_path}: {e}")
        
        self.photo_folder = folder_path
        
        if DEBUG_MODE:
            self._log_state(f"Photo folder set to {folder_path}")
    
    def set_ui_state(self, section: Optional[str] = None, action: Optional[str] = None) -> None:
        """
        Set UI section and current action.
        
        Args:
            section: Section name (PRODUCTS, TRANSACTIONS, ADMIN, etc.)
            action: Action name (ADD PRODUCT, EDIT PRODUCT, etc.)
        """
        self.current_section = section
        self.current_action = action
        
        if DEBUG_MODE:
            state_str = section or ""
            if action:
                state_str += f" | {action}"
            print(f"[DEBUG-CONTEXT] UI state: {state_str}")
    
    def close_database(self) -> None:
        """Close database connection safely."""
        if self.db_connection:
            try:
                self.db_connection.close()
                self.db_connection = None
                if DEBUG_MODE:
                    print("[DEBUG-CONTEXT] Database connection closed")
            except Exception as e:
                print(f"[ERROR] Error closing database: {e}")
    
    def __str__(self) -> str:
        """Human-readable representation."""
        cat_str = self.active_category
        if self.active_subcategory:
            cat_str += f" | {self.active_subcategory}"
        if self.active_unit:
            cat_str += f" | {self.active_unit}"
        
        return f"AppContext({cat_str}, db={os.path.basename(self.db_path)}, photos={os.path.basename(self.photo_folder)})"


# Global instance - initialized at application startup
global_app_context: Optional[AppContext] = None


def initialize_app_context() -> AppContext:
    """Initialize and return the global AppContext instance."""
    global global_app_context
    if global_app_context is None:
        global_app_context = AppContext()
        if DEBUG_MODE:
            print("[DEBUG-CONTEXT] Global AppContext initialized")
    return global_app_context


def get_app_context() -> AppContext:
    """Get the global AppContext instance."""
    global global_app_context
    if global_app_context is None:
        global_app_context = initialize_app_context()
    return global_app_context
