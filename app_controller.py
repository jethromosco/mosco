import customtkinter as ctk
import importlib
import pkgutil
import os
from theme import theme
from home_page import HomePage, CategoryPage, ComingSoonPage
from inventory_context import InventoryContext, create_context, INVALID_CONTEXT


CATEGORY_FOLDER_MAP = {
    # Main categories with implementations
    "OIL SEALS": "oilseals",
    "O-RINGS": "orings",
    "O-CORDS": "ocords",
    "O-RING KITS": "oringkits",
    "QUAD RINGS (AIR SEALS)": "quadrings",
    "PACKING SEALS": "packingseals",
    
    # Packing seals subcategories - explicit mappings for modular structure
    # These allow each subcategory to have its own database and GUI implementation
    "PACKING SEALS MONOSEALS": "packingseals/monoseals",
    "PACKING SEALS WIPER SEALS": "packingseals/wiperseals",
    "PACKING SEALS WIPERMONO": "packingseals/wipermono",
    "PACKING SEALS VEE PACKING": "packingseals/vee",
    "PACKING SEALS ZF PACKING": "packingseals/zf",
    
    # Lock rings with subtypes
    "LOCK RINGS (CIRCLIPS)": "lockrings",
    
    # Other categories with implementations
    "V-RINGS": "vrings",
    "PISTON CUPS": "pistoncups",
    "VALVE SEALS": "valveseals",
    
    # Coming Soon / Future categories (None = not yet implemented)
    "MECHANICAL SHAFT SEALS": None,
    "OIL CAPS": None,
    "RUBBER DIAPHRAGMS": None,
    "COUPLING INSERTS": None,
    "IMPELLERS": None,
    "BALL BEARINGS": None,
    "BUSHINGS (FLAT RINGS)": None,
    "GREASE & SEALANTS": None,
    "ETC. (SPECIAL)": None,
}


