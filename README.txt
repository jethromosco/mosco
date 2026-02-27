MOSCO INVENTORY SYSTEM - USER & ADMIN MANUAL
================================================================

Welcome to MOSCO Inventory! This guide helps you manage stock and view products.

This manual is for:
- Regular staff (finding products, viewing details)
- Admin users (adding/editing products, recording sales & restocks)
- New employees (step-by-step learning)


================================================================
PART 1: QUICK START
================================================================

Getting Started:
1. Double-click the MOSCO.bat file (or ask your supervisor how to run it)
2. Wait 5-10 seconds for the app to open
3. You will see a grid of category buttons (Oil Seals, Monoseals, etc.)

Main Screen:
- Click any category button to see products
- The window title shows where you are (helps you stay oriented)
- Click "Back" button (top left) to return to the main screen


================================================================
PART 2: FINDING & VIEWING PRODUCTS
================================================================

SEARCHING FOR A PRODUCT
-------------------------
1. Click a category button to open it
2. You will see search boxes at the top of the product list
3. Type what you're looking for in any search box:
   * Type (e.g., TC, SC)
   * ID (Inner Diameter)
   * OD (Outer Diameter)
   * TH (Thickness)
   * Brand (e.g., NOK, T.Y.)
   * Part Number
4. Results update automatically as you type
5. To see all products again, press ESC

Helpful Tips:
- Search for less = Find more. "10" finds more than "10.5"
- Searches are not case-sensitive
- You can search by any part of the name

SMART PASTE - QUICK SIZE ENTRY (MM SEARCH ONLY)
-------------------------------------------------
Copy & paste messy size text - MOSCO handles the rest!

How It Works:
1. Copy any messy size text like:
   * "30mm ID x 40mm OD x 6 THK"
   * "30-40-6"
   * "TC 30 * 40 * 6 NOK"
   * "40 - 30 - 6" (numbers in any order!)
2. Click in any of the MM search boxes (ID, OD, or THK field)
3. Press Ctrl + V (or Cmd + V)
4. MOSCO automatically:
   * Extracts all the numbers
   * Figures out which is ID, OD, and THK
   * Fills all three fields
   * Refreshes the product list

Example:
- Copy: "30mm ID x 40mm OD x 6 THK"
- Paste in any size field with Ctrl+V
- Result: ID=30, OD=40, THK=6 (automatic!)

Smart Rules:
- Number sorting is automatic: Smallest=Thickness, Middle=ID, Largest=OD
- Works with any format (dashes, spaces, "x", "*", etc.)
- If something's wrong, just paste using normal Ctrl+V for plain text

ALTERNATIVE OFFER/S - WHEN EXACT SIZE NOT FOUND
-------------------------------------------------
Can't find the exact size? MOSCO shows you alternative thicknesses!

How It Works:
1. Search for a specific size: ID=30, OD=40, THK=6
2. If EXACT match not found:
   * ID and OD must match EXACTLY (no tolerance)
   * TH searches within a ±2 range to show alternative thicknesses
   * Shows products like: 30-40-4, 30-40-5, 30-40-7, 30-40-8 (same ID and OD, different thickness)
3. Status header shows: "⚠ Exact size not available – ALTERNATIVE OFFER/S" in large bold text

When This Helps:
- You need 30-40-6 but it's out of stock
- 30-40-5 or 30-40-7 might work instead (exact ID/OD, just different thickness)
- No need to search manually!

What Gets Shown:
- Products with EXACT ID and OD matching your search
- TH values within ±2 of what you searched (e.g., search TH=6 shows TH 4, 5, 6, 7, 8)
- Still respects all other filters (Brand, Type, Part Number)
- Exact matches NOT shown (those would be in normal results)

When It Doesn't Apply:
- If you searched for Brand or Type, only exact matches show
- Size-only search required for alternative offer to activate
- If no products exist with exact ID and OD, nothing is shown

