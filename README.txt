MOSCO INVENTORY SYSTEM - USER MANUAL
================================================================

Welcome to the MOSCO Inventory Application. This guide will help you use the system to manage stock, view products, and handle transactions.

This file is divided into two parts:
1. USER GUIDE (For daily use)
2. ADMIN GUIDE (For managers and stock controllers)


================================================================
PART 1: USER GUIDE
================================================================

1. GETTING STARTED
------------------
- To open the app, double-click the application icon or run the main script.
- The app will start in a maximized window.

2. THE HOME SCREEN
------------------
- You will see a grid of buttons representing different categories (like OIL SEALS, O-RINGS, etc.).
- Click on any category button to open it.
- Some categories have sub-categories (e.g., clicking O-RINGS might ask for material type).
- To go back, click the "Back" button at the top left corner.

2A. WINDOW TITLE NAVIGATION (Know Where You Are)
--------------------------------------------------
The window title at the very top shows exactly which part of the system you are in.

Examples of what you might see:
- "MOS Inventory - HOMEPAGE" = At the main screen
- "MOS Inventory - OIL SEALS" = Inside Oil Seals category
- "MOS Inventory - PACKING SEALS | MONOSEALS | MM" = In Monoseals → MM subcategory
- "MOS Inventory - PACKING SEALS | MONOSEALS | MM | PRODUCTS" = Viewing product list
- "MOS Inventory - PACKING SEALS | MONOSEALS | MM | TRANSACTIONS" = Viewing transaction history
- "MOS Inventory - PACKING SEALS | MONOSEALS | MM | ADMIN" = In Admin panel for that module

This helps you know exactly which category and module you are working with at all times.

3. FINDING PRODUCTS (SEARCH)
----------------------------
- Once inside a category list, you will see search boxes at the top.
- You can type in:
  * TYPE (e.g., TC, SC)
  * ID (Inner Diameter)
  * OD (Outer Diameter)
  * TH (Thickness)
  * BRAND
  * PART NO.
- The list updates automatically as you type. You do not need to press Enter.
- To clear all filters and see everything again, press the "Esc" key on your keyboard.

4. VIEWING PRODUCT DETAILS
--------------------------
- The main list shows products with their size, brand, and current stock.
- Double-click on any row in the list to open the "Product Details" window.
- This window shows:
  * Big Stock Number (Green/Red/Orange)
  * Price (SRP)
  * Location
  * Notes
  * Transaction History (a list of all sales and restocks)

5. EDITING INFO (LOCATION, NOTES, PRICE)
----------------------------------------
- In the Product Details window, there is an "Edit" button on the right side.
- Click "Edit" to unlock the fields.
- You can change:
  * Location (Where the item is kept)
  * Notes (Any remarks)
  * Price (SRP)
- Click "Save" when you are done.

IMPROVEMENT: After you edit and save, the changes take effect immediately. A transaction window will
automatically open to confirm your update. You do not need to exit the admin panel or restart anything
to see the changes reflected in the product list.

6. STOCK ALERTS & COLORS
------------------------
- The stock number changes color to warn you:
  * Green: Good stock level
  * Orange: Low stock
  * Red: Out of stock or critical
- To change when these colors appear:
  1. Click directly on the big "STOCK: XX" text.
  2. A small window will pop up.
  3. Enter the number for "Restock Needed" (Red) and "Low on Stock" (Orange).
  4. Click Save.

7. PHOTOS
------------------------
- If a product has a photo, you will see it on the right side of the details window.
- Click the photo to view it in full screen.
- If the product is "MOS" brand and has no photo, clicking the camera icon allows you to upload one.

8. LIGHT MODE & DARK MODE
-------------------------
- Look for the Sun/Moon button in the top right corner.
- Click it to switch between a light theme (white/grey) and a dark theme (black/grey).
- This setting is saved while the app is running.

9. KEYBOARD SHORTCUTS
---------------------
- F11: Toggle Fullscreen mode (removes window borders).
- Esc: Clear search filters or Close pop-up windows.
- Ctrl + 2: Open the Admin Panel (requires password).
- Tab: Move to the next box or button.
- Shift + Tab: Move to the previous box or button.
- Enter: Confirm action or Save.
- Arrow Keys: Move selection in lists.

