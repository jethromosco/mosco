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

SPECIAL COPY RULES:

• Country names (Japan, Korea, China, etc.) are automatically removed when copying.

• If the product starts with "SPL", the "SPL" word is removed when copied.

• This applies to:
  - Oil Seals
  - Wiper Seals
  - Monoseals

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

11. SIMPLE TIPS
-------------------
- If you can't find an item, try typing less. For example, instead of "10.5", try just "10".
- Use right-click copy when quoting prices to customers.
- Pasted items already have spacing between them.
- Use the "Back" button to navigate, do not close the window unless you want to exit the app.

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

7. ADMIN KEYBOARD SHORTCUTS
---------------------------
- Ctrl + Tab: Switch between "Products" and "Transactions" tabs.
- Ctrl + Shift + Tab: Switch tabs in reverse.
- Ctrl + 1: Add a new Transaction (only in Transactions tab).
- Ctrl + 2: Add a new Product (only in Products tab).
- Delete: Delete the selected Transaction (only in Transactions tab).
- Ctrl + Tab (Inside Transaction Form): Change Transaction Type (Sale -> Restock -> Actual -> Fabrication).

8. IMPORTANT ADMIN NOTES
------------------------
- Data is saved automatically to the database file.
- Do not rename or move the database files manually while the app is running.
- When adding a product, make sure the "Type" and "Brand" are consistent (e.g., don't use "MOS" one time and "M.O.S." another time).
- If you change a product's size (ID/OD) in Edit mode, it updates that specific product record. It does not change past transaction history text, but the link remains valid.


================================================================
FINAL REMINDERS
================================================================

- Always check the "Stock Filter" if you think items are missing. You might be viewing only "Out of Stock" items.
- Remember to back up your database files regularly (copy the .db files to a safe place).
- If the app looks strange or buttons are missing, try resizing the window or pressing F11.
- Double-check your entries before saving, especially for Prices and Stock adjustments.
- Contact the system developer if you see "Database Error" messages.
