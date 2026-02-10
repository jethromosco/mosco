import os
import sqlite3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "wiperseals_mm_inventory.db")

def connect_db():
    return sqlite3.connect(DB_PATH)
