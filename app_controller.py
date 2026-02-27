import customtkinter as ctk
import importlib
import os
import sqlite3
from typing import Optional
from theme import theme
from home_page import HomePage, CategoryPage, ComingSoonPage
from inventory_context import InventoryContext, create_context, INVALID_CONTEXT
from debug import DEBUG_MODE
from app_context import get_app_context


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
        if DEBUG_MODE:
            print(f"[CONTROLLER-INIT] AppController initializing with root id={id(root)}")
            print(f"[CONTROLLER-INIT] root type={type(root).__name__}, exists={root.winfo_exists()}")
        
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
        
        # Setup debug hotkey (Ctrl+Shift+T) to print context state
        try:
            self.root.bind("<Control-Shift-T>", lambda e: self._print_debug_context())
        except Exception:
            pass

        # Setup global mouse button bindings for back/forward navigation (Windows only)
        self._setup_global_mouse_bindings()

        # Create container frame using CustomTkinter
        self.container = ctk.CTkFrame(root, fg_color=theme.get("bg"))
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        # Current selected inventory context (single source of truth)
        self.current_category = None
        self.current_subcategory = None
        self.current_unit = None
        self.current_db_module = None
        
        if DEBUG_MODE:
            print(f"[CONTROLLER-INIT] AppController initialization complete")
        self.current_context = INVALID_CONTEXT  # The authoritative context object
        
        # Dynamic window title tracking
        self.current_section = None  # PRODUCTS, TRANSACTIONS, ADMIN, etc.
        self.current_action = None   # ADD PRODUCT, EDIT PRODUCT, DELETE PRODUCT, etc.
        
        # Admin Panel singleton - only one instance allowed
        self.admin_panel_instance = None

        # Create and add home page
        home_page = HomePage(self.container, controller=self)
        self.frames["HomePage"] = home_page
        home_page.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_frame("HomePage")

    def _setup_app_context_for_category(
        self,
        category: str,
        subcategory: Optional[str] = None,
        unit: Optional[str] = None,
        base_pkg: str = ""
    ) -> bool:
        """
        Setup AppContext (database paths, photo folder) for a category.
        
        This should be called after InventoryApp is successfully loaded
        to configure the centralized state.
        
        Args:
            category: Category name
            subcategory: Optional subcategory
            unit: Optional unit (MM/INCH)
            base_pkg: Base package path (e.g., 'oilseals', 'packingseals.monoseals')
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from typing import Optional
            
            if DEBUG_MODE:
                print(f"[CONTROLLER] Setting up AppContext for {category}")
            
            # Try to load database module to get DB path
            db_module = None
            db_path = ""
            data_dir = ""
            
            # Build database module path
            if base_pkg:
                sub_folder = (subcategory or '') and subcategory.replace(' ', '').lower()
                if sub_folder:
                    # Try packingseals.subcategory.database (e.g., packingseals.monoseals.database)
                    try:
                        db_module = importlib.import_module(f"{base_pkg}.{sub_folder}.database")
                        if DEBUG_MODE:
                            print(f"[CONTROLLER] Loaded db module: {base_pkg}.{sub_folder}.database")
                    except Exception:
                        pass
                
                if not db_module:
                    # Try base_pkg.database (e.g., oilseals.database)
                    try:
                        db_module = importlib.import_module(f"{base_pkg}.database")
                        if DEBUG_MODE:
                            print(f"[CONTROLLER] Loaded db module: {base_pkg}.database")
                    except Exception:
                        pass
            
            # Extract database paths from module
            if db_module:
                db_path = getattr(db_module, 'DB_PATH', "")
                data_dir = getattr(db_module, 'DATA_DIR', "")
                
                if DEBUG_MODE:
                    print(f"[CONTROLLER] DB_PATH: {db_path}")
                    print(f"[CONTROLLER] DATA_DIR: {data_dir}")
            
            # Determine photo folder
            photo_folder = ""
            if db_path:
                # Photos folder is typically at {category}/photos
                # E.g., oilseals/photos, packingseals/monoseals/photos
                try:
                    # Extract category folder from db_path
                    # db_path is like /path/to/mosco/oilseals/data/oilseals_mm_inventory.db
                    # We want /path/to/mosco/oilseals/photos
                    parts = db_path.replace('\\', '/').split('/')
                    
                    # Find 'data' in path and go up to get category root
                    try:
                        data_idx = parts.index('data')
                        if data_idx >= 1:
                            category_root = '/'.join(parts[:data_idx])
                            photo_folder = os.path.join(category_root, 'photos')
                    except (ValueError, IndexError):
                        pass
                    
                    if DEBUG_MODE:
                        print(f"[CONTROLLER] Photo folder: {photo_folder}")
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"[CONTROLLER] Error deriving photo folder: {e}")
            
            # Update AppContext with all information
            context = get_app_context()
            context.set_active_category(category, subcategory, unit)
            
            if db_path:
                try:
                    # Import sqlite3 and create connection
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    context.set_database(db_path, conn)
                except Exception as e:
                    print(f"[ERROR-CONTEXT] Failed to connect to database: {e}")
                    return False
            
            if photo_folder:
                context.set_photo_folder(photo_folder)
            
            if DEBUG_MODE:
                context._log_state("AppContext updated for category")
            
            return True
        
        except Exception as e:
            print(f"[ERROR-CONTEXT] Error setting up AppContext: {e}")
            return False

    def add_category_page(self, name, sub_data, return_to="HomePage"):
        frame = CategoryPage(self.container, self, name, sub_data, return_to=return_to)
        # Track the parent category for nested navigation
        frame.parent_category = self.current_category
        self.frames[name] = frame
        frame.place(x=0, y=0, relwidth=1, relheight=1)

    def _print_debug_context(self):
        """Print context state for debugging (triggered by Ctrl+Shift+T)."""
        try:
            app_context = get_app_context()
            current_frame = self.get_current_frame_name()
            
            print("\n" + "="*60)
            print("[DEBUG CONTEXT] Application State")
            print("="*60)
            print(f"Active Category    : {self.current_category or 'None'}")
            print(f"Active Subcategory : {self.current_subcategory or 'None'}")
            print(f"Active Unit        : {self.current_unit or 'None'}")
            print(f"DB Path            : {app_context.db_path or 'Not configured'}")
            print(f"Photo Folder       : {app_context.photo_folder or 'Not configured'}")
            print(f"Active Window      : {current_frame or 'HomePage'}")
            print(f"Current Section    : {self.current_section or 'None'}")
            print(f"Current Action     : {self.current_action or 'None'}")
            print("="*60 + "\n")
        except Exception as e:
            print(f"[ERROR] Error printing debug context: {e}")

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
        if DEBUG_MODE:
            print(f"[FRAME-SHOW] show_frame({page_name}) called")
            print(f"[FRAME-SHOW] root children: {len(self.root.winfo_children())}")
        
        # Get ALL currently visible frames and find the topmost one
        # The topmost frame is the last one in iteration (most recently placed)
        viewable_frames = []
        for frame_name, frame in self.frames.items():
            try:
                if frame.winfo_viewable():
                    viewable_frames.append((frame_name, frame))
            except Exception:
                pass
        
        if DEBUG_MODE:
            print(f"[FRAME-SHOW] Current visible frames: {[name for name, _ in viewable_frames]}")
        
        # Hide current frame (the topmost/most recent one)
        if viewable_frames:
            current_frame_name, current_frame = viewable_frames[-1]
            try:
                if DEBUG_MODE:
                    print(f"[FRAME-SHOW] Hiding current frame: {current_frame_name}")
                current_frame.place_forget()
            except Exception as e:
                if DEBUG_MODE:
                    print(f"[FRAME-SHOW] Error hiding frame {current_frame_name}: {e}")
        else:
            current_frame = None
            if DEBUG_MODE:
                print(f"[FRAME-SHOW] No visible frame to hide")
        
        # Show the requested frame with fade-in
        if page_name in self.frames:
            frame = self.frames[page_name]
            try:
                if DEBUG_MODE:
                    print(f"[FRAME-SHOW] Placing frame {page_name}")
                
                # Ensure frame is placed before updating
                frame.place(x=0, y=0, relwidth=1, relheight=1)
                frame.lift()
                
                # CRITICAL: Call update_idletasks TWICE to ensure all widgets are realized
                # First call ensures widgets exist, second ensures they're properly laid out
                frame.update_idletasks()
                frame.update_idletasks()
                
                if DEBUG_MODE:
                    print(f"[FRAME-SHOW] Frame {page_name} placed, checking for on_frame_show")
                
                # Schedule frame's on_frame_show hook ONLY for InventoryApp frames
                # Call immediately (not delayed) to refresh content right away
                # Check: must have on_frame_show method AND be named InventoryApp
                if (hasattr(frame, 'on_frame_show') and callable(frame.on_frame_show) and 
                    frame.__class__.__name__ == 'InventoryApp'):
                    try:
                        if frame.winfo_exists():
                            if DEBUG_MODE:
                                print(f"[FRAME-SHOW] Calling on_frame_show for {page_name}")
                            frame.on_frame_show()
                    except Exception as e:
                        if DEBUG_MODE:
                            print(f"[FRAME-SHOW] Error in on_frame_show for {page_name}: {e}")
                        # If on_frame_show failed, try refresh_product_list directly as fallback
                        try:
                            if hasattr(frame, 'refresh_product_list'):
                                print(f"[FRAME] Fallback: calling refresh_product_list directly")
                                frame.refresh_product_list()
                        except Exception as e2:
                            print(f"[FRAME] Fallback refresh also failed: {e2}")
            except Exception as e:
                print(f"[FRAME] Error placing/showing frame {page_name}: {e}")
        
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
                    print(f"[CONTEXT] Found InventoryApp in {mod_path}")
                    break
                else:
                    print(f"[CONTEXT] No InventoryApp in {mod_path}")
            except Exception as e:
                print(f"[CONTEXT] Failed to import {mod_path}: {type(e).__name__}")
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
                        print(f"[CONTEXT] Found InventoryApp in fallback {mod_path}")
                        break
                except Exception as e:
                    print(f"[CONTEXT] Fallback failed {mod_path}: {type(e).__name__}")
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
            print(f"[CONTEXT] {context}")
            self.current_context = context
            
            # Load and show the InventoryApp
            frame_key = f"{category}::{subcategory or ''}::{unit or ''}"
            if frame_key not in self.frames:
                try:
                    frame = loaded_module(self.container, controller=self)
                    
                    # CRITICAL: Set return_to to current parent frame
                    # This ensures back button navigates step-by-step, not directly to HomePage
                    current_frame_name = self.get_current_frame_name()
                    if current_frame_name and current_frame_name != "HomePage":
                        frame.return_to = current_frame_name
                    
                    self.frames[frame_key] = frame
                    frame.place(x=0, y=0, relwidth=1, relheight=1)
                    
                    # CRITICAL: Setup AppContext with database and photo paths
                    # This ensures all modules use centralized state for db and photos
                    self._setup_app_context_for_category(
                        category=category,
                        subcategory=subcategory,
                        unit=unit,
                        base_pkg=base_pkg
                    )
                    
                    print(f"[CONTEXT] Created and placed InventoryApp frame (return_to={frame.return_to})")
                except Exception as e:
                    print(f"[CONTEXT] Failed to create InventoryApp: {e}")
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
            print(f"[CONTEXT] {context}")
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

    def _setup_global_mouse_bindings(self):
        """Setup global mouse back button binding for Windows navigation.
        Button-4 = Windows back button (invokes the visible back button widget).
        
        This binding finds the currently visible frame and invokes its back_btn
        widget directly, simulating a physical click on the back button.
        """
        try:
            self.root.bind_all("<Button-4>", self._handle_global_mouse_back)
        except Exception:
            # Side buttons may not be supported on this platform
            pass

    def _handle_global_mouse_back(self, event=None):
        """Handle mouse back button (Button-4): invoke the back button of topmost visible frame.
        
        This finds the most recently placed/visible frame and invokes its back button widget
        directly - equivalent to physically clicking the back button. Ensures we only invoke
        the back button of the topmost (foreground) frame.
        """
        try:
            # Find the topmost visible frame by checking in reverse insertion order
            # (later frames are on top)
            topmost_frame = None
            topmost_name = None
            
            # Iterate through frames to find all viewable ones
            viewable_frames = []
            for frame_name, frame in self.frames.items():
                try:
                    if frame.winfo_viewable():
                        viewable_frames.append((frame_name, frame))
                except Exception:
                    pass
            
            # The last one in the list is the topmost (since TransactionWindow, ComingSoon,
            # and InventoryApp frames are added/placed in order, later ones are on top)
            if viewable_frames:
                topmost_name, topmost_frame = viewable_frames[-1]
            
            # If we found a viewable frame, invoke its back button
            if topmost_frame and topmost_name:
                if hasattr(topmost_frame, 'back_btn'):
                    back_btn = getattr(topmost_frame, 'back_btn', None)
                    if back_btn is not None and back_btn.winfo_exists():
                        # Invoke the button directly - triggers its command callback
                        back_btn.invoke()
                        return "break"
                # If no back button found, try to navigate back to home
                if topmost_name != "HomePage":
                    self.go_back("HomePage")
                return "break"
        except Exception:
            pass

    def go_back(self, page_name):
        if DEBUG_MODE:
            print(f"[FRAME-BACK] go_back({page_name}) called")
            print(f"[FRAME-BACK] root children: {len(self.root.winfo_children())}")
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
        if DEBUG_MODE:
            print(f"[TRANS-SHOW] show_transaction_window() called")
            print(f"[TRANS-SHOW] product={details.get('type_name', 'unknown')} {details.get('id', 'unknown')}")
            print(f"[TRANS-SHOW] return_to={return_to}")
        
        # CRITICAL FIX: Preserve return_to from old TransactionWindow before destroying it
        old_return_to = None
        if "TransactionWindow" in self.frames:
            try:
                old_frame = self.frames["TransactionWindow"]
                # PRESERVE the return_to value before destroying
                if hasattr(old_frame, 'return_to') and old_frame.return_to:
                    old_return_to = old_frame.return_to
                    if DEBUG_MODE:
                        print(f"[TRANS-SHOW] Preserving old return_to={old_return_to}")
                
                if DEBUG_MODE:
                    print(f"[TRANS-SHOW] Destroying old TransactionWindow")
                # CRITICAL: Cancel any pending admin close callback before destroying frame
                if hasattr(old_frame, '_admin_close_callback_id') and old_frame._admin_close_callback_id is not None:
                    try:
                        old_frame.after_cancel(old_frame._admin_close_callback_id)
                        if DEBUG_MODE:
                            print("[TRANS-SHOW] Cancelled pending callback in old TransactionWindow")
                        old_frame._admin_close_callback_id = None
                    except Exception:
                        pass
                old_frame.destroy()
            except Exception as e:
                if DEBUG_MODE:
                    print(f"[TRANS-SHOW] Error destroying old TransactionWindow: {e}")
                pass
        
        # CRITICAL FIX: Never allow return_to to be None
        if not return_to:
            # Try to use preserved return_to from old window first
            if old_return_to:
                return_to = old_return_to
                if DEBUG_MODE:
                    print(f"[TRANS-SHOW] Using preserved return_to={return_to}")
            else:
                # Fall back to current frame
                return_to = self.get_current_frame_name()
                if DEBUG_MODE:
                    print(f"[TRANS-SHOW] Using current frame return_to={return_to}")
        
        # SAFETY CHECK: Ensure return_to is valid
        if not return_to or return_to == "TransactionWindow":
            return_to = "HomePage"
            if DEBUG_MODE:
                print(f"[TRANS-SHOW] WARNING: return_to was invalid, using HomePage as fallback")

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

        # CRITICAL: Hide current frame before showing transaction window
        # This ensures only TransactionWindow is winfo_viewable(), preventing mouse button
        # handler from invoking the wrong frame's back button
        current_frame = None
        for frame in self.frames.values():
            try:
                if frame.winfo_viewable() and frame != self.frames.get("TransactionWindow"):
                    current_frame = frame
                    break
            except Exception:
                pass
        
        if current_frame:
            current_frame.place_forget()

        frame = TransactionCls(self.container, details, controller=self, return_to=return_to)
        self.frames["TransactionWindow"] = frame
        frame.place(x=0, y=0, relwidth=1, relheight=1)
        frame.lift()
        
        # Ensure frame is fully rendered before loading data
        # Use multiple update cycles to ensure all widgets are created and visible
        try:
            frame.update_idletasks()
            frame.update_idletasks()  # Double update to ensure full render
            
            # Verify the tree widget exists before loading data
            if hasattr(frame, 'tree') and frame.tree.winfo_exists():
                # Load data after ensuring widget exists
                if hasattr(frame, 'set_details'):
                    frame.set_details(details, main_app)
            else:
                # If tree doesn't exist, wait a bit longer and try again
                self.root.after(50, lambda: self._load_transaction_data_delayed(frame, details, main_app))
        except Exception as e:
            print(f"[TRANSACTION] Error loading transaction details: {e}")
            # Try again with delay
            self.root.after(100, lambda: self._load_transaction_data_delayed(frame, details, main_app))

    def show_coming_soon(self, category_name):
        frame_name = f"{category_name}ComingSoon"
        if frame_name not in self.frames:
            # Set return_to to current frame for consistency with other navigation
            current_frame_name = self.get_current_frame_name()
            return_target = current_frame_name if current_frame_name else "HomePage"
            frame = ComingSoonPage(self.container, self, category_name, return_to=return_target)
            self.frames[frame_name] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.show_frame(frame_name)

    def is_admin_panel_open(self):
        """Check if Admin Panel is currently open and valid.
        
        Returns:
            True if Admin Panel exists and window is valid
            False otherwise
        """
        if self.admin_panel_instance is None:
            return False
        
        try:
            if self.admin_panel_instance.win.winfo_exists():
                return True
            else:
                # Window was destroyed but reference not cleared
                self.admin_panel_instance = None
                return False
        except Exception:
            # Invalid reference
            self.admin_panel_instance = None
            return False

    def show_admin_panel(self, parent_app, on_close_callback=None):
        """Show Admin Panel with singleton pattern - only one instance allowed.
        
        If Admin Panel already open:
        - Restore if minimized
        - Bring to front
        - Give focus
        
        If not open:
        - Create new AdminPanel instance
        - Store reference for singleton check
        
        Args:
            parent_app: The calling frame/app (main_app parameter)
            on_close_callback: Optional callback when Admin Panel closes
        """
        # If admin panel is already open, bring it to front
        if self.admin_panel_instance is not None:
            try:
                # Check if window still exists
                if self.admin_panel_instance.win.winfo_exists():
                    # Ensure window is normal state (restore if minimized)
                    try:
                        if self.admin_panel_instance.win.state() == 'iconic':
                            self.admin_panel_instance.win.state('normal')
                    except Exception:
                        pass
                    
                    # Bring to front
                    self.admin_panel_instance.win.lift()
                    
                    # Make topmost briefly to ensure it comes to front over other windows
                    self.admin_panel_instance.win.attributes('-topmost', True)
                    self.root.after(200, lambda: self.admin_panel_instance.win.attributes('-topmost', False) if self.admin_panel_instance.win.winfo_exists() else None)
                    
                    # Give focus
                    self.admin_panel_instance.win.focus_force()
                    return
                else:
                    # Window was destroyed but reference not cleared
                    self.admin_panel_instance = None
            except Exception as e:
                # Window or reference is bad, clear it and create new one
                self.admin_panel_instance = None
        
        # Create new AdminPanel instance
        try:
            # Import AdminPanel from the current module context
            # This returns the correct AdminPanel class for the current category
            AdminPanelClass = None
            
            # Try to get AdminPanel from the same module as parent_app
            if hasattr(parent_app, '__module__'):
                try:
                    mod_base = parent_app.__module__.rsplit('.', 1)[0]
                    products_mod = importlib.import_module(f"{mod_base}.gui_products")
                    AdminPanelClass = getattr(products_mod, 'AdminPanel', None)
                except Exception:
                    pass
            
            # Fallback to oilseals AdminPanel
            if AdminPanelClass is None:
                try:
                    products_mod = importlib.import_module('oilseals.gui.gui_products')
                    AdminPanelClass = getattr(products_mod, 'AdminPanel', None)
                except Exception:
                    pass
            
            if AdminPanelClass is None:
                print("[ADMIN] Failed to load AdminPanel class")
                return
            
            # Create the instance and store reference
            admin_panel = AdminPanelClass(
                self.root,
                parent_app,
                self,
                on_close_callback=on_close_callback
            )
            
            # Store reference for singleton check
            self.admin_panel_instance = admin_panel
            
        except Exception as e:
            print(f"[ADMIN] Failed to create AdminPanel: {e}")
    
    def _load_transaction_data_delayed(self, frame, details, main_app):
        """Load transaction data with retry logic if widget not ready"""
        try:
            if hasattr(frame, 'tree') and frame.tree.winfo_exists():
                if hasattr(frame, 'set_details'):
                    frame.set_details(details, main_app)
            else:
                # Still not ready, try one more time
                self.root.after(50, lambda: self._load_transaction_data_delayed(frame, details, main_app))
        except Exception as e:
            print(f"[TRANSACTION] Failed to load transaction data: {e}")

    def _clear_admin_panel(self):
        """Clear AdminPanel reference when it closes.
        
        Called by AdminPanel.on_closing() to allow re-opening.
        """
        self.admin_panel_instance = None