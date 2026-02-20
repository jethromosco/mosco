# Copilot Instructions for MOSCO Inventory (Stability & Architecture-Preserving)

## CRITICAL PROJECT RULES

**These rules are non-negotiable. Violations break the project.**

- **WINDOWS OS ONLY** — All features (mouse Button-4 bindings, window state functions) are Windows-specific. Do not add cross-platform abstractions.
- **NO ARCHITECTURE CHANGES** — Do not refactor navigation, controller logic, or frame management. The 3-level hierarchical navigation flow is stable.
- **NO NEW FILES** — Do not create new modules, packages, or helper files unless explicitly required to fix a bug in existing code.
- **NO CONFIG FILES** — Do not create `requirements.txt`, `.env`, `config.yml`, etc.
- **NO REDESIGNS** — Do not change UI layout, move buttons, alter keyboard shortcuts, or rewrite window management.
- **ANALYZE FIRST** — Before editing any file, read the entire project context. This prevents cascading failures.
- **STABILITY OVER SPEED** — Test edge cases, check for side effects, validate state consistency before returning output.

---

## QUICK START

**Run from repository root:**
```bash
python main.py
```

**Required dependencies** (pip install if missing):
- `customtkinter` — Modern UI framework
- `pillow` (PIL) — Image handling
- `sqlite3` — Built-in Python module, no install needed

**Working directory** — Always run from workspace root so relative paths resolve:
- `icons/` — Icon PNG files
- `photos/` — Product photos storage
- `oilseals/data/`, `packingseals/monoseals/data/`, etc. — Database files

---

## PROJECT ARCHITECTURE OVERVIEW

### Frame Hierarchy
The app is built on **CustomTkinter frames** stacked via `.place(x=0, y=0, relwidth=1, relheight=1)`.

**Key frames:**
- `HomePage` — Main category button grid
- `CategoryPage` — Subcategory selection (for nested categories like PACKING SEALS)
- `InventoryApp` (dynamic) — Product list, search, details (loaded per category/unit)
- `TransactionWindow` (dynamic) — Product history, stock edits (linked to InventoryApp)
- `ComingSoonPage` — Placeholder for unimplemented categories or units
- `AdminPanel` (external window) — Password-protected administration

**Frame stacking rule:**
- Only **one frame is visible at a time** via `.winfo_viewable()`.
- Frames are placed on top of each other; switching frames calls `show_frame(name)`.
- **Do not use geometry managers (pack/grid) for frame switching** — always use `.place()`.

### InventoryContext (Single Source of Truth)
See [inventory_context.py](inventory_context.py).

This object controls **what the UI is allowed to show**:
- `products_available` → Can products tab be shown?
- `transactions_available` → Can transactions tab be shown?
- `coming_soon` → Show Coming Soon page instead?
- `reason` → Why Coming Soon (for debugging)?

**Key rules:**
- INCH is **never implemented** → Always Coming Soon
- Missing database/module → Coming Soon
- Only load InventoryApp UI if the class actually exists in the module
- All GUI logic must check context before assuming tabs exist