10. RIGHT-CLICK COPY FUNCTIONS
------------------------------
The system supports **right-click copying** to make quoting and sharing prices faster.

You can right-click in the following places:
- Product list rows
- Product cards
- SRP price in the product details window
- Transaction history rows (Sale, Restock, Actual)

When you right-click, the item is copied to your clipboard in this format:

Product Name  
Price per piece  

Example:
TC 30-47-7 NOK Oil Seal  
₱250- / pc.

Two blank lines are automatically added after the price so you can paste many items without pressing Shift+Enter every time.

---

SPECIAL COPY RULES (Applied Across All Modules):

These rules work consistently across all product types:
- Oil Seals
- Monoseals
- Wiper Seals
- Wipermono

Automatic formatting:
• Country names (Japan, Korea, China, etc.) are automatically removed when copying.
• If the product starts with "SPL", the "SPL" word is removed when copied.
• Brand extraction: The brand is automatically taken from the product information.
• Spacing: Two blank lines are added between items for easy pasting into quotes.
• All formatting is consistent across all modules.

---

TRANSACTION COLOR RULES (IMPORTANT):

• RED (Sale):
  - Copies the actual sale price used in that transaction.

• GREEN (Actual Checking):
  - Copies the recorded price normally.

• BLUE (Restock):
  - Price amount is removed.
  - Only the peso sign (₱) is copied.
  - The brand is taken from the restock name input.

Example (Restock):
TC 30-47-7 NQK Oil Seal  
₱

If the restock name starts with "(" and has no brand:
TC 30-47-7 (?) Oil Seal  
₱

---

11. SIMPLE TIPS FOR DAILY USE
-------------------
- If you can't find an item, try typing less. For example, instead of "10.5", try just "10".
- Use right-click copy when quoting prices to customers.
- Pasted items already have spacing between them.
- Use the "Back" button to navigate, do not close the window unless you want to exit the app.
- Always double-check brand spelling before saving new products.
- Always confirm that you are in the correct category before editing.
- Keep consistent naming when adding new products (e.g., use "MOS" always, not "M.O.S.").
- Back up your database files regularly (copy the .db files to a safe location).
- Use the window title to verify you are in the right module before making changes.

================================================================
PART 2: ADMIN GUIDE
================================================================

This section is for users with Admin access only.

1. ENTERING ADMIN MODE
----------------------
- Click the "Admin" button at the top right of the screen (or press Ctrl + 2).
- Enter the admin password "1".
- If correct, the Admin Panel window will open.

2. THE ADMIN PANEL
------------------
- The Admin Panel has two main tabs at the top:
  * Products: For adding/editing items.
  * Transactions: For adding sales, restocks, or adjustments.
- Below the tabs, there is a selector bar. Use this to switch between different inventories (e.g., Oil Seals -> MM).

2A. CATEGORY DROPDOWN STABILITY
-------------------------------
The category dropdown in the Admin Panel now works reliably and consistently:

✓ Switching between Oil Seals, Monoseals, Wiper Seals, and Wipermono updates both the GUI and Admin tables correctly.
✓ The Products tab updates when you switch categories.
✓ The Transactions tab updates when you switch categories.
✓ No longer need to restart the Admin window after switching categories.
✓ All data displayed is accurate for the selected category.

How to use: Simply click the category dropdown and select the module you want to work with.
The window will update immediately with the correct products and transactions for that category.

3. ADDING NEW PRODUCTS
----------------------
1. Go to the "Products" tab.
2. Click the green "Add" button.
3. Fill in the details:
   * Type, ID, OD, Thickness
   * Brand, Name
   * Initial Stock and Price
4. Click Save.
5. The new product will appear in the list immediately.

4. EDITING OR DELETING PRODUCTS
-------------------------------
- To Edit: Select a product in the list and click "Edit". Change values and Save.
- To Delete: Select a product and click "Delete". Confirm the warning.
  * WARNING: Deleting a product removes it permanently.

5. MANAGING TRANSACTIONS (STOCK IN/OUT)
---------------------------------------
To record a sale or restock:
1. Go to the "Transactions" tab in the Admin Panel.
2. Click "Add".
3. Select the Transaction Type (press Ctrl+Tab to cycle):
   * Sale: Reduces stock (Red button).
   * Restock: Adds stock (Blue button).
   * Actual: Sets the stock to an exact number (Green button).
   * Fabrication: Special mode for made-to-order items.
