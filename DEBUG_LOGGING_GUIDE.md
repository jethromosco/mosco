# Debug Logging System

## Overview
Comprehensive debug logging has been added to diagnose the inconsistent "grey window" issue. All logging is controlled by a global `DEBUG_MODE` toggle in `main.py`.

## Enabling/Disabling Debug Mode

Edit `main.py`:
```python
# Global debug mode toggle - Set to False to disable all debug prints
DEBUG_MODE = True  # Set to False to disable all logging
```

## Debug Logging Coverage

### 1. **main.py** - Application Entry Point
- Root Tk instance creation and ID tracking
- AppController initialization
- Mainloop start/exit

**Log Examples:**
```
[DEBUG] DEBUG_MODE enabled - all lifecycle events will be logged
[DEBUG] Creating root Tk instance at id=<address>
[DEBUG] Root created: type=CTk, id=<address>
[DEBUG] AppController created. Starting mainloop...
```

---

### 2. **gui_mm.py** - Main InventoryApp Frame
#### Initialization Logging
- Frame creation with IDs
- Root widget validation
- Widget count tracking
- Entire initialization sequence

**Log Examples:**
```
[MM-INIT] Initializing InventoryApp (id=<address>)
[MM-INIT] root=CTk (id=<address>)
[MM-INIT] root.winfo_exists()=1
[MM-INIT] root children count=1
```

#### Widget Creation Logging
- Header, search, and table section creation
- Step-by-step widget build process

**Log Examples:**
```
[MM-WIDGETS] create_widgets() called
[MM-WIDGETS] Creating header section
[MM-WIDGETS] Creating search section
[MM-WIDGETS] Creating table section
[MM-WIDGETS] create_widgets() complete
```

#### Back Button Logic
- Back button click detection
- Navigation state tracking
- Widget existence validation

**Log Examples:**
```
[MM-BACK] Back button pressed, return_to=OIL SEALS::::MM
[MM-BACK] MM exists: 1
[MM-BACK] MM viewable: 1
[MM-BACK] root exists: 1
[MM-BACK] root children: 1
[MM-BACK] Calling controller.go_back(OIL SEALS::::MM)
```

#### Product List Refresh
- Refresh call tracking
- Frame/widget state validation
- **Grey window detection** ⚠️

**Log Examples:**
```
[MM-REFRESH] refresh_product_list() called
[MM-REFRESH] MM exists: 1
[MM-REFRESH] MM viewable: 1
[MM-REFRESH] MM geometry: 1920x1057+0+0
[MM-REFRESH] root exists: 1
[MM-REFRESH] root children count: 1
[MM-REFRESH] Has tree: 1
[MM-REFRESH] Tree exists: 1
```

**IMPORTANT - Grey Window Detection:**
```
[ERROR] GREY WINDOW STATE DETECTED: root has 0 children!
```
If you see this message, capture the terminal output and send it to diagnose the issue.

#### Frame Visibility
- Frame show/hide lifecycle
- Content packing status
- Deferred refresh mechanism

**Log Examples:**
```
[MM-SHOW] on_frame_show() CALLED - MM is now ACTIVE
[MM-SHOW] Frame state:
  MM exists: 1
  MM viewable: 1
  MM geometry: 1920x1057+0+0
  root children: 1
[MM-SHOW] main_content exists
[MM-SHOW] main_content viewable: 1
[MM-SHOW] main_content packed and lifted
[MM-SHOW] DEFERRED REFRESH: Admin made changes, refreshing now that MM is visible
```

---

### 3. **gui_transaction_window.py** - Transaction Window
#### Initialization Logging
- TransactionWindow creation
- Product detail tracking
- Return target recording

**Log Examples:**
```
[TRANS-INIT] TransactionWindow initializing (id=<address>)
[TRANS-INIT] details=Oil Seal 12, return_to=OIL SEALS::::MM
[TRANS-INIT] Building UI...
[TRANS-INIT] TransactionWindow initialization complete
```

#### Admin Callback Logging
- Admin close callback execution
- Main frame state checking
- Refresh decision logic

**Log Examples:**
```
[ADMIN-CALLBACK] Executing admin close callback
[ADMIN-CALLBACK] TransactionWindow exists: 1
[ADMIN-CALLBACK] MM state: exists=1, viewable=1
[ADMIN-CALLBACK] root children: 1
[ADMIN-CALLBACK] Calling MM refresh_product_list()
[ADMIN-CALLBACK] MM is viewable, refreshing now
[ADMIN-CALLBACK] MM refresh completed
```

**Deferred Refresh Example:**
```
[ADMIN-CALLBACK] MM not viewable, deferring refresh
```

---

### 4. **app_controller.py** - Navigation Controller
#### Controller Initialization
- Root widget tracking
- Frame container setup
- Initial state

**Log Examples:**
```
[CONTROLLER-INIT] AppController initializing with root id=<address>
[CONTROLLER-INIT] root type=CTk, exists=1
[CONTROLLER-INIT] AppController initialization complete
```

#### Frame Showing/Hiding
- Frame visibility management
- Widget placement tracking
- **Root children counting** ⚠️
- on_frame_show callback execution