### AppController (Navigation Hub)
See [app_controller.py](app_controller.py#L1-L120).

Central controller managing:
- All frame transitions via `show_frame(page_name)`
- Category/subcategory/unit context via `set_inventory_context(category, subcategory, unit)`
- Back navigation via `go_back(page_name)`
- Admin panel singleton via `show_admin_panel(parent_app, on_close_callback)`
- Transaction window via `show_transaction_window(details, main_app, return_to)`

**Key instance variables:**
- `self.frames` — Dict of all frame objects keyed by name/identifier
- `self.current_category`, `self.current_subcategory`, `self.current_unit` — Active selection
- `self.current_context` — Authoritative InventoryContext object
- `self.current_section`, `self.current_action` — Window title state
- `self.admin_panel_instance` → Singleton Admin Panel reference (None = closed)

### Category Module Structure
Each implemented category mirrors this layout:
```
<category>/
  __init__.py
  database.py          # connect_db(), DATA_DIR, table schema
  data/                # SQLite database files (inventory.db)
  admin/
    products.py        # Product CRUD and AdminPanel class
    transactions.py    # Transaction CRUD
    ...
  gui/
    gui_mm.py          # Main InventoryApp class (products + transactions tabs)
    gui_products.py    # Product search/list layout
    gui_transactions.py # Transaction list layout
    gui_transaction_window.py  # TransactionWindow class (details + edit)
    ...
  photos/              # Product images
  ui/
    mm.py              # Helper functions (validation, conversions, DB queries)
    transaction_window.py
```

**Important:** Every category must expose:
1. **`InventoryApp` class** in `gui/gui_mm.py` (or delegated module)
2. **`TransactionWindow` class** in `gui/gui_transaction_window.py`
3. **`AdminPanel` class** in `gui/gui_products.py`

Without these classes, the category shows Coming Soon.

---

## NAVIGATION FLOW & RULES

### Hierarchical Navigation (Strict One-Level Back)

**Flow hierarchy:**
```
HOME
  ↓
CATEGORY PAGE (e.g., PACKING SEALS)
  ↓
SUBCATEGORY PAGE (e.g., MONOSEALS)  [optional, some categories skip this]
  ↓
UNIT SELECTION (e.g., MM / INCH)
  ↓
INVENTORY APP (Products + Transactions tabs)
  ↓
TRANSACTION WINDOW (Product details + edit)
```

**Back button rule:**
- Back button **always goes exactly one level up** in this hierarchy.
- No skipping levels, no jumping to HomePage directly (except from top level).
- Example: If in TRANSACTION WINDOW → back goes to INVENTORY APP, not to CATEGORY PAGE.

**Implementation:**
- Each frame stores `self.return_to` = the previous frame's name.
- When frame is created/placed, the value of `return_to` is set to the current visible frame (see `set_inventory_context()`).
- Back button calls `self._handle_back_button() → self.controller.go_back(self.return_to)`.

### Mouse Button-4 (Windows Back Button)

**Behavior:**
- Windows mouse back button (Button-4) must invoke the visible back button **exactly like clicking it**.
- Not a navigation override — it's a **physical button click simulation**.

**Implementation in AppController:**
```python
self.root.bind_all("<Button-4>", self._handle_global_mouse_back)
```

**Handler logic:**
1. Find the **topmost visible frame** by checking `winfo_viewable()` in reverse order.
2. Invoke its `back_btn.invoke()` — triggers the button's command callback.
3. If no back button found, fallback to `go_back("HomePage")`.

**CRITICAL:** Do not intercept Button-4 elsewhere or override the handler. One binding per window.

### Ctrl+2 Admin Shortcut

**Behavior:**
- Ctrl+2 opens the Admin panel **from any InventoryApp frame**.
- Must call `self.open_admin_panel()` method on the InventoryApp instance.

**Implementation:**
- Bound in `InventoryApp._setup_bindings()` via `self.root.bind("<Control-Key-2>", ...)`
- If Admin already open → restore, focus, bring to front (no password prompt).
- If Admin closed → show password dialog first.

**Do NOT:**
- Add Ctrl+2 bindings to TransactionWindow or HomePage.
- Change shortcut to a different key without explicit user request.

### Category Switcher Behavior

**When user clicks a category button from HomePage:**
1. `show_inventory_for(category_name)` parses category/subcategory/unit.
2. `set_inventory_context(category, subcategory, unit)` attempts to load InventoryApp.
3. If loaded, frame is created with `return_to = "HomePage"` (since we came from home).

**When user clicks a subcategory button from CategoryPage:**
1. `show_subcategory(name, sub_data)` sets `return_target = current_frame_name`.
2. New CategoryPage created with `return_to = return_target`.
3. When back is pressed, navigates to the parent CategoryPage, not directly to HomePage.

**RULE:** Every navigation action updates `return_to` to the current visible frame. This ensures step-by-step back navigation.

---

## WINDOW MANAGEMENT

### Window Title Dynamics

The title reflects current navigation state:
```
MOS Inventory                                            [HomePage]
MOS Inventory - OIL SEALS                                [Category only]
MOS Inventory - PACKING SEALS | MONOSEALS | MM           [Category + Subcategory + Unit]
MOS Inventory - PACKING SEALS | MONOSEALS | MM | PRODUCTS [... + Section]
MOS Inventory - PACKING SEALS | MONOSEALS | MM | ADMIN    [... + Section/Action]
```

**Update via:**
```python
self.controller.set_window_title(section="PRODUCTS", action=None)
```

**Sections:** PRODUCTS, TRANSACTIONS, ADMIN, etc.
**Actions:** ADD PRODUCT, EDIT PRODUCT, DELETE PRODUCT, etc.

**Rule:** Always update title when switching frames or opening dialogs. Users rely on title to know their location.

### Fullscreen Toggle (F11)

- Handled by `AppController._toggle_fullscreen(event)`.
- Saves previous geometry before entering fullscreen.
- Restores geometry when exiting.
- Fallback for InventoryApp-level handling if needed (delegates to controller).

---

## ADMIN PANEL RULES (CRITICAL)

### Singleton Pattern — Only One Instance Allowed

**Rule:** At any time, **at most one Admin Panel window exists**.

**How it works:**

```python
self.admin_panel_instance = None  # Initially closed

# When user requests Admin:
if self.admin_panel_instance is not None and self.admin_panel_instance.win.winfo_exists():
    # Already open → bring to front
    self.admin_panel_instance.win.lift()
    self.admin_panel_instance.win.focus_force()
    return  # Do NOT open password dialog
else:
    # Closed → create new instance
    admin_panel = AdminPanelClass(...)
    self.admin_panel_instance = admin_panel
```

**When Admin closes (on_closing callback):**
```python
self.controller._clear_admin_panel()  # Sets admin_panel_instance = None
```

### Admin Panel Lifecycle

1. **Opening:**
   - User clicks Admin button or presses Ctrl+2.
   - `AppController.show_admin_panel(parent_app, on_close_callback=...)` is called.
   - If already open → restore/focus (no password).
   - If closed → show password dialog, then create AdminPanel.

2. **Editing Products/Transactions:**
   - Changes are made in the Admin dialog.
   - When user saves, **the main InventoryApp must refresh** (see Data Consistency Rules).

3. **Closing:**
   - User clicks close button on Admin window.
   - `on_close_callback()` is invoked.
   - `_clear_admin_panel()` clears the singleton reference.
   - Main InventoryApp refreshes if callback specified.

### Do NOT:
- Create multiple AdminPanel instances or windows.
- Allow Admin window to spawn additional admin dialogs.
- Destroy Admin panel without clearing the singleton reference.
- Forget to refresh main_app after admin edits.

---

## DATA CONSISTENCY & REFRESH RULES

### Refresh Requirements

**After ANY of these operations, the system must refresh:**
1. **Add** — New product/transaction created
2. **Edit** — Product/transaction modified (SRP, location, notes, thresholds)
3. **Delete** — Product/transaction removed
4. **Category Switch** — User selects a different category/unit
5. **Admin Close** — Admin panel closes after edits

### What Must Refresh

**InventoryApp refresh:**
- Call `self.refresh_product_list()` to reload from database.
- Clears search filters and redraws the product table.
- Do NOT rely on in-memory lists or cached data.

**TransactionWindow refresh:**
- When opened, always load fresh data via `set_details(details, main_app)`.
- This calls `load_transactions_records()` from the database, not from cache.
- Example: After adding a transaction, close and reopen TransactionWindow to see new record.

**Admin close callback:**
- After AdminPanel closes, the supplied `on_close_callback` is invoked.
- Callback typically calls `main_app.refresh_product_list()` to reload all products.
- Ensures user sees added/edited products in real-time.

### Stale Data Prevention

**Rule:** Never persist references to product lists or transaction records across navigation boundaries.

**Bad:**
```python
self.products = load_products()  # Cache at frame init
# ... Later, user edits via Admin panel ...
# self.products is stale, shows old data
```

**Good:**
```python
def refresh_product_list(self):
    self.products = load_products()  # Fresh load every time
    self.tree.delete(*self.tree.get_children())
    for product in self.products:
        self.tree.insert("", "end", values=(...))
```

### Category Context Preservation

When switching categories:
1. `set_inventory_context(category, subcategory, unit)` updates the active context.
2. All subsequent data loads use this context.
3. Do NOT inherit product lists from previous category.
4. Ensure transaction window only shows records matching current context.

---

## TRANSACTION WINDOW DATA LOADING

**Critical sequence:**

1. **User clicks a product row:**
   ```python
   self.controller.show_transaction_window(details, main_app=self, return_to=...)
   ```

2. **AppController shows TransactionWindow:**
   ```python
   frame = TransactionWindow(self.container, details, controller=self, return_to=return_to)
   self.frames["TransactionWindow"] = frame
   frame.place(...)
   frame.update_idletasks()  # Ensure all widgets are created
   frame.set_details(details, main_app)  # Load data AFTER widget creation
   ```

3. **TransactionWindow loads data:**
   ```python
   def set_details(self, details, main_app):
       self.details = details
       self.main_app = main_app
       transactions = load_transactions_records(...)  # Fresh from DB
       self.tree.delete(*self.tree.get_children())
       for tx in transactions:
           self.tree.insert("", "end", values=(...))
   ```

**Critical rules:**
- **Always call `frame.update_idletasks()` before `set_details()`** to ensure tree widget exists.
- **Do NOT load data in `__init__`** — wait for widget initialization.
- **Load fresh from database,** not from cached lists.
- If tree widget not found, retry with `self.root.after(50, lambda: ...)`

### Transaction Window → Admin → Back

**Flow:**
1. TransactionWindow open, user clicks Edit.
2. Admin panel opens with `on_close_callback=self.refresh_product_list` (or similar).
3. User edits product details, saves, closes Admin.
4. Callback refreshes the TransactionWindow's product list (or full InventoryApp).
5. TransactionWindow shows updated data (SRP, location, notes, thresholds).

**Do NOT:**
- Assume TransactionWindow persists after Admin close.
- Keep references to closed/destroyed frames.
- Reuse stale DataFrame objects.

---

## STRICT DEVELOPMENT CONSTRAINTS

### Forbidden Patterns

1. **Do NOT add new files unless required to fix a bug:**
   - No new scripts, modules, or utilities.
   - No refactoring scripts or helper files.
   - Exception: Bug fixes to existing code only.

2. **Do NOT refactor architecture:**
   - Navigation flow is locked (HomePage → CategoryPage → InventoryApp → TransactionWindow).
   - Controller logic is fixed.
   - Frame management is stable.
   - Only refactor if fixing a specific bug.

3. **Do NOT redesign UI:**
   - Button positions (back, admin) are absolute-positioned and tied to `on_window_resize()`.
   - Do not move elements to pack/grid managers.
   - Do not add new header/footer structures.
   - Preserve theme subscription pattern (`theme.subscribe(self.apply_theme)`).

4. **Do NOT create configuration systems:**
   - No `config.ini`, `.env`, or `settings.json`.
   - Hardcoded values are intentional (theme colors, window size limits, etc.).

5. **Do NOT add cross-platform code:**
   - Windows Button-4 binding is intentional.
   - Do not add fallbacks for Mac/Linux mouse events.
   - Do not add conditional OS checks in navigation code.

6. **Do NOT change keyboard shortcuts:**
   - Escape = clear filters (do not reuse for other purposes).
   - Ctrl+2 = Admin panel (do not change key).
   - Backspace = back navigation in search fields (do not disable).
   - Return = remove focus (do not intercept).

7. **Do NOT alter database patterns:**
   - Each category has its own `database.py` and `data/` directory.
   - Do not consolidate databases.
   - Do not add global connection pooling.
   - Relative paths to `DATA_DIR` are intentional.

### Required Practices

- **Always read the entire project** before editing any file.
- **Test edge cases:** What happens when Admin closes? When category switches?
- **Check for side effects:** Does this change affect back navigation? Category context?
- **Validate state:** Before returning, ensure `current_context` is correct, `return_to` is set, and frames are properly placed.
- **Log clearly:** Use print statements like `[FRAME]`, `[CONTEXT]`, `[NAVIGATION]` for debugging.
- **Update window title** whenever navigation state changes.

---

## DEBUGGING & SAFETY GUIDELINES

### Pre-Edit Checklist

Before modifying any file, answer these questions:

1. **Navigation impact:** Does this change affect back button, frame switching, or hierarchy?
2. **Data consistency:** Does this affect product loads, transactions, or admin workflows?
3. **Admin panel:** Could this break the singleton pattern or admin panel lifecycle?
4. **Frame state:** Are frames properly placed? Is `return_to` set correctly?
5. **Context accuracy:** Does current context match actual UI state?

### Common Bugs to Prevent

#### Bug: Stale Transaction Data
**Symptom:** TransactionWindow shows old records after editing via Admin.
**Cause:** `set_details()` called before tree widget exists, or using cached list.
**Fix:** Always call `frame.update_idletasks()` before `set_details()`. Load fresh from DB.

#### Bug: Wrong Back Target
**Symptom:** Back button jumps multiple levels instead of one level.
**Cause:** `return_to` not set when frame created.
**Fix:** In `set_inventory_context()`, set frame's `return_to = self.get_current_frame_name()`.

#### Bug: Duplicate Admin Windows
**Symptom:** Multiple Admin panels open simultaneously.
**Cause:** `admin_panel_instance` not cleared on close, or multiple instances created.
**Fix:** Ensure `_clear_admin_panel()` called in `on_closing()`. Check `is_admin_panel_open()` before creating new.

#### Bug: Mouse Button-4 Invokes Wrong Back Button
**Symptom:** Back button press navigates from wrong frame.
**Cause:** Multiple frames visible via `winfo_viewable()`, or handler doesn't find topmost frame.
**Fix:** In `_handle_global_mouse_back()`, filter `winfo_viewable()` and select last (topmost) frame.

#### Bug: TransactionWindow Not Visible After Show
**Symptom:** TransactionWindow created but doesn't appear, or user sees previous frame.
**Cause:** Previous frame not hidden via `place_forget()`.
**Fix:** Before placing TransactionWindow, explicitly hide current frame:
```python
if current_frame:
    current_frame.place_forget()
```

#### Bug: Category Switch Shows Old Products
**Symptom:** Switching from OIL SEALS to MONOSEALS shows OIL SEALS products.
**Cause:** InventoryApp not refreshed, or wrong context loaded.
**Fix:** Call `refresh_product_list()` in `on_frame_show()`. Verify `current_context` changed.

#### Bug: Search Filters Not Clearing
**Symptom:** Switching categories preserves search from previous category.
**Cause:** Search variables not cleared on category switch.
**Fix:** In `on_frame_show()`, call `self.clear_filters()` to reset all search vars.

### Validation Checks

After making changes, verify:

```python
# 1. Check frame visibility
visible_frame = None
for name, frame in self.frames.items():
    if frame.winfo_viewable():
        visible_frame = name
assert visible_frame is not None, "No frame visible!"

# 2. Check context matches UI
assert self.current_context.category == current_frame_category

# 3. Check return_to chain
frame = self.frames[visible_frame_name]
assert hasattr(frame, 'return_to'), "Frame missing return_to!"

# 4. Check admin panel state
assert self.admin_panel_instance is None or self.admin_panel_instance.win.winfo_exists()

# 5. Check transaction data freshness
# (After TransactionWindow.set_details, verify tree has rows)
assert len(self.tree.get_children()) == expected_transaction_count
```

---

## KEY FILES & THEIR ROLES

| File | Purpose |
|------|---------|
| [main.py](main.py#L1-L40) | Entry point, theme init, AppController creation |
| [app_controller.py](app_controller.py#L1-L150) | Frame management, navigation, context loading |
| [inventory_context.py](inventory_context.py#L1-L80) | Context data model (what's available to show) |
| [theme.py](theme.py) | Centralized theme values, subscription system |
| [home_page.py](home_page.py) | HomePage, CategoryPage, ComingSoonPage classes |
| [oilseals/gui/gui_mm.py](oilseals/gui/gui_mm.py#L1-L150) | Example InventoryApp (products + transactions) |
| [oilseals/gui/gui_transaction_window.py](oilseals/gui/gui_transaction_window.py#L1-L100) | Example TransactionWindow |
| [oilseals/gui/gui_products.py](oilseals/gui/gui_products.py) | Example AdminPanel |
| [oilseals/database.py](oilseals/database.py) | Database connection, DATA_DIR, schema setup |
| [oilseals/ui/mm.py](oilseals/ui/mm.py) | Helper functions (validation, conversions, queries) |

---

## EXTENDING THE APP (Within Constraints)

### Adding a New Category Implementation

1. **Create folder structure:**
   ```
   newcategory/
     __init__.py
     database.py
     data/
     admin/
     gui/
     photos/
     ui/
   ```

2. **Implement required classes:**
   - `newcategory/gui/gui_mm.py` → `InventoryApp` class
   - `newcategory/gui/gui_transaction_window.py` → `TransactionWindow` class
   - `newcategory/gui/gui_products.py` → `AdminPanel` class

3. **Register in CATEGORY_FOLDER_MAP:**
   ```python
   CATEGORY_FOLDER_MAP = {
       ...
       "NEW CATEGORY": "newcategory",
   }
   ```

4. **Mirror oilseals/ patterns exactly:**
   - Use same method signatures.
   - Copy theme subscriptions, keyboard bindings, search vars setup.
   - Implement `on_frame_show()` hook for refresh.
   - Set `return_to` in `__init__` if used outside HomeNotifications.

### Bug Fixes Only

- Fix data consistency issues → Refresh after edits.
- Fix stale transaction window data → Load fresh from DB.
- Fix back navigation to wrong level → Verify `return_to` chain.
- Fix admin panel reopening → Check singleton pattern.

**Do NOT use bug fixes as justification for architecture changes.**

---

## FINAL CHECKLIST

Before submitting any change:

- [ ] Entire project was read before editing.
- [ ] No new files created (unless fixing a bug).
- [ ] No architecture / navigation changes.
- [ ] No UI redesigns or button moves.
- [ ] No cross-platform code added.
- [ ] Data consistency verified (refresh after add/edit/delete).
- [ ] Window title updated appropriately.
- [ ] `return_to` chain correct for back navigation.
- [ ] Admin panel singleton pattern maintained.
- [ ] TransactionWindow loads fresh data (not cached).
- [ ] Mouse Button-4 binding preserved.
- [ ] Keyboard shortcuts unchanged (unless fixing specific bug).
- [ ] Theme subscriptions in place.
- [ ] State consistency verified (context, frames, visibility).

---

## QUESTIONS OR CLARIFICATIONS?

If this document is ambiguous or missing critical information, request additional detail by section name. Do not attempt interpretation or adaptation—ask for clarification first.