4. Fill in the Date, Product details, and Quantity.
5. Click Save.

6. FABRICATION TRANSACTIONS
---------------------------
- Fabrication is special because it involves two steps:
  1. Taking raw materials (Stock Out).
  2. Creating the finished product (Stock In).
- When you select "Fabrication", the form will ask for "Qty Restock" (total items made) and "Qty Sold" (total items sold).
- This keeps your inventory balanced.

IMPROVEMENT - Editing Fabrication Transactions:
Before: Editing a fabrication transaction sometimes created duplicate records.
Now: Editing a fabrication transaction properly replaces the original record.

You can safely edit fabrication and convert it to:
  • Sale (Red transaction)
  • Restock (Blue transaction)
  • Actual Checking (Green transaction)

This makes fabrication transactions fully editable and reliable. No more duplicates when making corrections.

7. ADMIN KEYBOARD SHORTCUTS
---------------------------
- Ctrl + Tab: Switch between "Products" and "Transactions" tabs.
- Ctrl + Shift + Tab: Switch tabs in reverse.
- Ctrl + 1: Add a new Transaction (only in Transactions tab).
- Ctrl + 2: Add a new Product (only in Products tab).
- Delete: Delete the selected Transaction (only in Transactions tab).
- Ctrl + Tab (Inside Transaction Form): Change Transaction Type (Sale -> Restock -> Actual -> Fabrication).

8. BRAND NORMALIZATION (AUTOMATIC CORRECTIONS)
----------------------------------------------
The system automatically corrects common brand spelling inconsistencies to keep your database clean:

Automatic Brand Corrections:
  NAK → T.Y.         (Corrects common misspelling)
  NQK → T.Y.         (Corrects common misspelling)
  NTC → NOK          (Corrects common misspelling)

Automatic Country Fill-in:
  If a product's country of origin is missing, the system will auto-fill it based on the brand.
  This keeps naming consistent across the entire database.

Why This Matters:
  Consistent brand names make searching easier and prevent duplicate product entries.
  The system automatically applies these rules when you add or edit a product.
  You do not need to do anything special — the corrections happen automatically.


