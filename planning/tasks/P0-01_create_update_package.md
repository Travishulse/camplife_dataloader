# Task P0-01: Create `src/update/` Package with Scaffolding

> **Phase**: 0 — Foundation | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The Camplife DataLoader (v1.1.0) currently has three source packages: `src/api/`, `src/core/`, and `src/gui/`. The update system needs its own isolated package — `src/update/` — to encapsulate all update-related logic without modifying or interacting with existing modules.

This task creates the package skeleton with configuration constants and placeholder modules. It is the foundation for all subsequent update system tasks.

### Architectural Intent

- **Isolation**: All update logic lives in one package. No existing module needs to import from `src/update/` until Phase 2 (UI integration).
- **Consistency**: Follow the existing project's file organization pattern (see `docs/update-protocol.md` File Organization Rules).
- **No side effects**: This task adds files only — zero modifications to any existing file.

---

## Affected Files

### New Files to Create

| File | Purpose |
|------|---------|
| `src/update/__init__.py` | Package marker (consistent with `src/api/__init__.py` pattern) |
| `src/update/update_config.py` | Constants: URLs, paths, intervals, protected files list, channels |
| `src/update/version_utils.py` | Placeholder — implemented in P0-09 |
| `src/update/integrity.py` | Placeholder — implemented in P1-01 |
| `src/update/update_checker.py` | Placeholder — implemented in P1-02 |
| `src/update/update_manager.py` | Placeholder — implemented in P1-03 |
| `src/update/rollback_manager.py` | Placeholder — implemented in P1-04 |

### Existing Files — NO Modifications

No existing files are modified in this task.

---

## Dependencies & Prerequisites

- None — this is the first task in Phase 0.
- Requires: Python 3.9+ installed, project directory accessible.

---

## Implementation Details

### Step 1: Create `src/update/__init__.py`

```python
# src/update/__init__.py
"""Update system for Camplife DataLoader."""
```

Follow the exact pattern of existing `__init__.py` files:
- `src/__init__.py` contains `"# src package marker"`
- `src/api/__init__.py` contains `"# api package marker"`

### Step 2: Create `src/update/update_config.py`

This file must contain all constants needed by the update system. Reference `config.py` for the `APP_DIR` detection pattern.

```python
"""
Update system configuration constants.

All URLs, paths, intervals, and protected file lists for the update system.
This is the single source of truth for update system configuration.
"""
import os
from config import APP_DIR

# --- Remote Endpoints ---
# Primary: GitHub Releases API (rate-limited: 60 req/hr unauthenticated)
# Fallback: Firebase Hosting CDN (no rate limit)
UPDATE_CHECK_URL_PRIMARY = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
UPDATE_CHECK_URL_FALLBACK = "https://{project}.web.app/update-manifest.json"

# --- Local Paths ---
UPDATE_STAGING_DIR = os.path.join(APP_DIR, ".updates")
UPDATE_BACKUP_DIR = os.path.join(APP_DIR, ".backups")
UPDATE_STATE_FILE = os.path.join(APP_DIR, ".updates", "update_state.json")

# --- Behavior ---
UPDATE_CHECK_INTERVAL_HOURS = 24     # How often to check for updates on startup
UPDATE_DOWNLOAD_TIMEOUT_SECONDS = 300  # 5 minute timeout for archive downloads
UPDATE_CHECK_TIMEOUT_SECONDS = 5      # 5 second timeout for manifest fetch
HEALTH_CHECK_TIMEOUT_SECONDS = 10     # Time to wait before confirming update success
MAX_BACKUP_VERSIONS = 3               # Number of backup versions to retain

# --- Update Channels ---
UPDATE_CHANNEL = "stable"  # stable | beta | dev

# --- Protected Files (never modified by updates) ---
PROTECTED_FILES = [
    "config.json",         # Encrypted API credentials
    "cache.json",          # Cached resort/membership data
]

PROTECTED_DIRS = [
    "logs",                # Application log files
    ".backups",            # Backup archives (must never be deleted by updates)
    ".updates",            # Staging area (managed by update system only)
]

PROTECTED_PATTERNS = [
    "*.xlsx",              # Upload log files
]

# --- Required Files (post-update validation) ---
REQUIRED_FILES_AFTER_UPDATE = [
    "main.py",
    "config.py",
    "src/__init__.py",
    "src/api/client.py",
    "src/core/uploader.py",
    "src/gui/main_window.py",
]
```

**Important**: The `{owner}`, `{repo}`, and `{project}` placeholders are intentional — they will be replaced with actual values when the GitHub repository is created (Task P0-03).

### Step 3: Create Placeholder Modules

For `version_utils.py`, `integrity.py`, `update_checker.py`, `update_manager.py`, and `rollback_manager.py`, create minimal placeholder files:

```python
"""
[Module Name] — [One-line description].

This module will be implemented in Task [P0-XX/P1-XX].
"""
# Implementation pending — see planning/tasks/[task-file].md
```

---

## Validation Requirements

After completing this task, the following must be true:

1. **Directory exists**: `src/update/` directory is present with 7 Python files
2. **Imports work**: Running `python -c "from src.update import update_config"` succeeds without errors
3. **Constants accessible**: `update_config.UPDATE_STAGING_DIR` returns a valid path string
4. **No regressions**: All existing tests still pass:
   - `python -m pytest tests/test_security.py`
   - `python tests/test_app.py` (if Qt is available)
5. **Build works**: `build.bat` still produces a working executable (optional — PyInstaller may need `.spec` update in P0-07)

---

## Expected Outcomes

- `src/update/` package exists with 7 files
- All update system constants are defined in one place (`update_config.py`)
- Protected file list is established (critical for data safety)
- Placeholder modules are ready for implementation in subsequent tasks
- Zero impact on existing application functionality

---

## Testing Expectations

No new test file is needed for this task. Validation is done via:
- Import check: `python -c "from src.update.update_config import PROTECTED_FILES; print(PROTECTED_FILES)"`
- Regression check: Existing tests pass unchanged

---

## Reasoning

**Why a separate package instead of adding to `src/core/`?**

The update system is a cross-cutting concern that interacts with the build system, the network, the filesystem, and the GUI. Placing it in `src/core/` would blur the boundaries between "business logic" (uploading camplife data) and "application lifecycle management" (updating the application itself). A dedicated package makes the update system independently testable, removable, and understandable.

**Why define constants in `update_config.py` rather than `config.py`?**

`config.py` is the centralized configuration for the Camplife DataLoader's core functionality (VERSION, API URLs, paths). Mixing update system constants into it would violate the single-responsibility principle and create coupling between the update system and the core application. If the update system is ever removed, `config.py` should need zero changes.

**Why placeholder files instead of creating them empty?**

Placeholders with docstrings make the import chain valid immediately, allow other developers/agents to understand the intended purpose of each module, and prevent accidental "file not found" errors when setting up the development environment.
