import sqlite3

DB_PATH = "data/inventory.db"

def connect_db():
    return sqlite3.connect(DB_PATH)
