import os
import sqlite3

# Path to this file (database.py)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# The 'data' folder is now a sibling of this file
DATA_DIR = os.path.join(CURRENT_DIR, "data")

# Full path to the MM database (explicit naming for future MM/INCH separation)
DB_PATH = os.path.join(DATA_DIR, "oilseals_mm_inventory.db")

def connect_db():
    return sqlite3.connect(DB_PATH)