Example Scenario:
Search: ID=30, OD=40, THK=6
Database has: 30-40-4, 30-40-5, 30-40-7, 30-40-8 (but NO 30-40-6 exactly)
Result: Shows all four with header "⚠ Exact size not available – ALTERNATIVE OFFER/S"  (note: 29-40-6 and 30-41-6 would NOT appear because ID and OD must be exact)

VIEWING PRODUCT DETAILS
-----------------------
Double-click any product row to open the full details window.

You will see:
- Stock number (colored: Green = Good, Orange = Low, Red = Out of stock)
- Price per piece (SRP)
- Location (where it's stored)
- Notes (any remarks about the product)
- Product photo (if available)
- Transaction history (all sales, restocks, and counts)

STOCK COLOR MEANINGS
---------------------
GREEN   = Good stock level, no action needed
ORANGE  = Running low, consider restocking soon
RED     = Out of stock or critical, restock immediately

To change when colors appear:
1. Click directly on the big colored STOCK number
2. A popup appears
3. Enter the quantity that triggers RED (restock needed)
4. Enter the quantity that triggers ORANGE (low stock)
5. Click Save


================================================================
PART 3: EDITING PRODUCT INFO
================================================================

You can edit: Location, Notes, and Price

How to Edit:
1. Open a product (double-click it)
2. Click the "Edit" button on the right side
3. You can now change:
   * Location (where the item is stored)
   * Notes (any remarks)
   * Price (selling price per piece)
4. Click "Save" when done
5. Changes take effect immediately


UPLOADING A PRODUCT PHOTO
---------------------------
If the product is "MOS" brand and has no photo:
1. Click the camera icon on the photo area
2. OR press Ctrl + 1
3. Select a photo from your computer
4. Click Save
5. The photo appears immediately


================================================================
PART 4: THEME & APPEARANCE
================================================================

Light Mode / Dark Mode:
1. Look for the Sun/Moon button in the top-right corner
2. Click it to switch between light (white) and dark (black) themes
3. Your preference stays while the app is running

Fullscreen Mode:
- Press F11 to remove window borders (fullscreen)
- Press F11 again to return to normal
- Useful if buttons or text look cut off


================================================================
PART 5: RIGHT-CLICK COPY (Fast Quoting)
================================================================

You can right-click in these places to copy product info:
- Product list rows
- Product cards/details
- Price display (SRP)
- Transaction history rows

What Gets Copied:
When you right-click, the product info is copied to your clipboard in this format:

    Type ID-OD-TH Brand Category
    ₱Price / pc.

Example:
    TC 30-47-7 NOK Oil Seal
    ₱250- / pc.

You can then paste this into:
- Emails (Ctrl + V)
- Word documents
- Google Sheets
- Quotes

IMPORTANT COPY RULES
---------------------
For SALES (Red transactions):
- Shows the actual price charged in that sale

For RESTOCKS (Blue transactions):
- Shows only the peso sign (₱)
- You can type the quantity right after

For ACTUAL COUNTS (Green transactions):
- Shows the recorded price normally

Automatic Features:
- Country names are removed (Japan, Korea, etc.)
- Brand is taken from restock information
- Two blank lines appear after each item for easy pasting


================================================================
PART 6: RECORDING SALES & RESTOCKS (ADMIN ONLY)
================================================================

ENTERING ADMIN MODE
---------------------
1. Click the "Admin" button (top-right corner)
   OR press Ctrl + 2
2. Enter the password: 1
3. The Admin Panel opens

RECORDING A SALE
-----------------
A sale reduces stock (stock goes down).

1. Go to Transactions tab (click "Transactions")
2. Click "Add" button
3. Make sure the RED button is selected (SALE)
4. Fill in:
   * Date (when the sale happened)
   * Product (search and select)
   * Unit (MM or INCH if available)
   * Quantity (how many pieces sold)
   * Price (how much was charged)
5. Click "Save"
6. Stock number decreases automatically

RECORDING A RESTOCK
--------------------
A restock increases stock (stock goes up).

1. Go to Transactions tab (click "Transactions")
2. Click "Add" button
3. Click the BLUE button to select (RESTOCK)
4. Fill in:
   * Date (when you received it)
   * Product (search and select)
   * Unit (MM or INCH if available)
   * Quantity (how many pieces received)
5. Click "Save"
6. Stock number increases automatically

PHYSICAL COUNT (ACTUAL)
------------------------
This sets the stock to an exact number (useful for inventory audits).

1. Go to Transactions tab
2. Click "Add" button
3. Click the GREEN button to select (ACTUAL)
4. Fill in:
   * Date (today's date usually)
   * Product (search and select)
   * Unit (MM or INCH if available)
   * Stock Amount (the exact count you verified)
5. Click "Save"
6. Stock changes to that exact number

FABRICATION (Special Mode)
----------------------------
For items that are made in-house (not purchased).

1. Go to Transactions tab
2. Click "Add" button
3. Click the purple/accent button to select (FABRICATION)
4. Fill in:
   * Date (when items were made)
   * Product (the item being made)
   * Unit (MM or INCH if available)
   * Qty Made (total items produced)
   * Qty Sold (items sold from that batch)
5. Click "Save"
6. Stock updates correctly (accounts for both production and sales)


ADDING A NEW PRODUCT (ADMIN ONLY)
-----------------------------------
1. Click the "Admin" button (top-right)
2. Go to "Products" tab
3. Click the green "Add" button
4. Fill in all fields:
   * Type (e.g., TC, SC)
   * ID, OD, TH (size dimensions)
   * Brand (e.g., NOK, T.Y.)
   * Initial Stock (starting quantity)
   * Price (selling price)
5. Click "Save"
6. The product appears in the list immediately

EDITING OR DELETING PRODUCTS (ADMIN ONLY)
-------------------------------------------
Edit a Product:
1. Find the product in the Products list
2. Click to select it
3. Click "Edit" button
4. Change the values you want to update
5. Click "Save"

Delete a Product:
1. Find the product in the list
2. Click to select it
3. Click "Delete" button
4. Confirm the warning
5. Product is removed permanently

WARNING: Deleted products cannot be recovered!


================================================================
PART 7: KEYBOARD SHORTCUTS - COMPLETE LIST
================================================================

GLOBAL SHORTCUTS (Work Everywhere)
-----------------------------------
F11                 → Toggle fullscreen mode (expand to full screen)
Ctrl + 2            → Open Admin Panel (password required)
Esc                 → Clear all search filters and show everything
Tab                 → Move to the next field or button
Shift + Tab         → Move to the previous field or button
Enter               → Confirm/Save (in forms)
Mouse Button-4      → Windows mouse back button (goes back one level)


IN PRODUCT LIST / SEARCH
-------------------------
Esc                 → Clear all search filters at once
BackSpace           → Delete text from current search field (clears one letter)
Arrow Keys          → Move up/down in product list
Enter               → Move focus away from search box


IN PRODUCT DETAILS WINDOW
---------------------------
Esc                 → Cancel edit mode or close window
Tab                 → Move to next editable field (Location → Notes → Price)
Shift + Tab         → Move to previous editable field


IN TRANSACTION WINDOW (Product Details)
-----------------------------------------
Ctrl + 1            → Upload a product photo
Ctrl + Q            → Toggle Edit Mode (edit Location, Notes, Price)
Return              → Save changes (when in edit mode)
Esc                 → Cancel editing (when in edit mode)


IN ADMIN PANEL TABS
--------------------
Ctrl + Tab          → Switch to next tab (Products ↔ Transactions)
Ctrl + Shift + Tab  → Switch to previous tab (reverse direction)


IN PRODUCTS ADMIN TAB
----------------------
Ctrl + 2            → Add a new product


IN TRANSACTIONS ADMIN TAB
---------------------------
Ctrl + 1            → Add a new transaction
Delete              → Delete selected transaction


IN TRANSACTION ADD/EDIT FORM
-------------------------------
Ctrl + Tab          → Cycle through transaction types:
                        Red (Sale) →
                        Blue (Restock) →
                        Green (Actual) →
                        Purple (Fabrication)
Ctrl + Shift + Tab  → Cycle backwards through transaction types
Return              → Save the transaction
Esc                 → Cancel and close the form


IN STOCK SETTINGS POPUP
------------------------
Return              → Save the new thresholds
Esc                 → Cancel without saving


IN PASSWORD DIALOG
-------------------
Return              → Submit password
Esc                 → Cancel and close


================================================================
PART 7B: MOUSE ACTIONS - COMPLETE LIST
================================================================

GENERAL CLICKS
---------------
Left-click Button   → Click any button to activate it
Left-click Field    → Click text fields to select them
Left-click Dropdown → Click to open dropdown menu
Double-click        → Open details (on product rows, product cards)
Right-click         → Copy information to clipboard


IN PRODUCT LIST
----------------
Left-click Row      → Select a product row
Double-click Row    → Open full product details window
Right-click Row     → Copy product info to clipboard
Mouse Button-4      → Go back one level (Windows mouse back button)


IN PRODUCT DETAILS WINDOW
---------------------------
Left-click Stock #  → Open stock threshold settings popup
Left-click Photo    → View photo in fullscreen viewer
Left-click X on Photo → Close fullscreen viewer
Left-click Camera   → Upload a new product photo


IN PRICE DISPLAY
-----------------
Right-click Price   → Copy product info to clipboard


IN TRANSACTION HISTORY LIST
-----------------------------
Left-click Row      → Select a transaction
Double-click Row    → Open transaction details
Right-click Row     → Copy product/price info to clipboard (based on type)


IN ADMIN PANEL
-----------------
Left-click Tab      → Switch between Products/Transactions tabs
Left-click Dropdown → Change module (Oil Seals, Monoseals, etc.)
Left-click Add      → Add new product or transaction
Left-click Edit     → Edit selected product or transaction
Left-click Delete   → Delete selected item (with confirmation)


IN FORMS
---------
Left-click Button   → Click to submit, save, or cancel
Left-click Checkbox → Toggle checkbox on/off
Left-click Dropdown → Select option from dropdown
Double-click Field  → Select all text in field


SPECIAL MOUSE ACTIONS
----------------------
Mouse Button-4      → Windows mouse back button
                       (invokes the back button of current screen)
                       Works: Home → Categories, Lists → Details, etc.


================================================================
PART 8: TROUBLESHOOTING
================================================================

PRODUCTS NOT SHOWING IN SEARCH
-------------------------------
Check the filter at the top:
1. Look for a "Filter" or "Stock" dropdown
2. If it says "Low Stock" or "Out of Stock", change it to "All"
3. Try pressing Esc to clear all filters
4. If still nothing, search for less text (e.g., "10" instead of "10.5")

STOCK NUMBER DOESN'T MATCH RECORDS
-------------------------------------
1. Open the product details
2. Click "Transactions" tab to see all sales and restocks
3. Add up all transactions to check the math
4. If you find an error, edit that transaction to fix it
5. Stock recalculates automatically

CAN'T SAVE A PRODUCT OR TRANSACTION
------------------------------------
1. Check that all required fields (*) are filled in
2. Make sure numbers only contain digits (no letters or extra spaces)
3. Check that prices use periods for decimals (10.50, not 10,50)
4. Make sure the date is valid
5. Click Save again

APP LOOKS STRANGE / BUTTONS MISSING / TEXT CUT OFF
----------------------------------------------------
1. Try resizing the window (drag the edges)
2. Press F11 to toggle fullscreen off, then on again
3. Press F11 again to return to normal view
4. Restart the app if it still looks wrong

DATABASE ERROR WHEN OPENING
-----------------------------
1. This usually means the database is corrupted or locked
2. Check that no one else is using the app on another computer
3. Close all other instances of the app
4. Restart the app

CAN'T OPEN ADMIN PANEL
------------------------
1. Make sure the password is correct (default is: 1)
2. Make sure the keyboard layout is correct (numbers only)
3. If you forgot the password, ask your system administrator


================================================================
PART 9: COMMON MISTAKES & HOW TO AVOID THEM
================================================================

MISTAKE 1: Recording a Sale as a Restock (or vice versa)
----------------------------------------------------------
Problem: Stock number is wrong because you picked the wrong transaction type.

How to Prevent:
- RED button = Sale (stock goes DOWN)
- BLUE button = Restock (stock goes UP)
- GREEN button = Exact count (set stock to exact number)
- Check the color before saving!

How to Fix:
1. Find the wrong transaction in history
2. Click "Edit"
3. Select the correct color
4. Click "Save"
5. Stock recalculates automatically

MISTAKE 2: Wrong Quantity Entered
-----------------------------------
Problem: You entered 5 instead of 50, so stock is wrong.

How to Prevent:
- Always double-check the number before clicking Save
- If you have a calculator, use it

How to Fix:
1. Find the transaction in history
2. Click "Edit"
3. Change the quantity to the correct number
4. Click "Save"
5. Stock updates immediately

MISTAKE 3: Added Product with Wrong Brand Spelling
-----------------------------------------------------
Problem: You typed "MOS" one time and "M.O.S." another time, creating two separate products.

How to Prevent:
- Always use the same spelling for brand names
- Example: Always use "MOS", never "M.O.S."
- The system has auto-corrections for common mistakes

How to Fix:
1. Delete the duplicate product
2. Make sure the remaining product has correct spelling

MISTAKE 4: Edited the Wrong Product
--------------------------------------
Problem: You edited a similar product and lost important info.

How to Prevent:
- Always read the product name carefully BEFORE clicking Edit
- Check the size (ID-OD-TH) and brand
- Window title shows the module you're in - verify it's correct

MISTAKE 5: Forgot Which Category You're In
---------------------------------------------
Problem: Added products to the wrong category.

How to Prevent:
- Always look at the window title at the very top
- Example: "MOS Inventory - PACKING SEALS | MONOSEALS | MM"
- This tells you exactly which category and module you're using
- Switch category BEFORE adding or editing


================================================================
PART 10: DAILY BEST PRACTICES
================================================================

Starting Your Shift:
1. Open the app
2. Check the window title to know which module you're in
3. Search for items you need to work with

During Your Shift:
1. Use right-click copy for quick price quoting
2. Don't leave search filters on (press Esc when done)
3. If stock looks wrong, check the transaction history
4. Save only when you're sure the info is correct

Quoting to Customers:
1. Search for the product
2. Right-click the product row
3. Paste into email (Ctrl + V)
4. Done! No need to type manually

Recording Sales:
1. Go to Admin > Transactions
2. Click Add
3. Select RED (Sale)
4. Enter the product, quantity, and price
5. Click Save

Restocking:
1. Go to Admin > Transactions
2. Click Add
3. Select BLUE (Restock)
4. Enter the product and quantity received
5. Click Save

Backing Up Your Data:
1. Copy the .db files from the data/ folders
2. Save them in a safe location (USB drive or backup folder)
3. Do this once per day
4. Keep backups for at least 7 days


================================================================
PART 11: MULTI-PC DATABASE SAFETY
================================================================

If your company shares ONE database file across multiple computers:

SAFE WORKFLOW:

1. START OF SHIFT
   - Download the latest database from shared storage (Google Drive, etc.)
   - Open the app
   - Verify the data looks correct

2. DURING WORK
   - Make all your entries and transactions
   - Keep the app open all day
   - Do NOT upload while someone else is working

3. END OF SHIFT
   - Finish all work
   - Close the app completely
   - Wait 30 seconds
   - Upload the database file back to shared storage

4. NEXT PERSON'S SHIFT
   - Download the latest file before opening the app
   - Repeat from step 1

WHAT NOT TO DO:

X Do NOT upload database while another computer is using the app
X Do NOT open the app while someone is uploading
X Do NOT edit database files in cloud storage directly
X Do NOT skip the backup step
X Do NOT share the database without downloading first


WHY THIS MATTERS:

Changes on PC A get OVERWRITTEN by PC B if both upload at the same time.
This causes lost transactions and data corruption.


DAILY BACKUP PROCEDURE:

1. Keep a backup folder (USB drive or separate hard drive)
2. Once per day, copy the .db files to your backup folder
3. Name the backups with dates (e.g., oilseals_backup_Feb13.db)
4. Keep at least 7 days of backups
5. If something goes wrong, restore from backup

If Database Becomes Corrupted:
1. Stop using the app immediately
2. Do NOT open it again
3. Restore the latest backup
4. Test it by opening a few products
5. Tell the system administrator


================================================================
PART 12: SETTING UP THE APP (For Installation)
================================================================

REQUIREMENTS

Python 3.9 or Newer:
- Go to python.org
- Download Python 3.9+ (NOT Python 2)
- Run the installer
- CHECK: "Add Python to PATH"
- Finish

Required Programs (Install in Order):
1. Open Command Prompt (Windows: Press Win+R, type cmd, press Enter)
2. Copy and paste these commands one at a time:
   
   pip install customtkinter
   pip install pillow
   pip install tkcalendar

3. Wait for each to finish before running the next

EXTRACTING THE APP:

1. Download the MOSCO Inventory APP folder
2. Extract it to a location (e.g., C:\My Drive\MOS INVENTORY APP\mosco)
3. Do NOT rename the main "mosco" folder

RUNNING THE APP:

Option A (Easy):
- Double-click the MOSCO.bat file

Option B (Manual):
1. Open Command Prompt
2. Navigate: cd C:\My Drive\MOS INVENTORY APP\mosco
3. Type: python main.py
4. Press Enter

DATABASE FOLDERS (Created Automatically):
- mosco/oilseals/data/                    (Oil Seals database)
- mosco/packingseals/monoseals/data/      (Monoseals database)
- mosco/packingseals/wiperseals/data/     (Wiper Seals database)
- mosco/packingseals/wipermono/data/      (Wipermono database)
- mosco/oilseals/photos/                  (Oil Seals photos)
- mosco/packingseals/*/photos/            (Other photos)

Do NOT delete or rename these folders.


ADMIN PASSWORD:

Default password: 1

You can discuss changing this to a stronger password with the system administrator.


================================================================
PART 13: DATABASE FILES EXPLAINED
================================================================

Each product category has its own database file:

Oil Seals:
- File: oilseals_mm_inventory.db
- Location: oilseals/data/
- Stores: All oil seal products and transactions

Monoseals:
- File: monoseals_mm_inventory.db
- Location: packingseals/monoseals/data/
- Stores: All monoseal products and transactions

Wiper Seals:
- File: wiperseals_mm_inventory.db
- Location: packingseals/wiperseals/data/
- Stores: All wiper seal products and transactions

Wipermono:
- File: wipermono_mm_inventory.db
- Location: packingseals/wipermono/data/
- Stores: All wipermono products and transactions

IMPORTANT:

- Never move or rename these files while the app is running
- Always back up these .db files daily
- If sharing via cloud, upload AFTER closing the app
- These files contain all your product and transaction data
- Losing these files means losing all your data


================================================================
PART 14: BRAND NORMALIZATION (Automatic Corrections)
================================================================

The system automatically corrects common brand name mistakes to keep your database clean:

Automatic Corrections:
- NAK → T.Y.
- NQK → T.Y.
- NTC → NOK

Automatic Country Fill-in:
- If a product's country of origin is blank, it gets filled in automatically based on the brand
- This keeps names consistent across the database

Why This Matters:
- Consistent brand names make searching easier
- Prevents duplicate product entries
- The system applies these rules automatically when you add/edit products
- You don't need to do anything special — it just works

Example:
If you type "NAK" as the brand:
- It automatically saves as "T.Y."
- All searches work correctly
- No duplicate products


================================================================
PART 15: CATEGORY DROPDOWN (Switching Modules in Admin)
================================================================

If your admin panel has a category dropdown:

How to Use:
1. Open Admin Panel (Ctrl + 2)
2. Find the category dropdown (usually near the top)
3. Click it and select a different category (e.g., Oil Seals → Monoseals)
4. Both Products and Transactions tabs update immediately
5. All data shown is for that selected category

No need to:
- Restart the Admin window
- Close and reopen the app
- It just works!

This lets you manage products in multiple categories without closing the Admin panel.


================================================================
PART 16: KNOWING WHERE YOU ARE (Window Title Help)
================================================================

The window title at the very top tells you exactly where you are:

Examples:

"MOS Inventory"
= At the main home screen (see category buttons)

"MOS Inventory - OIL SEALS"
= Inside Oil Seals category list

"MOS Inventory - PACKING SEALS | MONOSEALS | MM"
= In Monoseals, MM unit, viewing product list

"MOS Inventory - PACKING SEALS | MONOSEALS | MM | PRODUCTS"
= Same location, but specifically showing Products tab

"MOS Inventory - PACKING SEALS | MONOSEALS | MM | TRANSACTIONS"
= Same location, but showing Transaction history

"MOS Inventory - PACKING SEALS | MONOSEALS | MM | ADMIN"
= In Admin panel for that specific module

WHY THIS MATTERS:

- Know exactly which category you're working with
- Prevent editing products in the wrong category
- Understand if changes apply to Oil Seals or Monoseals
- Always check the title before editing or adding products


================================================================
PART 17: NEW EMPLOYEE TRAINING CHECKLIST
================================================================

FIRST DAY - BASICS

Things to Learn:
☐ How to open the app
☐ Find a product using search
☐ Open product details (double-click)
☐ Understand stock colors (Green/Orange/Red)
☐ Use right-click to copy prices
☐ Clear filters with Esc key
☐ Use window title to know where you are
☐ Exit the app properly

SECOND DAY - DETAILS

Things to Learn:
☐ Edit location and notes
☐ Change stock thresholds (click stock number)
☐ Upload a product photo
☐ Check transaction history
☐ Understand Light/Dark mode

THIRD DAY - ADMIN (If Authorized)

Things to Learn:
☐ Open Admin panel (Ctrl + 2, password: 1)
☐ Record a sale (Red button)
☐ Record a restock (Blue button)
☐ Record a physical count (Green button)
☐ Switch between Products and Transactions tabs (Ctrl + Tab)
☐ Edit a transaction
☐ Add a new product

FOURTH DAY - ADVANCED

Things to Learn:
☐ Fabrication mode (purple button)
☐ Category switching (dropdown in Admin)
☐ Understanding right-click copy rules (Red/Blue/Green differences)
☐ Backup procedures
☐ Multi-PC database safety

Common Daily Tasks by Role:

REGULAR STAFF:
- Search for products
- Copy prices using right-click
- Check stock levels
- Report low stock to supervisor

ADMIN USERS:
- Record sales and restocks
- Add new products
- Edit product information
- Fix transaction mistakes
- Back up database files


================================================================
PART 18: KNOWN LIMITATIONS & RECOMMENDATIONS
================================================================

CLOUD STORAGE SYNC:
Limitation: The app cannot sync with cloud storage automatically.
Recommendation: Follow the "Multi-PC Database Safety" section for safe sharing.

NO AUTOMATIC BACKUPS:
Limitation: The app does not back up your data automatically.
Recommendation: Assign one person per shift to handle backups. Do it every day.

MANUAL DATABASE HANDLING:
Limitation: You must manually upload/download database files from cloud storage.
Recommendation: Create a daily checklist for this task.

PASSWORD SECURITY:
Limitation: Default password is "1" (simple for learning).
Recommendation: Change to a strong password for production use.

NO USER ACCESS CONTROL:
Limitation: All admin users have equal power (can delete anything).
Recommendation: Train staff to double-check before saving. Control who has admin access.

NO CHANGE LOG:
Limitation: The system doesn't track who made what changes.
Recommendation: Keep a separate log if you need to know who changed what.


================================================================
PART 19: AVAILABLE CATEGORIES & MODULES
================================================================

Current Modules:

✓ OIL SEALS
  - Size Units: MM
  - Database: oilseals_mm_inventory.db

✓ PACKING SEALS - MONOSEALS
  - Size Units: MM
  - Database: monoseals_mm_inventory.db

✓ PACKING SEALS - WIPER SEALS
  - Size Units: MM
  - Database: wiperseals_mm_inventory.db

✓ PACKING SEALS - WIPERMONO
  - Size Units: MM
  - Database: wipermono_mm_inventory.db

Future Modules (Planned):
- Mechanical Shaft Seals
- Oil Caps
- Rubber Diaphragms
- Coupling Inserts
- Impellers
- Ball Bearings
- Bushings (Flat Rings)
- Grease & Sealants

Each new module will work the same way as these current modules.


================================================================
PART 20: SUPPORT & FEEDBACK
================================================================

ENCOUNTERING ERRORS?

Contact the system administrator with:
1. The exact error message (copy the text)
2. What you were trying to do
3. Which category/product you were working with
4. Whether the problem happens every time

SUGGESTIONS FOR IMPROVEMENT?

The system developers welcome feedback!
- If something is confusing, let them know
- If you have ideas to make it better, share them
- Common user mistakes help guide future improvements

REPORT ISSUES EARLY

Small problems found early are easier to fix.
Don't wait until end of day to report.
Report immediately if:
- Data looks corrupted
- Stock numbers seem wrong
- Database error appears
- App won't open


================================================================
PART 21: SYSTEM IMPROVEMENTS & VERSION HISTORY
================================================================

Latest Improvements:

✓ Window Title Navigation
  Shows exactly which module and category you're in

✓ Category Dropdown Stability
  Switching between modules works reliably
  No need to restart Admin window

✓ Product Editing Improvements
  Changes take effect immediately
  No need to close and reopen

✓ Fabrication Transaction Fix
  Can edit fabrication transactions without creating duplicates
  Can convert fabrication to Sale/Restock/Actual safely

✓ Brand Normalization
  Automatic corrections: NAK→T.Y., NQK→T.Y., NTC→NOK
  Keeps database clean and searchable

✓ Right-Click Copy
  Consistent formatting across all modules
  Special rules for different transaction types

✓ Alternative Offer Search Update
  ID and OD now require an exact match — no range tolerance applied
  TH uses a ±2 range to show nearby thickness alternatives
  Alternative offer header is now large and bold for visibility
  Shows: "⚠ Exact size not available – ALTERNATIVE OFFER/S"

✓ Import Cleanup
  More efficient code
  Faster startup time


================================================================
FINAL REMINDERS
================================================================

REMEMBER:

1. Window title shows where you are — always check it
2. Press Esc to clear filters when you can't find something
3. Double-check before saving (especially for prices and quantities)
4. Backup your database files every day
5. Don't close the window unless you want to exit
6. Back button goes ONE level up, not directly to home
7. Stock colors: Green = OK, Orange = Low, Red = Out
8. Red = Sale, Blue = Restock, Green = Count
9. Right-click to copy prices for faster quoting
10. Ask supervisors if unsure — better to ask than make a mistake

IF IN DOUBT:

- Check the window title
- Use Esc to clear filters
- Try pressing F11 if something looks wrong
- Restart the app
- Contact the system administrator

================================================================
END OF MANUAL
================================================================

Thank you for using MOSCO Inventory!

Questions? Contact your system administrator.

Version: Production (Multi-Module Support)
Last Updated: February 27, 2026

===================================================================