**Log Examples:**
```
[FRAME-SHOW] show_frame(OIL SEALS::::MM) called
[FRAME-SHOW] root children: 1
[FRAME-SHOW] Current visible frames: ['HomePage']
[FRAME-SHOW] Hiding current frame: HomePage
[FRAME-SHOW] Placing frame OIL SEALS::::MM
[FRAME-SHOW] Frame OIL SEALS::::MM placed, checking for on_frame_show
[FRAME-SHOW] Calling on_frame_show for OIL SEALS::::MM
```

#### Back Navigation
- Back button handler tracking
- Frame transition logging
- Root state after navigation

**Log Examples:**
```
[FRAME-BACK] go_back(OIL SEALS::::MM) called
[FRAME-BACK] root children: 1
```

#### Transaction Window Opening
- Product selection tracking
- Return target recording
- Window lifecycle

**Log Examples:**
```
[TRANS-SHOW] show_transaction_window() called
[TRANS-SHOW] product=Oil Seal 12
[TRANS-SHOW] return_to=OIL SEALS::::MM
[TRANS-SHOW] Destroying old TransactionWindow
```

---

## Key Metrics to Watch

### Root Widget Count
```
[MM-REFRESH] root children count: 1
```
- **Expected:** 1 (the container frame)
- **Problem:** 0 = GREY WINDOW STATE
- **Problem:** >1 = Multiple containers (indicates lifecycle issue)

### Frame Existence
```
[MM-SHOW] MM exists: 1
[MM-BACK] MM exists: 1
```
- **Expected:** Always 1 (true)
- **Problem:** 0 = Frame was destroyed unexpectedly

### Frame Viewability
```
[MM-SHOW] MM viewable: 1
[ADMIN-CALLBACK] MM state: exists=1, viewable=0
```
- **Expected:** 1 when navigating to frame, 0 when hidden
- **Problem:** 0 when it should be 1 = Hidden frame

---

## How to Diagnose the Grey Window Issue

### Step 1: Enable Debug Mode
Set `DEBUG_MODE = True` in `main.py`

### Step 2: Reproduce the Issue
1. Open application
2. Navigate to a category (e.g., OIL SEALS)
3. Open a transaction window
4. Open admin panel
5. Edit a transaction in admin panel → transactions tab
6. Close admin panel
7. Click back or use mouse button 4
8. **Grey window appears** → Capture terminal output

### Step 3: Look for These Error Signs
```
[ERROR] GREY WINDOW STATE DETECTED: root has 0 children!
[MM-REFRESH] Frame no longer exists, skipping refresh
[ERROR] Root destroyed unexpectedly
[MM-REFRESH] Tree widget no longer exists
```

### Step 4: Trace the Sequence
Look at the logs in chronological order:
1. Where did the refresh call originate? (admin callback, navigation, etc.)
2. What was the state of root/MM/tree before refresh?
3. When did the container disappear?
4. Did any frame get destroyed unexpectedly?

### Step 5: Send Terminal Output
When grey window happens, copy ALL terminal output from start to grey window event and send it. Include:
- Initial app startup logs
- Navigation sequence logs
- Admin panel lifecycle logs
- Back button click logs
- Any `[ERROR]` messages

---

## Test Scenarios

### ✓ Normal Flow (Should work without errors)
```
[MM-INIT] Initializing InventoryApp
[MM-SHOW] Frame state: MM exists=1, MM viewable=1, root children=1
[MM-REFRESH] root children count: 1
[MM-BACK] root children: 1
```

### ✓ Admin Edit Flow (Deferred refresh)
```
[ADMIN-CALLBACK] MM not viewable, deferring refresh
[MM-SHOW] DEFERRED REFRESH: Admin made changes
[MM-REFRESH] root children count: 1
```

### ✗ Grey Window Flow (Problem)
```
[ADMIN-CALLBACK] MM not viewable, deferring refresh
[FRAME-SHOW] root children: 0  ⚠️
[ERROR] GREY WINDOW STATE DETECTED: root has 0 children!
```

---

## Performance Note

When `DEBUG_MODE = False`, all logging is skipped with zero overhead.

```python
if DEBUG_MODE:
    print(...)  # Only executes when DEBUG_MODE=True
```

This means you can leave the code in place and toggle logging without any performance impact.

---

## Code Changes Summary

| File | Changes |
|------|---------|
| `main.py` | Added DEBUG_MODE toggle, root/controller tracking |
| `gui_mm.py` | Added logging to init, widgets, refresh, back button, frame show |
| `gui_transaction_window.py` | Added logging to init, admin callback |
| `app_controller.py` | Added logging to init, show_frame, go_back, show_transaction_window |

All changes are **non-breaking** and maintain the same behavior. No logic was changed, only diagnostic logging added.

---

## Next Steps

1. Run the application with `DEBUG_MODE = True`
2. Perform the actions that trigger the grey window
3. When grey window appears, capture the complete terminal output
4. Look for:
   - Any `[ERROR]` messages
   - Root children going from 1 to 0
   - Frames being destroyed unexpectedly
   - Refresh failures
5. Send the terminal output for analysis

The logging will help pinpoint exactly where and when the grey window state is triggered.
