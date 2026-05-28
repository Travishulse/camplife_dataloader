# Task P2-01: Add Update Notification Widget to Main Window

> **Phase**: 2 — UI Integration | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

This task connects the update system to the user interface. The Camplife DataLoader's main window (`FramelessCamplifeLoader`) needs a non-intrusive update notification area that informs users when updates are available and lets them initiate the update process.

The notification must follow the existing UI patterns:
- The main window uses a custom frameless design with a title bar at the top and status bar at the bottom
- The status bar currently shows "Ready" (left) and "✔ Connected" / "Disconnected" (right)
- Styling uses `LIGHT_THEME` / `DARK_THEME` QSS from `src/gui/themes.py`

### Architectural Intent

- **Non-intrusive**: The notification is a collapsible banner, not a modal dialog
- **Consistent**: Uses the existing QSS theme system — no inline styles
- **Minimal code change**: Only `main_window.py` and `themes.py` are modified; all other GUI files are untouched
- **Signal-driven**: Update state changes propagate via Qt signals (matches existing patterns)

---

## Affected Files

### Files to Modify

| File | Change | Lines Affected |
|------|--------|----------------|
| `src/gui/main_window.py` | Add update banner widget and handler methods | ~60 new lines in `_init_gui()` and 3 new methods |
| `src/gui/themes.py` | Add QSS rules for update banner (light + dark) | ~30 new lines |

### Files NOT Modified

All other GUI files (`loading_screen.py`, `setup_dialog.py`, `preview_dialog.py`, `progress_dialog.py`) are untouched.

---

## Dependencies & Prerequisites

- **P1-02**: `update_checker.py` must be implemented (provides `UpdateCheckResult`)
- **P1-03**: `update_manager.py` must be implemented (provides download + apply methods)
- Existing: `main_window.py` at current v1.1.0 state (441 lines)
- Existing: `themes.py` at current v1.1.0 state

---

## Implementation Details

### Step 1: Add Update Banner Widget to `_init_gui()`

Insert a new widget **between the central area and the status bar** (around line 183-188 in current `main_window.py`). The banner is hidden by default and shown when an update is available.

```python
# --- Update Notification Banner ---
# Placed between the central content area and the status bar
self.update_banner = QWidget()
self.update_banner.setObjectName("UpdateBanner")
self.update_banner.setVisible(False)  # Hidden by default

banner_layout = QHBoxLayout(self.update_banner)
banner_layout.setContentsMargins(15, 8, 15, 8)

self.update_icon_label = QLabel("⬆️")
banner_layout.addWidget(self.update_icon_label)

self.update_info_label = QLabel("Update available")
self.update_info_label.setObjectName("UpdateInfoLabel")
banner_layout.addWidget(self.update_info_label)

banner_layout.addStretch()

self.update_progress = QProgressBar()
self.update_progress.setObjectName("UpdateProgress")
self.update_progress.setFixedWidth(200)
self.update_progress.setVisible(False)
banner_layout.addWidget(self.update_progress)

self.update_action_btn = QPushButton("Update Now")
self.update_action_btn.setObjectName("UpdateActionBtn")
self.update_action_btn.clicked.connect(self._on_update_action)
banner_layout.addWidget(self.update_action_btn)

self.update_dismiss_btn = QPushButton("✕")
self.update_dismiss_btn.setObjectName("UpdateDismissBtn")
self.update_dismiss_btn.setFixedSize(24, 24)
self.update_dismiss_btn.clicked.connect(self._dismiss_update_banner)
banner_layout.addWidget(self.update_dismiss_btn)

cl.addWidget(self.update_banner)  # Add before status bar
```

**Placement**: The banner goes in the `cl` (central layout) after the "Review and Upload" button and before the status bar. This keeps it visible but not obstructive.

### Step 2: Add Handler Methods

