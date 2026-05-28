# Task P2-03: Integrate UpdateChecker into `main.py` Bootstrap

> **Phase**: 2 — UI Integration | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

This task wires the UpdateChecker into the application's startup sequence. After the main window is shown and the API connection attempt completes (or times out), the update checker runs in the background to check for available updates.

The check must be non-blocking and happen after the existing loading screen → main window transition to avoid slowing down the perceived startup time.

### Architectural Intent

- **After startup**: Update check runs AFTER the main window is visible and functional
- **Non-blocking**: Uses QThread (via UpdateChecker) — never freezes the UI
- **Graceful failure**: If the check fails, the app continues normally with zero user impact
- **Single entry point**: UpdateChecker is created in `main.py` and connected to `FramelessCamplifeLoader` via signals

---

## Affected Files

### Files to Modify

| File | Change | Lines Affected |
|------|--------|----------------|
| `main.py` | Add UpdateChecker initialization after app startup | ~10 new lines after line 50 |

---

## Dependencies & Prerequisites

- **P1-02**: `update_checker.py` must be implemented
- **P2-01**: Update notification widget must exist in `main_window.py`

---

## Implementation Details

Add to `main.py` after the connection handling section (around line 50):

```python
from src.update.update_checker import UpdateChecker

# After window.show() is called (inside on_connection_attempt_finished):
def start_update_check():
    """Run update check in background after startup completes."""
    update_checker = UpdateChecker()
    update_checker.check_complete.connect(window.on_update_check_result)
    update_checker.status_msg.connect(lambda msg: window.update_status(msg, 3000))
    update_checker.start()
    # Keep reference to prevent garbage collection
    window._update_checker = update_checker

# Trigger update check 2 seconds after main window is shown
QTimer.singleShot(2000, start_update_check)
```

**Key point**: The 2-second delay ensures the main window is fully visible and the loading screen has closed before the update check begins. This prevents the update check from interfering with the API connection flow.

---

## Validation Requirements

1. App starts normally with update check running silently in background
2. If update is available, notification banner appears after ~3-5 seconds
3. If no update, nothing visible happens (brief status bar message auto-dismisses)
4. If network fails, nothing visible happens (logged silently)
5. Existing startup flow (loading screen → main window → API connect) unchanged

---

## Expected Outcomes

- Update check runs automatically on every app launch (respecting 24-hour cache interval)
- Users see update notifications without any manual action
- Zero impact on startup performance or existing functionality

---

## Reasoning

**Why 2-second delay?** The loading screen transition and API connection attempt happen in the first 1-2 seconds. Starting the update check after this avoids competing network requests and ensures the UI is responsive before the check begins. The check itself runs on a separate thread, so the actual timing has minimal impact.

**Why keep the reference on `window`?** Python's garbage collector would destroy the QThread object if no reference exists, causing a crash. Storing it as `window._update_checker` keeps it alive for the duration of the application.