class AppController:
    def __init__(self, root):
        self.root = root
        # Do not force any window state here; respect user's window sizing.
        self.root.configure(bg=theme.get("bg"))

        # Track exclusive fullscreen state and remember previous geometry to
        # restore when exiting fullscreen.
        self._is_fullscreen = False
        self._previous_geometry = None
        try:
            self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        except Exception:
            pass

        # Create container frame using CustomTkinter
        self.container = ctk.CTkFrame(root, fg_color=theme.get("bg"))
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        # Current selected inventory context (single source of truth)
        self.current_category = None
        self.current_subcategory = None
        self.current_unit = None
        self.current_db_module = None
        self.current_context = INVALID_CONTEXT  # The authoritative context object
        
        # Dynamic window title tracking
        self.current_section = None  # PRODUCTS, TRANSACTIONS, ADMIN, etc.
        self.current_action = None   # ADD PRODUCT, EDIT PRODUCT, DELETE PRODUCT, etc.

        # Create and add home page
        home_page = HomePage(self.container, controller=self)
        self.frames["HomePage"] = home_page
        home_page.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_frame("HomePage")

    def add_category_page(self, name, sub_data, return_to="HomePage"):
        frame = CategoryPage(self.container, self, name, sub_data, return_to=return_to)
        # Track the parent category for nested navigation
        frame.parent_category = self.current_category
        self.frames[name] = frame
        frame.place(x=0, y=0, relwidth=1, relheight=1)

    def _build_window_title(self):
        """Build dynamic window title based on current navigation context."""
        parts = ["MOS Inventory"]
        
        # Add category if present
        if self.current_category:
            parts.append(self.current_category)
        
        # Add subcategory if present
        if self.current_subcategory:
            parts.append(self.current_subcategory)
        
        # Add unit (MM/INCH) if present
        if self.current_unit:
            parts.append(self.current_unit)
        
        # Add section (PRODUCTS, TRANSACTIONS, ADMIN, etc.) if present
        if self.current_section:
            parts.append(self.current_section)
        
        # Add action (ADD PRODUCT, EDIT PRODUCT, DELETE PRODUCT, etc.) if present
        if self.current_action:
            parts.append(self.current_action)
        
        # Build title with " - " separating base from hierarchy, and " | " between hierarchy levels
        if len(parts) == 1:
            title = parts[0]
        else:
            base = parts[0]
            hierarchy = " | ".join(parts[1:])
            title = f"{base} - {hierarchy}"
        
        return title

    def set_window_title(self, section=None, action=None):
        """Update window title, optionally setting section and action first.
        
        Args:
            section: Current section (PRODUCTS, TRANSACTIONS, ADMIN, etc.)
            action: Current action (ADD PRODUCT, EDIT PRODUCT, etc.)
        """
        if section is not None:
            self.current_section = section
        if action is not None:
            self.current_action = action
        
        title = self._build_window_title()
        self.root.title(title)

    def show_subcategory(self, name, sub_data):
        current_frame = self.get_current_frame_name()
        return_target = current_frame if current_frame else "HomePage"

        if sub_data == "COMING_SOON":
            self.show_coming_soon(name)
            return

        if not sub_data:
            self.show_inventory_for(name)
            return

        if name not in self.frames:
            self.add_category_page(name, sub_data, return_to=return_target)

        self.show_frame(name)

    def show_inventory_for(self, category_name):
        # Backwards-compatible wrapper that attempts to load an InventoryApp
        # for the given category by delegating to the new centralized loader.
        # The new loader will try several candidate module paths and show
        # a "Coming Soon" page when no implementation exists.
        # 
        # category_name can be:
        # 1. "OIL SEALS MM" (category with unit)
        # 2. "MONOSEALS MM" (subcategory + unit, when called from nested CategoryPage)
        # 3. "PACKING SEALS MONOSEALS" (category + subcategory)
        # 4. "PACKING SEALS WIPER SEALS MM" (category + multi-word subcategory + unit)
        
        parts = category_name.split()
        
        # Strategy: Look for known CATEGORY_FOLDER_MAP keys first
        category = None
        subcategory = None
        unit = None
        
        # Try to match the first N words as a known category
        for i in range(len(parts), 0, -1):
            candidate_cat = " ".join(parts[:i])
            if candidate_cat in CATEGORY_FOLDER_MAP:
                category = candidate_cat
                remaining = parts[i:]
                if len(remaining) == 2:
                    # category + subcategory + unit (or category + two-word subcategory)
                    # Need to check if remaining is a valid subcategory pair or subcategory+unit
                    subcategory = remaining[0]
                    unit = remaining[1]
                elif len(remaining) == 1:
                    # category + unit (or category + subcategory if no children)
                    unit = remaining[0]
                elif len(remaining) >= 3:
                    # Multiple remaining parts: try to parse as subcategory + unit
                    # The last part is likely the unit (MM/INCH)
                    unit = remaining[-1]
                    subcategory = " ".join(remaining[:-1])
                break
        
        # If no known category found, check if this is a nested subcategory
        if category is None:
            from home_page import categories
            first_part = parts[0]
            for cat_name, cat_data in categories.items():
                if isinstance(cat_data, dict) and first_part in cat_data:
                    # Found parent category with first_part as subcategory
                    category = cat_name
                    subcategory = first_part
                    if len(parts) > 1:
                        unit = parts[1]
                    break
            
            # If still not found, try matching multi-word subcategories
            if category is None and len(parts) >= 2:
                for cat_name, cat_data in categories.items():
                    if isinstance(cat_data, dict):
                        # Try to match progressively longer subcategory names
                        for i in range(len(parts)-1, 0, -1):
                            candidate_subcat = " ".join(parts[:i])
                            if candidate_subcat in cat_data:
                                category = cat_name
                                subcategory = candidate_subcat
                                if i < len(parts):
                                    unit = parts[i]
                                break
                    if category:
                        break
        
        # Fallback
        if category is None:
            if len(parts) >= 3:
                category = " ".join(parts[:-2])
                subcategory = parts[-2]
                unit = parts[-1]
            elif len(parts) == 2:
                category = parts[0]
                unit = parts[1]
            else:
                category = category_name
        
        self.set_inventory_context(category, subcategory, unit)


    def show_frame(self, page_name):
        """Show a frame with smooth transition animation"""
        # Get currently visible frame
        current_frame = None
        for frame in self.frames.values():
            try:
                if frame.winfo_viewable():
                    current_frame = frame
                    break
            except Exception:
                pass
        
        # Hide current frame with fade-out
        if current_frame:
            current_frame.place_forget()
        
        # Show the requested frame with fade-in
        if page_name in self.frames:
            frame = self.frames[page_name]
            # Ensure frame is placed before updating
            frame.place(x=0, y=0, relwidth=1, relheight=1)
            frame.lift()
            # Use after to ensure smooth rendering on the next frame
            self.root.after(1, lambda: frame.update_idletasks())
        
        # Update window title based on current frame
        if page_name == "HomePage":
            # When returning home, reset all context
            self.current_category = None
            self.current_subcategory = None
            self.current_unit = None
            self.current_section = None
            self.current_action = None
            self.set_window_title()
        elif page_name and page_name != "HomePage":
            # For category/inventory pages, just update title (context should be set separately)
            self.set_window_title()

    # --- New centralized inventory context handling ---
    def set_inventory_context(self, category, subcategory=None, unit=None) -> InventoryContext:
        """Set the active inventory context and load the corresponding UI.

        This is the **single source of truth** for what inventory is selected.
        It returns an InventoryContext object that explicitly declares:
        - products_available: Can products be shown?
        - transactions_available: Can transactions be shown?
        - coming_soon: Should Coming Soon be shown?
        - reason: Why Coming Soon (if applicable)?
        
        RULES:
        1. INCH is never implemented → always Coming Soon
        2. Missing DB/module → Coming Soon
        3. Only load UI if InventoryApp class exists
        4. GUI must check context before assuming tabs exist
        
        Returns:
            InventoryContext object describing availability
        """
        
        # Store selected context
        self.current_category = category
        self.current_subcategory = subcategory
        self.current_unit = unit

        # RULE 1: INCH is never implemented
        if unit and unit.upper() == "INCH":
            reason = "INCH system not yet implemented"
            print(f"[CONTEXT] {category} {subcategory or ''} {unit}: {reason}")
            context = create_context(
                category=category,
                subcategory=subcategory,
                unit=unit,
                coming_soon=True,
                reason=reason
            )
            self.current_context = context
            self.show_coming_soon(f"{category} {subcategory or ''} {unit}".strip())
            return context

        # Try to load MM implementation
        base_pkg = CATEGORY_FOLDER_MAP.get(category)
        if not base_pkg:
            cat_l = (category or '').lower()
            for k, v in CATEGORY_FOLDER_MAP.items():
                if k and k.lower() in cat_l:
                    base_pkg = v
                    break
        if not base_pkg:
            base_pkg = ''.join(word.lower() for word in (category or '').split())

        candidates = []
        sub_folder = (subcategory or '') and subcategory.replace(' ', '').lower()
        unit_name = (unit or '').lower() if unit else None

        # Candidate patterns (most specific first)
        if base_pkg and sub_folder and unit_name:
            candidates.append(f"{base_pkg}.{sub_folder}.gui.gui_{unit_name}")
            candidates.append(f"{base_pkg}.{sub_folder}.gui.gui_{sub_folder}")
        if base_pkg and unit_name:
            candidates.append(f"{base_pkg}.gui.gui_{unit_name}")
            if sub_folder:
                candidates.append(f"{base_pkg}.gui.gui_{sub_folder}")

        loaded = False
        loaded_module = None
        loaded_path = None
        
        print(f"[CONTEXT] Trying {len(candidates)} candidates for {category} {subcategory or ''} {unit or ''}")
        
        for mod_path in candidates:
            try:
                mod = importlib.import_module(mod_path)
                InventoryClass = getattr(mod, 'InventoryApp', None)
                if InventoryClass:
                    loaded = True
                    loaded_module = InventoryClass
                    loaded_path = mod_path
                    print(f"[CONTEXT] ✓ Found InventoryApp in {mod_path}")
                    break
                else:
                    print(f"[CONTEXT] ✗ No InventoryApp in {mod_path}")
            except Exception as e:
                print(f"[CONTEXT] ✗ Failed to import {mod_path}: {type(e).__name__}")
                continue

        # Try fallbacks if primary candidates failed
        if not loaded and base_pkg:
            # Only allow fallback to a module if it matches the requested subcategory/unit
            # Never fallback to a different subcategory (e.g., never load Mono for WiperMono)
            fallbacks = []
            # Only add {base_pkg}.gui.gui_mm if there is no subcategory (top-level only)
            if not sub_folder:
                fallbacks.append(f"{base_pkg}.gui.gui_mm")
            # Scan subpackages, but only allow fallback to the exact requested subcategory
            try:
                pkg = importlib.import_module(base_pkg)
                if hasattr(pkg, '__path__') and sub_folder:
                    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
                        if name == sub_folder:
                            fallbacks.append(f"{base_pkg}.{name}.gui.gui_mm")
                            fallbacks.append(f"{base_pkg}.{name}.gui.gui_{name}")
            except Exception:
                pass

            print(f"[CONTEXT] Trying {len(fallbacks)} fallback modules (filtered by subcategory)")
            for mod_path in fallbacks:
                try:
                    mod = importlib.import_module(mod_path)
                    InventoryClass = getattr(mod, 'InventoryApp', None)
                    if InventoryClass:
                        loaded = True
                        loaded_module = InventoryClass
                        loaded_path = mod_path
                        print(f"[CONTEXT] ✓ Found InventoryApp in fallback {mod_path}")
                        break
                except Exception as e:
                    print(f"[CONTEXT] ✗ Fallback failed {mod_path}: {type(e).__name__}")
                    continue

        # Create context object (this is authoritative)
        if loaded and loaded_module:
            # SUCCESS: We can show the full UI
            context = create_context(
                category=category,
                subcategory=subcategory,
                unit=unit,
                products_available=True,
                transactions_available=True,
                coming_soon=False,
                reason="Module loaded successfully",
                module_path=loaded_path
            )
            print(f"[CONTEXT] ✓ {context}")
            self.current_context = context
            
            # Load and show the InventoryApp
            frame_key = f"{category}::{subcategory or ''}::{unit or ''}"
            if frame_key not in self.frames:
                try:
                    frame = loaded_module(self.container, controller=self)
                    self.frames[frame_key] = frame
                    frame.place(x=0, y=0, relwidth=1, relheight=1)
                    print(f"[CONTEXT] ✓ Created and placed InventoryApp frame")
                except Exception as e:
                    print(f"[CONTEXT] ✗ Failed to create InventoryApp: {e}")
                    # Fall through to Coming Soon
                    context = create_context(
                        category=category,
                        subcategory=subcategory,
                        unit=unit,
                        coming_soon=True,
                        reason=f"Failed to initialize: {type(e).__name__}",
                        error=str(e)
                    )
                    self.current_context = context
                    self.show_coming_soon(f"{category} {subcategory or ''} {unit or ''}".strip())
                    return context
            
            self.show_frame(frame_key)
            # Update window title with current context
            self.set_window_title()
            return context
        else:
            # FAILURE: No module found → Coming Soon
            context = create_context(
                category=category,
                subcategory=subcategory,
                unit=unit,
                coming_soon=True,
                reason="No implementation found"
            )
            print(f"[CONTEXT] ✗ {context}")
            self.current_context = context
            self.show_coming_soon(f"{category} {subcategory or ''} {unit or ''}".strip())
            return context


    def _animate_fade_out(self, frame):
        """Fade out animation"""
        if not hasattr(frame, 'winfo_exists') or not frame.winfo_exists():
            return
        try:
            frame.place_forget()
        except Exception:
            pass

    def _animate_fade_in(self, frame):
        """Fade in animation with smooth transition"""
        if not hasattr(frame, 'winfo_exists') or not frame.winfo_exists():
            return
        try:
            # Update the frame immediately to make it visible
            frame.update_idletasks()
        except Exception:
            pass

    def _toggle_fullscreen(self, event=None):
        try:
            entering = not getattr(self, "_is_fullscreen", False)
            if entering:
                # save current geometry to restore later
                try:
                    self._previous_geometry = self.root.geometry()
                except Exception:
                    self._previous_geometry = None
            self._is_fullscreen = entering
            self.root.attributes("-fullscreen", entering)
            if not entering:
                # restore previous geometry if available
                try:
                    if self._previous_geometry:
                        # make sure fullscreen flag is off first
                        self.root.attributes("-fullscreen", False)
                        self.root.geometry(self._previous_geometry)
                except Exception:
                    pass
        except Exception:
            pass

    def go_back(self, page_name):
        self.show_frame(page_name)

    def get_current_frame_name(self):
        for name, frame in self.frames.items():
            try:
                if frame.winfo_viewable():
                    return name
            except:
                continue
        return None

    def show_home(self):
        self.show_frame("HomePage")

    def show_transaction_window(self, details, main_app, return_to=None):
        if "TransactionWindow" in self.frames:
            try:
                self.frames["TransactionWindow"].destroy()
            except Exception:
                pass
        if not return_to:
            return_to = self.get_current_frame_name()

        # Determine TransactionWindow class dynamically from the caller's module
        TransactionCls = None
        try:
            if main_app is not None and hasattr(main_app, '__module__'):
                mod_base = main_app.__module__.rsplit('.', 1)[0]
                try:
                    tw_mod = importlib.import_module(f"{mod_base}.gui_transaction_window")
                    TransactionCls = getattr(tw_mod, 'TransactionWindow', None)
                except Exception:
                    pass
        except Exception:
            pass

        # Fallback to oilseals gui transaction window
        if TransactionCls is None:
            try:
                tw_mod = importlib.import_module('oilseals.gui.gui_transaction_window')
                TransactionCls = getattr(tw_mod, 'TransactionWindow', None)
            except Exception:
                TransactionCls = None

        if TransactionCls is None:
            # Can't find a TransactionWindow implementation
            self.show_coming_soon("Transactions")
            return

        frame = TransactionCls(self.container, details, controller=self, return_to=return_to)
        self.frames["TransactionWindow"] = frame
        frame.place(x=0, y=0, relwidth=1, relheight=1)
        frame.lift()
        # Ensure frame is rendered, then load data
        try:
            frame.update_idletasks()
            if hasattr(frame, 'set_details'):
                frame.set_details(details, main_app)
        except Exception:
            pass

    def show_coming_soon(self, category_name):
        frame_name = f"{category_name}ComingSoon"
        if frame_name not in self.frames:
            frame = ComingSoonPage(self.container, self, category_name, return_to="HomePage")
            self.frames[frame_name] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.show_frame(frame_name)