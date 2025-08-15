import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from app_controller import AppController

if __name__ == "__main__":
    root = tk.Tk()
    app = AppController(root)
    root.mainloop()

# 7/8 tsaka yung decimals /

# actual check (green) transactiaction tab + FAB MOS 4 BTNS - sa black yung JO

# 
# inventroy app country - gawin brand /
# 
#  _ taiwan T.Y magkakasama _ NOK = NACTEC
# 
# lipat admin sa loob ng oil seal/
# lipat db sa loob/
# diff db per cat./

# oilsseal per type picture/
# special upload button (no type)/

# C:\My Drive\WAREHOUSE\PRODUCTS-DATA PICTURES\Oil Seals "TYPES"

# now in searches 9/10 should be 0.354/0.394 not 0.035 /

# TODO: Move admin panel inside each category folder (e.g., oilseals/admin)/
# TODO: Move each category's database file inside its own folder (e.g., oilseals/database/oilseals.db)/
# TODO: Create separate folders for each product category (oilseals, bearings, filters, etc.)/
# TODO: Refactor homepage so only homepage.py is in the root; all categories are folders/
# TODO: Update imports after moving files/folders/
# TODO: Implement dynamic homepage that lists all categories and links to their inventory apps/
# TODO: Add image upload and display per product type/category ///
# TODO: Add a special upload button for products with no type/category/
# TODO: Implement exact search for ID, OD, TH, and PART NO. fields ///
# TODO: Improve mm-to-inch converter for thickness fields (e.g., 9/10 → 0.354/0.394) ///
# TODO: Add clear filters button in the UI
# TODO: Add user-friendly error messages and input validation
# TODO: Optimize database queries and consider pagination for large inventories
# TODO: Add README.md and requirements.txt for project documentation and setup
# TODO: Add basic unit tests for utility functions and database operations

#photo upload sa special di siguro gagana bc of /

#back button returning to home page instead of previous category hard fix/

#everything under ng admin di nagrerrefresh sa mm table sa trans window ok naman don lang talaga sa mm/

# ty (taiwan) NQK and NACTEC 

#nung nagenter save sa transaction tab nag exit naguupdate na pero nagcclose/

#5/6.5 invalid literal for fraction -transaction tab/

#isama brand sa special type file name uploads/

#actual green black jo