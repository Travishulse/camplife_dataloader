# Task P1-03: Implement `update_manager.py` — Download, Stage & Apply Orchestrator

> **Phase**: 1 — Core Logic | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The UpdateManager is the orchestration layer that coordinates the entire update lifecycle: downloading the update archive, verifying its integrity, staging it in a temporary directory, and initiating the apply process (which delegates to `apply_update.bat` for the actual file swap).

It bridges the UpdateChecker (which determines *if* an update is available) and the RollbackManager (which handles backups/restores). The UpdateManager handles the *how* of getting from "update available" to "update applied."

### Architectural Intent

- **Orchestrator pattern**: Delegates to specialized modules (integrity, rollback_manager, apply_update.bat) rather than implementing everything itself
- **Signal-driven**: Emits progress and completion signals for GUI integration (matches AuthWorker/UploadWorker pattern)
- **Resumable downloads**: Uses HTTP range requests for download resume on interruption
- **Fail-safe**: Any failure at any stage leaves the app in its current working state

---

## Affected Files

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/update/update_manager.py` | Replace placeholder | Download, verify, stage, apply orchestration |

### Existing Files — NO Modifications

No existing files are modified.

---

## Dependencies & Prerequisites

- **P1-01**: `integrity.py` for hash verification
- **P1-02**: `update_checker.py` for `UpdateCheckResult` data class
- **P1-04**: `rollback_manager.py` for backup creation before apply
- **Existing**: `requests` library for HTTP downloads
- **Existing**: `zipfile` for archive extraction

---

## Implementation Details

### Public API

```python
class UpdateManager(QObject):
    """Orchestrates the update download, staging, and apply process."""
    
    # Signals
    download_progress = Signal(int)       # Percentage (0-100)
    download_complete = Signal(bool)      # True=success, False=failure
    stage_complete = Signal(bool)         # True=success, False=failure
    apply_started = Signal()              # Emitted when apply_update.bat launches
    status_msg = Signal(str)              # Human-readable status messages
    
    def download_and_stage(self, check_result: UpdateCheckResult):
        """Download update and stage it for application. Runs on background thread."""
    
    def apply_and_restart(self):
        """Create backup, launch apply_update.bat, and close the application."""
    
    def cancel_download(self):
        """Cancel an in-progress download."""
    
    def get_staged_update(self) -> Optional[dict]:
        """Get info about a staged (ready-to-apply) update, or None."""
    
    def clear_staged_update(self):
        """Remove a staged update that was not applied."""
```

### Key Behaviors

1. **Download decision**: If a patch is available for the user's version, download the patch (smaller). Otherwise, download the full archive.
2. **Download progress**: Report progress via `download_progress` signal (percentage 0-100).
3. **Integrity verification**: After download, verify SHA-256 hash. If mismatch, delete the file and emit failure.
4. **Staging**: Extract the archive to `.updates/staged/` directory. Validate structure against `REQUIRED_FILES_AFTER_UPDATE`.
5. **Apply initiation**: Create backup via RollbackManager, then launch `apply_update.bat` with appropriate arguments, then close the application via `QApplication.quit()`.

---

## Validation Requirements

1. Download to staging directory works with mock HTTP server
2. SHA-256 verification rejects corrupted downloads
3. Cancel during download stops the transfer and cleans up
4. Apply creates backup before launching the updater script
5. Staged update info is correctly stored and retrievable

---

## Expected Outcomes

- Complete download → verify → stage → apply pipeline
- All failures are handled gracefully with clear error signals
- Background download never blocks the GUI

---

## Reasoning

**Why QObject instead of QThread?**

The UpdateManager uses QThread internally for downloads but is itself a QObject owned by the main thread. This matches how `CamplifeAPIClient` works — it's a QObject that delegates heavy work to `AuthWorker` (a QThread). The manager needs to coordinate between the GUI (main thread) and the download (background thread).
