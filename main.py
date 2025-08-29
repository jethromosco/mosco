import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from app_controller import AppController
from theme import theme

if __name__ == "__main__":
    # Initialize theme (default dark) and CTk appearance
    theme.set_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("MOSCO Inventory System")
    app = AppController(root)
    root.mainloop()

# 7/8 tsaka yung decimals /
# actual check (green) transactiaction tab + FAB MOS 4 BTNS - sa black yung JO /
# inventroy app country - gawin brand /
# lipat admin sa loob ng oil seal/
# lipat db sa loob/
# diff db per cat./
# oilsseal per type picture/
# special upload button (no type)/
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

#photo upload sa special di siguro gagana bc of /
#back button returning to home page instead of previous category hard fix/
#everything under ng admin di nagrerrefresh sa mm table sa trans window ok naman don lang talaga sa mm/
#nung nagenter save sa transaction tab nag exit naguupdate na pero nagcclose/
#5/6.5 invalid literal for fraction -transaction tab/
#isama brand sa special type file name uploads/
#SPECIAL (VC) lagyan ng ganyan pero dapat readable as special pa din siya /
# or pede gawin pag MOS automatic na special type siya/

# JO di mapagsama sa isang line ang "finabricate" at "nabenta" due to formulas present /
# ginawang magkahiwalay = fab (blue) and sold (red) INVOICE NUM SA KALAS /
# quad tabi ng v-ring /
# bushing palit bearings / 

# ok na yung recent ilagay na lang sa read me /

# di functional na maayos nasira after gui /
# paghiwalayin ui sa functions para mas madali magedit /


# NOK - NOK NACTEC /
# TY - lahat ng taiwan brands /
# C:\My Drive\WAREHOUSE\PRODUCTS-DATA PICTURES\Oil Seals "TYPES"

# TRANS AED BIG PROBLEM !!! /
# gawin din consistent yung cards styles pati table size and margins UI /
# dapat seamless parang sa admin /
# LAKIHAN TEXT SA UI /

# back button sa subcategories di maayos kasi bumabalik sa home page /
# LIGHT MODE SA LAHAT kahit sa home na lang yung button for switching modes /

# stock threshold not working

# TODO: Add README.md and requirements.txt for project documentation and setup