import os
import sqlite3
from app_context import get_app_context
from debug import DEBUG_MODE

# Path to this file (database.py)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# The 'data' folder is now a sibling of this file
DATA_DIR = os.path.join(CURRENT_DIR, "data")

# Full path to the MM database (explicit naming for future MM/INCH separation)
DB_PATH = os.path.join(DATA_DIR, "monoseals_mm_inventory.db")


class _AppContextConnectionWrapper:
    """Wrapper that prevents closing AppContext's connection."""
    def __init__(self, conn, is_app_context=False):
        self.conn = conn
        self.is_app_context = is_app_context
    
    def __getattr__(self, name):
        return getattr(self.conn, name)
    
    def close(self):
        """Only close if not an AppContext connection."""
        if not self.is_app_context and self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self.conn
    
    def __exit__(self, *args):
        self.close()


def connect_db():
    """
    Get database connection using AppContext.
    
    This reads from AppContext to ensure the correct database is used
    when categories are switched, fixing the product validation bug.
    
    The connection is wrapped to prevent closing if it's from AppContext.
    
    Returns:
        sqlite3.Connection to the active database
    """
    try:
        context = get_app_context()
        if context.db_connection:
            # Wrap AppContext connection to prevent closing
            return _AppContextConnectionWrapper(context.db_connection, is_app_context=True)
    except Exception as e:
        if DEBUG_MODE:
            print(f"[DEBUG-DB] AppContext unavailable: {e}. Creating new connection")
    
    # Create new connection if AppContext unavailable
    conn = sqlite3.connect(DB_PATH)
    return _AppContextConnectionWrapper(conn, is_app_context=False)