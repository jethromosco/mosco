# Copilot Instructions for MOSCO Inventory (local AI agents)

Purpose
- Help AI agents become productive quickly when editing or extending this CustomTkinter-based inventory app.

Quick start (how devs run the app)
- Run from repository root:

```bash
python main.py
```
- Important dependency: `customtkinter` (install via `pip install customtkinter`). The app uses Python's builtin `sqlite3` for persistence.

Big picture (what to read first)
- Entry: [main.py](main.py#L1-L20) — sets theme and constructs `AppController`.
- App orchestration: [app_controller.py](app_controller.py#L1-L120) — maintains frames, dynamic category imports, and navigation.
- Example category: `oilseals/` — UI lives under `oilseals/gui/` and low-level helpers under `oilseals/ui/` (see [oilseals/gui/gui_mm.py](oilseals/gui/gui_mm.py#L1-L80) for an example `InventoryApp`).
- Database: [oilseals/database.py](oilseals/database.py#L1-L40) — DB path is relative to the package (look for `DATA_DIR` / `inventory.db`).

Project-specific patterns and conventions
- UI framework: uses `customtkinter` + `PIL` for images; theme values are centralized in `theme.py` and widgets subscribe via `theme.subscribe()`.
- Frame-based app: `AppController` manages named frames (HomePage, CategoryPage, InventoryApp, TransactionWindow). New pages should be added to `self.frames` and use `place()` for stacking.
- Dynamic import convention: `AppController.show_inventory_for()` constructs module paths using category words — category modules should expose an `InventoryApp` class. When adding a new category, mirror folder/module naming used in `oilseals/`.
- Admin & transactions: Admin panels and transaction windows are implemented as separate frames (see `AdminPanel` and `TransactionWindow` usage in `oilseals/gui/*`). Follow the same class names/signatures when creating new panels.
- UI placement: some elements are absolutely positioned (logo, back button, admin button) and rely on `on_window_resize()` to reflow — preserve that pattern when refactoring header/footer code.

Data access
- Database connections are made via helper functions (e.g., `connect_db()` in `oilseals/database.py`) which use a package-relative `DATA_DIR`. If you move DB files, update those helpers.

Developer workflows and gotchas
- No `requirements.txt` present; before running locally, ensure `customtkinter` and `pillow` are installed.
- Run with the workspace root as CWD so relative paths to `icons/`, `photos/`, and package `data/` resolve correctly.
- Many TODOs and UI comments are embedded in [main.py](main.py#L1-L200); consult them for current pain points and expected refactors.

How to extend
- To add a category: create a folder like `newcat/`, add `newcat/gui/gui_<sub>.py` that defines `InventoryApp`, and register any mapping in `CATEGORY_FOLDER_MAP` in `app_controller.py` if the name-to-folder mapping is nonstandard.
- Follow `oilseals/gui/gui_mm.py` for keyboard bindings, theme subscriptions, and search field patterns (`search_vars`, trace handlers).

Where to look next (key files)
- [app_controller.py](app_controller.py#L1-L120)
- [main.py](main.py#L1-L40)
- [oilseals/gui/gui_mm.py](oilseals/gui/gui_mm.py#L1-L80)
- [oilseals/database.py](oilseals/database.py#L1-L40)
- [oilseals/ui/mm.py](oilseals/ui/mm.py#L1-L120) — UI helpers for conversions/validation

If anything here is unclear or you'd like more details (run targets, missing requirements, or a short onboarding checklist), tell me which section to expand and I will iterate.