```python
@Slot(object)
def on_update_check_result(self, result):
    """Handle the update check result from UpdateChecker."""
    if result.error:
        logger.info(f"Update check error (non-critical): {result.error}")
        return  # Silent failure — don't bother the user
    
    if result.update_available:
        self.update_info_label.setText(
            f"Update available: v{result.latest_version} — {result.changelog_summary}"
        )
        self.update_action_btn.setText("Update Now")
        self.update_action_btn.setEnabled(True)
        self.update_banner.setVisible(True)
        self._pending_update_result = result
        
        if result.is_critical:
            self.update_icon_label.setText("⚠️")
            self.update_info_label.setText(
                f"Critical update: v{result.latest_version} — {result.changelog_summary}"
            )

def _on_update_action(self):
    """Handle the update action button click."""
    btn_text = self.update_action_btn.text()
    
    if btn_text == "Update Now":
        # Start download
        self.update_action_btn.setText("Downloading...")
        self.update_action_btn.setEnabled(False)
        self.update_progress.setVisible(True)
        self.update_progress.setValue(0)
        # Delegate to UpdateManager (P1-03)
        # self.update_manager.download_and_stage(self._pending_update_result)
    
    elif btn_text == "Restart to Update":
        # Launch apply_update.bat and close app
        # self.update_manager.apply_and_restart()
        pass

def _dismiss_update_banner(self):
    """Dismiss the update notification."""
    self.update_banner.setVisible(False)

def _on_download_progress(self, percent):
    """Update the download progress bar."""
    self.update_progress.setValue(percent)

def _on_download_complete(self, success):
    """Handle download completion."""
    self.update_progress.setVisible(False)
    if success:
        self.update_action_btn.setText("Restart to Update")
        self.update_action_btn.setEnabled(True)
    else:
        self.update_info_label.setText("Download failed. Will retry later.")
        self.update_action_btn.setText("Retry")
        self.update_action_btn.setEnabled(True)
```

### Step 3: Add QSS Theme Rules

Add to `LIGHT_THEME` in `themes.py`:

```css
/* Update Banner */
#UpdateBanner {
    background-color: #E8F4E8;
    border-top: 1px solid #B8D4B8;
    border-bottom: 1px solid #B8D4B8;
}
#UpdateInfoLabel {
    color: #2D5A2D;
    font-size: 12px;
}
#UpdateActionBtn {
    background-color: #4A7C4A;
    color: white;
    border-radius: 4px;
    padding: 4px 12px;
    font-weight: bold;
}
#UpdateActionBtn:hover {
    background-color: #5A8C5A;
}
#UpdateActionBtn:disabled {
    background-color: #8AAB8A;
}
#UpdateDismissBtn {
    background: transparent;
    border: none;
    color: #666;
    font-size: 14px;
}
#UpdateDismissBtn:hover {
    color: #333;
}
#UpdateProgress {
    max-height: 16px;
}
```

Add matching rules to `DARK_THEME` with dark-mode-appropriate colors.

### Step 4: Add Import

Add `QProgressBar` to the PySide6 import list in `main_window.py`:

```python
from PySide6.QtWidgets import (
    ..., QProgressBar  # Add to existing import
)
```

---

## Validation Requirements

1. **App launches**: Application starts normally with the update banner hidden
2. **Banner shows on signal**: Calling `on_update_check_result()` with a mock result shows the banner
3. **Dismiss works**: Clicking ✕ hides the banner
4. **Theme support**: Banner renders correctly in both light and dark themes
5. **No regressions**: All existing functionality works unchanged
6. **Existing tests pass**: `test_app.py` and `test_security.py` still pass

---

## Expected Outcomes

- Update notification banner appears in the main window when an update is available
- Banner shows version number, changelog summary, and action button
- Download progress bar appears during download
- "Restart to Update" button appears when download is complete
- Banner is dismissible
- Both light and dark themes are supported

---

## Testing Expectations

No automated test file for this task (GUI testing is manual per existing QA practices). Instead, add to `tests/qa_test_plan.md`:

```markdown
## Phase 5: Update System

### 5.1 Update Notification
- **Task**: Trigger an update check (or mock one) that reports an available update.
- **Criteria**:
  - A green banner appears between the main content and the status bar.
  - The banner shows the version number and a changelog summary.
  - Clicking ✕ dismisses the banner.
  - The banner re-appears on next update check.

### 5.2 Theme Compatibility
- **Task**: Toggle the theme while the update banner is visible.
- **Criteria**:
  - The banner colors update correctly for both themes.
  - All text remains readable.
```

---

## Reasoning

**Why a banner instead of a modal dialog?**

Users are in the middle of uploading campground data — interrupting with a modal dialog would be frustrating and potentially cause data entry to be lost. A banner is visible but non-blocking, letting users choose when to act.

**Why between content and status bar, not in the title bar?**

The title bar is already crowded (title, resort label, connect, setup, theme, window controls). Adding an update indicator there would reduce readability. The bottom area near the status bar is a natural location for system notifications — it's visible but doesn't compete with the data upload workflow.

**Why a dismiss button?**

Users should never feel forced to update (except for critical security patches, which are flagged differently). Dismissing respects user autonomy and prevents "notification fatigue" that causes users to ignore all notifications.