9. IMPORTANT ADMIN NOTES
------------------------
- Data is saved automatically to the database file.
- Do not rename or move the database files manually while the app is running.
- When adding a product, make sure the "Type" and "Brand" are consistent (e.g., don't use "MOS" one time and "M.O.S." another time).
  The system will auto-correct some common brand name variations (see "Brand Normalization" section above).
- If you change a product's size (ID/OD) in Edit mode, it updates that specific product record. It does not change past transaction history text, but the link remains valid.


10. ADMIN CONSISTENCY IMPROVEMENTS
----------------------------------
The admin panel behavior is now consistent across all modules:

✓ Category switching works the same way in Oil Seals as in Packing Seals modules.
✓ Transaction window behavior is unified across Monoseals, Wiper Seals, and Wipermono.
✓ Product editing logic uses the same rules in all modules.
✓ Right-click copy formatting is consistent across all product categories.
✓ Brand normalization applies uniformly to all brands in all modules.

This makes administration faster and more predictable.

================================================================
FINAL REMINDERS
================================================================

Daily Best Practices:
- Always check the "Stock Filter" if you think items are missing. You might be viewing only "Out of Stock" items.
- Remember to back up your database files regularly (copy the .db files to a safe place).
- If the app looks strange or buttons are missing, try resizing the window or pressing F11.
- Double-check your entries before saving, especially for Prices and Stock adjustments.
- Contact the system developer if you see "Database Error" messages.

MULTI-PC DATABASE SAFETY (IMPORTANT):
- If you are using Google Drive or cloud storage to share the database across multiple PCs:
  * Upload from ONE PC at a time.
  * Avoid simultaneous uploads from different computers.
  * This prevents the database from being overwritten with conflicting changes.
  * Wait for one person to finish and save before another person uploads.
  * Daily backups are recommended (keep a backup copy of the .db file in a separate location).

Database Integrity:
- Never open the database file with external tools (like SQLite Browser) while the app is running.
- Always use the MOSCO app to make changes to keep data consistent.
- If the database becomes corrupted, restore from your backup.

================================================================
COMMON USER MISTAKES & HOW TO AVOID THEM
================================================================

1. WRONG BRAND SPELLING
Problem: Product branded as "MOS" one time, then "M.O.S." another time creates two separate entries.
Solution: 
  - Always check the brand spelling before saving.
  - Use the same spelling every time (e.g., always "MOS", never "M.O.S.").
  - The system helps with auto-correction for some brands, but consistency is best.

2. EDITING THE WRONG PRODUCT
Problem: Accidentally editing a similar product and losing correct data.
Solution:
  - Always verify the product size and brand BEFORE clicking Edit.
  - Read the product header carefully (Type, ID, OD, Thickness, Brand).
  - Double-check the gray text at the top of the edit window.

3. WRONG TRANSACTION TYPE
Problem: Recording a sales as a restock, or a restock as a sale.
Solution:
  - Understand the three transaction types BEFORE recording:
    * SALE (Red): Stock goes OUT. Stock number decreases.
    * RESTOCK (Blue): Stock goes IN. Stock number increases.
    * ACTUAL (Green): Manually set the exact stock count.
  - Confirm the transaction type by looking at the button color.
  - If you make a mistake, you can edit the transaction to fix it.

4. INCORRECT QUANTITY
Problem: Entering wrong quantity for sale or restock, causing stock mismatch.
Solution:
  - Always double-check the number before clicking Save.
  - If you made an error, go back to that transaction and edit it.
  - Check the running balance to catch mistakes quickly.

5. FORGETTING TO SELECT CORRECT CATEGORY
Problem: Adding products to the wrong product type (e.g., Oil Seals instead of Monoseals).
Solution:
  - Always look at the window title to confirm which category you are in.
  - Window title shows: "MOS Inventory - CATEGORY NAME"
  - Switch category BEFORE adding or editing products.

6. INCONSISTENT LOCATION NAMING
Problem: Storing item info as "Shelf A", "Shelf A2", "Shelf-A", making search confusing.
Solution:
  - Decide on a naming standard for all locations (e.g., "Shelf A", "Room B", "Cabinet 1").
  - Write it down and follow it always.
  - Train all staff to use the same system.

================================================================
QUICK TROUBLESHOOTING GUIDE
================================================================

PROBLEM: App won't open / Shows "Python Error"
SOLUTION:
  1. Check that Python 3.9+ is installed on your computer.
  2. Open Command Prompt and type: python --version
  3. If Python is not found, install it from python.org
  4. Ensure you have these libraries installed (see Setup Guide section below).

PROBLEM: Missing Products in the list
SOLUTION:
  1. Check the "Stock Filter" dropdown at the top.
  2. If set to "Out of Stock" or "Low Stock", you may not see everything.
  3. Change filter to "All" to see all products.
  4. Try pressing Esc to clear all search filters.
  5. Type less in search boxes if nothing appears (e.g., search "10" instead of "10.5").

PROBLEM: Stock Numbers Don't Match My Records
SOLUTION:
  1. Go to the product details window.
  2. Check the "Transaction History" tab to see all sales and restocks.
  3. Add up all transactions to verify the final stock number is correct.
  4. If you find an error, edit that specific transaction to fix it.
  5. The stock will recalculate automatically.

PROBLEM: App looks strange / Buttons missing / Text cut off
SOLUTION:
  1. Try resizing the window to see if elements appear.
  2. Press F11 to exit fullscreen mode, then try again.
  3. Restart the app.
  4. If it still looks wrong, the screen resolution might be too low.

PROBLEM: Can't save a product or transaction
SOLUTION:
  1. Check that all required fields are filled in (marked with *).
  2. Make sure numbers only contain digits (no extra spaces or letters).
  3. Check that prices are entered correctly (use periods for decimals: 10.50 not 10,50).
  4. Click Save again.
  5. If still failing, contact the system administrator.

PROBLEM: Database Error when opening the app
SOLUTION:
  1. This usually means the database file is corrupted or locked.
  2. Check that nobody else has the app open on another PC.
  3. Restore from your latest backup copy of the .db file.
  4. If no backup exists, contact the system administrator.

================================================================
PERFORMANCE TIPS & BEST PRACTICES
================================================================

1. AVOID MULTIPLE ADMIN WINDOWS
  - Do not open the Admin Panel twice on the same PC.
  - Do not open Admin from one PC while another PC is using the database.
  - Close the Admin window when finished to free up system resources.

2. CLOSE UNUSED WINDOWS
  - Only keep the window you need open.
  - Close product details windows when done viewing.
  - Close admin panel when not in use.
  - Multiple open windows slow down the system.

3. DON'T EDIT DATABASE MANUALLY
  - Never open .db files with external tools (like SQLite).
  - Never edit data files in Google Drive or cloud storage directly.
  - Only use the MOSCO app to make changes.
  - External edits can corrupt the database.

4. KEEP SEARCH FILTERS CLEAR
  - Remember to press Esc after searching to clear all filters.
  - Clearing filters helps you see all products.
  - This prevents confusion of missing items.

5. BACKUP REGULARLY
  - Copy the .db files to a backup location once a day.
  - Better: Use dedicated backup software or cloud backup (not the same as working copy).
  - Test your backup by opening it to make sure it works.

================================================================
INSTALLER & SETUP GUIDE
================================================================

IMPORTANT: No requirements.txt file is included. You must install libraries manually.

STEP 1: INSTALL PYTHON
  - Go to python.org
  - Download Python 3.9 or newer (NOT Python 2)
  - Run the installer
  - IMPORTANT: Check the box that says "Add Python to PATH"
  - Finish installation

STEP 2: INSTALL REQUIRED LIBRARIES
  Open Command Prompt (on Windows: Win+R, type "cmd", press Enter)
  
  Copy and paste these commands one by one:
    pip install customtkinter
    pip install pillow
    pip install tkcalendar
  
  Wait for each one to finish before running the next.

STEP 3: DOWNLOAD AND EXTRACT THE APP
  - Download the MOSCO Inventory APP folder
  - Extract it to a location (e.g., C:\My Drive\MOS INVENTORY APP\mosco)
  - Do NOT rename the main "mosco" folder

STEP 4: RUN THE APP
  Option A (Easiest): Double-click MOSCO.bat file
  Option B (Manual): 
    - Open Command Prompt
    - Navigate to the mosco folder: cd C:\My Drive\MOS INVENTORY APP\mosco
    - Type: python main.py
    - Press Enter

STEP 5: VERIFY DATABASE FOLDERS EXIST
  The app creates these folders automatically:
    - oilseals/data/            (stores Oil Seals database)
    - packingseals/monoseals/data/     (stores Monoseals database)
    - packingseals/wiperseals/data/    (stores Wiper Seals database)
    - packingseals/wipermono/data/     (stores Wipermono database)
    - oilseals/photos/          (stores product photos)
    - packingseals/*/photos/    (stores photos for other modules)
  
  Do not delete or rename these folders.

STEP 6: CREATE ADMIN PASSWORD
  The default password is "1"
  You can discuss changing this with the system administrator.

========================================
DATABASE FILES EXPLAINED
========================================

Each module stores its data in a separate database:

File: oilseals_mm_inventory.db
Location: oilseals/data/
Purpose: Stores all Oil Seals products and transactions

File: monoseals_mm_inventory.db
Location: packingseals/monoseals/data/
Purpose: Stores all Monoseals products and transactions

File: wiperseals_mm_inventory.db
Location: packingseals/wiperseals/data/
Purpose: Stores all Wiper Seals products and transactions

File: wipermono_mm_inventory.db
Location: packingseals/wipermono/data/
Purpose: Stores all Wipermono products and transactions

IMPORTANT:
  - Never move or rename these files while the app is running.
  - Always backup these .db files daily.
  - If sharing via Google Drive, upload only after closing the app.

================================================================
SHARED DATABASE BEST-PRACTICE GUIDE
================================================================

If your company uses ONE DATABASE shared across multiple PCs:

SAFE WORKFLOW:

1. START OF SHIFT
  - Download latest database copy from cloud storage (Google Drive, etc.)
  - Place it in the correct data/ folder
  - Open the app and verify the database loads

2. DURING WORK
  - Make all your entries and transactions
  - Do NOT upload while someone else is working
  - Keep the app open — DO NOT close and reopen during the day

3. END OF WORK
  - Finish all your work
  - Close the MOSCO app completely
  - Wait 30 seconds for system to save everything
  - Upload the database file to cloud storage

4. NEXT PERSON'S SHIFT
  - Download the latest file before opening the app
  - Repeat from Step 1

WHAT NOT TO DO:

✗ DO NOT upload database while another PC is using the app
✗ DO NOT open the app while uploading to cloud
✗ DO NOT edit database files in cloud storage directly  
✗ DO NOT skip the backup step
✗ DO NOT share the exact same database from cloud without downloading first

WHY THIS MATTERS:

Changes made on PC A might be OVERWRITTEN by PC B if both upload at the same time.
This causes lost transactions and data corruption.

DAILY BACKUP PROCEDURE:

1. Keep a backup folder on USB drive or separate hard drive
2. Once per day, copy the .db files to your backup folder
3. Date your backups (e.g., "oilseals_backup_Feb13.db")
4. Keep at least 7 days of backups
5. If something goes wrong, you can restore from backup

CONFLICT RESOLUTION:

If the database becomes corrupted:
1. Close the app immediately
2. Do NOT open it again
3. Restore the latest backup to the data/ folder
4. Verify it works by opening a few products
5. Notify the system administrator

================================================================
KNOWN LIMITATIONS & RECOMMENDATIONS
================================================================

1. CLOUD SYNC RISK
   The system does not have built-in cloud sync.
   Simultaneous uploads = data loss risk.
   Recommendation: Follow the "Shared Database Best-Practice Guide" above.

2. MANUAL DATABASE HANDLING REQUIRED
   The app does not automatically sync with cloud storage.
   You must manually upload and download files.
   Recommendation: Create a daily upload checklist for staff.

3. NO AUTOMATIC BACKUPS
   The app does not create automatic backups.
   Backups are your responsibility.
   Recommendation: Assign one person per shift to handle backups.

4. PASSWORD SECURITY
   Default admin password is "1" (simple for learning).
   Recommendation: Change this to a strong password for production use.

5. NO USER ACCESS CONTROL
   All admin users have equal power (can see all data, delete products).
   Recommendation: Control who has admin access.

6. NO CHANGE LOG
   The system does not track who made what changes.
   Recommendation: Train staff to double-check before saving.

These are not bugs — they are design choices to keep the system simple and fast.

================================================================
VERSION & IMPROVEMENTS LOG
================================================================

SYSTEM VERSION: Production (Multiple Module Support)

RECENT IMPROVEMENTS (Latest Session):

✓ Window Title Navigation
  - Window title now shows exactly which module you are working in
  - Helps prevent editing wrong products
  - Examples: "MOS Inventory - OIL SEALS | MM | PRODUCTS"

✓ Category Dropdown Stability  
  - Switching between Oil Seals, Monoseals, Wiper Seals, Wipermono now works reliably
  - Both Products and Transactions tabs update correctly
  - No need to restart Admin window

✓ Product Editing Improvements
  - Edit changes take effect immediately
  - Transaction confirmation shows after edit
  - No need to exit and re-enter

✓ Fabrication Transaction Fix
  - Editing fabrication no longer creates duplicates
  - Can convert fabrication to Sale/Restock/Actual safely

✓ Brand Normalization
  - Automatic corrections: NAK→T.Y., NQK→T.Y., NTC→NOK
  - Country auto-fill based on brand
  - Keeps database clean and consistent

✓ Import Cleanup
  - Removed unused imports
  - Code is more efficient
  - Faster startup time

MODULES SUPPORTED:
  ✓ Oil Seals (Oilseals)
  ✓ Monoseals
  ✓ Wiper Seals
  ✓ Wipermono
  ✓ (More modules planned for future expansion)

================================================================
INTERNAL EMPLOYEE TRAINING GUIDE
================================================================

FOR NEW STAFF:

FIRST DAY - BASIC NAVIGATION

1. Opening the App
   - Double-click MOSCO.bat (or ask supervisotr how to run on your system)
   - Wait for window to appear (takes 5-10 seconds)
   - You should see a grid of category buttons

2. Finding the Right Category
   - Look at the main screen
   - Click on the category you need (e.g., "PACKING SEALS")
   - If it asks for sub-category, click to select (e.g., "MONOSEALS")
   - If it asks for unit type, click to select (e.g., "MM")

3. Finding a Product
   - Use the search boxes at the top
   - You can type TYPE, ID, OD, THICKNESS, or BRAND
   - Results filter automatically as you type
   - Press Esc to clear all filters and see everything

4. Using Right-Click Copy
   - Right-click on any product in the list
   - Product info is COPIED to clipboard
   - Paste into your email/quote (Ctrl+V)
   - Two blank lines are added between items
   - Perfect for quoting multiple items to customers

SECOND DAY - PRODUCT DETAILS

1. Opening Product Details
   - Double-click on any product row
   - A new window opens with complete info
   - You see stock, price, location, and notes

2. Reading the Stock Color
   - GREEN stock number = Good level
   - ORANGE stock number = Low, restock soon
   - RED stock number = Out of stock or critical

3. Understanding Transaction History
   - Scroll down to see all past sales and restocks
   - RED = Sold
   - BLUE = Restocked (added stock)
   - GREEN = Physical count (inventory adjustment)
   - Each row shows DATE, QUANTITY, PRICE, and more

4. Checking Location
   - Look for "Location: " in the details window
   - This tells you where the item is stored
   - Useful for finding inventory quickly

THIRD DAY - SIMPLE EDITING

1. Editing Location or Notes
   - Click the "Edit" button in the details window
   - Change the location or notes
   - Click "Save"
   - Changes take effect immediately

2. Understanding Price and Stock
   - "Price (SRP)" = Selling price per piece
   - "Current Stock" = How many pieces we have now
   - Both are calculated automatically based on transactions

3. Adjusting Stock Thresholds
   - Click on the big green/orange/red STOCK number
   - A popup appears
   - Set "Restock Needed" = when color turns RED
   - Set "Low on Stock" = when color turns ORANGE
   - Click Save

COMMON DAILY TASKS:

TASK: Customer asks for a quote
  1. Search for the product using Type or Brand
  2. Right-click on product row
  3. Paste into email (Ctrl+V)
  4. Easy!

TASK: Record a sale
  1. Go to Admin > Transactions tab
  2. Click "Add"
  3. Make sure button is RED (SALE)
  4. Select product, enter quantity, price
  5. Click Save
  6. Stock number updates automatically

TASK: Record a restock (purchased new items)
  1. Go to Admin > Transactions tab
  2. Click "Add"
  3. Make sure button is BLUE (RESTOCK)
  4. Select product, enter quantity
  5. Click Save
  6. Stock number updates automatically

TASK: Physical count (inventory verification)
  1. Go to Admin > Transactions tab
  2. Click "Add"
  3. Make sure button is GREEN (ACTUAL)
  4. Select product, enter exact stock count
  5. Click Save
  6. Stock updates to that number

MISTAKES TO AVOID:

X Do not edit the same product twice by accident
X Do not record a sale as a restock (stock will be wrong)
X Do not forget to specify if it's a SALE vs RESTOCK
X Do not close app without saving
X Do not edit database files manually

THINGS TO REMEMBER:

✓ Always verify product details before editing
✓ Double-check the category in the window title
✓ Use Esc to clear filters if you can't find a product
✓ Right-click copy is faster than typing
✓ Ask supervisors if unsure — better to ask than make a mistake

================================================================
SUPPORT & FEEDBACK
================================================================

PRIMARY CONTACT:
If you encounter errors or problems, contact the system administrator.

WHAT TO REPORT:
- Error messages (copy the exact text)
- What you were trying to do
- Which category/product you were working with
- Whether the issue is repeatable

ENCOURAGE EARLY REPORTING:
- Small problems found early are easier to fix
- Do not wait until end of day to report
- Report immediately if database looks corrupted

FEEDBACK & IMPROVEMENT SUGGESTIONS:
- If you have ideas to make the system better, let us know
- User feedback helps improve the app
- Common mistakes by staff guide future improvements

================================================================
FUTURE EXPANSION / PLANNED FEATURES
================================================================

The system is designed for expansion.

MODULES IN PLANNING STAGE:
- Mechanical Shaft Seals
- Oil Caps
- Rubber Diaphragms
- Coupling Inserts
- Impellers
- Ball Bearings
- Bushings (Flat Rings)
- Grease & Sealants
- ETC (Special items)

Each new module will:
  ✓ Have its own database
  ✓ Work like Oil Seals and Monoseals
  ✓ Support same features (search, right-click copy, admin panel)
  ✓ Integrate seamlessly with the main system

No special training will be needed for new modules — same workflow as current modules.
