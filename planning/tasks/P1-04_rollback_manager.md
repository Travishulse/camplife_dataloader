# Task P1-04: Implement `rollback_manager.py` — Backup, Restore & Manifest Tracking

> **Phase**: 1 — Core Logic | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The rollback manager is the safety net of the entire update system. It guarantees that every update is reversible — if anything goes wrong, the user can get back to a working version instantly, without network access.

This is the most safety-critical module in the update system. Bugs here can cause data loss or leave the application unrecoverable.

### Architectural Intent

- **Backup-first**: No update operation begins without creating a complete backup first
- **User data isolation**: User files (`config.json`, `cache.json`, `logs/`) are backed up separately from application files
- **Manifest-driven**: A JSON manifest tracks all backups, enabling programmatic restore and pruning
- **Offline recovery**: Rollback works without network access — all data is local
- **Pruning**: Old backups are cleaned up to prevent unbounded disk usage

---

## Affected Files

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/update/rollback_manager.py` | Replace placeholder | Backup creation, restore, manifest, pruning |

### Files to Create (Tests)

| File | Purpose |
|------|---------|
| `tests/test_rollback_manager.py` | Unit tests for backup/restore/prune operations |

### Existing Files — NO Modifications

No existing files are modified.

---

## Dependencies & Prerequisites

- **P0-01**: `src/update/` package must exist (for `update_config.py` constants)
- **P1-01**: `integrity.py` must be implemented (for `compute_directory_hash`)
- **Python stdlib**: `shutil`, `json`, `os`, `datetime`, `pathlib`

---

## Implementation Details

### Public API

```python
"""
RollbackManager — Manages application backups, restores, and version tracking.

This is the safety net of the update system. Every update creates a backup first.
If anything goes wrong, the backup can be restored instantly without network access.

CRITICAL SAFETY RULES:
1. NEVER delete a backup without first verifying another backup exists
2. ALWAYS back up user data (config.json, cache.json) separately from app files
3. ALWAYS verify backup integrity after creation
4. NEVER modify files in PROTECTED_FILES or PROTECTED_DIRS unless restoring them
"""
import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from config import APP_DIR, VERSION
from src.update.update_config import (
    UPDATE_BACKUP_DIR,
    MAX_BACKUP_VERSIONS,
    PROTECTED_FILES,
    PROTECTED_DIRS,
    PROTECTED_PATTERNS,
)
from src.update.integrity import compute_directory_hash

logger = logging.getLogger("camplife.update.rollback")


class BackupInfo:
    """Metadata about a single backup."""
    def __init__(self, version: str, backup_date: str, backup_path: str,
                 app_hash: str = "", user_data_hash: str = "",
                 is_verified: bool = False, notes: str = ""):
        self.version = version
        self.backup_date = backup_date
        self.backup_path = backup_path
        self.app_hash = app_hash
        self.user_data_hash = user_data_hash
        self.is_verified = is_verified
        self.notes = notes


class RollbackManager:
    """
    Manages application backups and restores.
    
    Usage:
        rm = RollbackManager()
        rm.create_backup("Pre-update backup before v1.2.0")
        # ... apply update ...
        # If something goes wrong:
        rm.restore_latest_backup()
    """
    
    def __init__(self):
        self._backup_dir = UPDATE_BACKUP_DIR
        self._manifest_path = os.path.join(self._backup_dir, "manifest.json")
        os.makedirs(self._backup_dir, exist_ok=True)

    def create_backup(self, notes: str = "") -> BackupInfo:
        """
        Create a complete backup of the current application.
        
        Creates two subdirectories within the backup:
        - app/       — Application files (main.py, config.py, src/, scripts/)
        - user_data/ — User files (config.json, cache.json, logs/)
        
        Args:
            notes: Human-readable note about why this backup was created.
        
        Returns:
            BackupInfo with metadata about the created backup.
        
        Raises:
            OSError: If backup directory cannot be created or files cannot be copied.
        """
        ...

    def restore_latest_backup(self) -> bool:
        """
        Restore the most recent backup.
        
        Returns:
            True if restore succeeded, False if no backup exists or restore failed.
        """
        ...

    def restore_backup(self, version: str) -> bool:
        """
        Restore a specific version from backup.
        
        Args:
            version: Version string to restore (e.g., "1.1.0").
        
        Returns:
            True if restore succeeded, False if backup not found or restore failed.
        """
        ...

    def list_backups(self) -> list[BackupInfo]:
        """
        List all available backups, newest first.
        
        Returns:
            List of BackupInfo objects.
        """
        ...

    def get_latest_backup(self) -> Optional[BackupInfo]:
        """
        Get the most recent backup, or None if no backups exist.
        """
        ...

    def prune_old_backups(self, keep: int = MAX_BACKUP_VERSIONS):
        """
        Remove old backups beyond the retention limit.
        
        Keeps the newest `keep` backups and deletes the rest.
        Never deletes the most recent backup even if keep=0.
        
        Args:
            keep: Number of backups to retain.
        """
        ...

    def verify_backup(self, backup_info: BackupInfo) -> bool:
        """
        Verify that a backup is complete and uncorrupted.
        
        Checks:
        1. Backup directory exists
        2. app/ subdirectory contains main.py and config.py
        3. user_data/ subdirectory contains config.json (if it existed when backed up)
        4. Directory hash matches stored hash (if available)
        
        Returns:
            True if backup is valid, False otherwise.
        """
        ...

    def _load_manifest(self) -> dict:
        """Load the backup manifest from disk."""
        ...

    def _save_manifest(self, manifest: dict):
        """Save the backup manifest to disk."""
        ...

    def _get_backup_dirname(self) -> str:
        """Generate a unique backup directory name: v{VERSION}_{timestamp}"""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        return f"v{VERSION}_{timestamp}"

    def _copy_app_files(self, dest_dir: str):
        """
        Copy application files to the backup directory.
        Excludes: PROTECTED_FILES, PROTECTED_DIRS, __pycache__, .backups, .updates, *.xlsx
        """
        ...

    def _copy_user_data(self, dest_dir: str):
        """
        Copy user data files to the backup directory.
        Includes: config.json, cache.json, logs/
        Only copies files that actually exist.
        """
        ...

    def _restore_app_files(self, backup_app_dir: str):
        """
        Restore application files from backup.
        Deletes current app files first (except protected), then copies from backup.
        """
        ...

    def _restore_user_data(self, backup_user_dir: str):
        """
        Restore user data files from backup.
        Only restores files that are missing from the current directory.
        Does NOT overwrite existing user data (it may have been updated since backup).
        """
        ...
```

### Critical Safety Logic

**Backup creation must**:
1. Create the backup directory atomically (if creation fails, no partial backup exists)
2. Copy app files first, then user data
3. Compute and store directory hashes for later verification
4. Update the manifest only after all files are copied
5. Log every step for debugging

**Restore must**:
1. Verify the backup is valid before attempting restore
2. Delete current app files (NOT user data, NOT backups, NOT .updates)
3. Copy app files from backup
4. Check if user data files exist — only restore if missing (don't overwrite newer data)
5. Update the manifest with restore metadata
6. Log every step

**Pruning must**:
1. Never delete the most recent backup
2. Sort backups by date before pruning
3. Delete directories, not just manifest entries
4. Handle partially-deleted backups (e.g., from a previous interrupted prune)

---

## Validation Requirements

1. **Unit tests pass**: `python -m pytest tests/test_rollback_manager.py -v`
2. **Backup creates correct structure**: Verify `app/` and `user_data/` directories exist with expected contents
3. **Restore produces working app**: After backup → modify → restore, app files match the backup
4. **User data preserved**: After restore, `config.json` and `cache.json` are NOT overwritten if they still exist
5. **Pruning works**: After creating 4 backups with `MAX_BACKUP_VERSIONS=3`, only 3 remain
6. **Manifest is correct**: Manifest reflects actual state of backups on disk
7. **No regressions**: Existing tests still pass

---

## Testing Expectations

Create `tests/test_rollback_manager.py` using a temporary directory (`tempfile.mkdtemp`) for isolation:

| Test Case | Description | Expected |
|-----------|-------------|----------|
| Create backup | Create backup of test app directory | Backup dir exists with app/ and user_data/ |
| Backup contains app files | Check main.py in backup | File exists and matches original |
| Backup contains user data | Check config.json in backup | File exists and matches original |
| Backup excludes protected | Check .backups not in backup | Directory not present |
| Manifest updated | Read manifest after backup | Entry exists with correct version |
| Restore from backup | Modify app, then restore | Files match backup |
| Restore preserves user data | Modify config.json, then restore | Modified config.json kept (not overwritten) |
| Restore missing user data | Delete config.json, then restore | config.json restored from backup |
| List backups | Create 3 backups, list them | 3 entries, newest first |
| Prune old backups | Create 4 backups, prune to 3 | Oldest deleted, 3 remain |
| Prune never deletes newest | Prune to 0 | 1 backup still exists |
| Verify valid backup | Verify a complete backup | Returns True |
| Verify corrupted backup | Delete a file from backup, verify | Returns False |
| No backup exists | Call restore with no backups | Returns False, no crash |

---

## Reasoning

**Why separate app/ and user_data/ in backups?**

User data follows different rules than application code. App files are replaced entirely during updates; user data is preserved. By separating them in the backup, the restore logic can make independent decisions: always restore app files, but only restore user data if it's missing.

**Why not overwrite existing user data during restore?**

Consider this scenario: User updates to v1.2.0, the app works fine for 3 days (uploading data, saving new credentials). Then the user decides to downgrade. If restore overwrites `config.json`, they lose 3 days of credential changes. Instead, restore only fills in missing files — if `config.json` exists, it's the user's current version and should be kept.

**Why a manifest file instead of just scanning the directory?**

Scanning the directory is fragile — it depends on directory naming conventions and can't distinguish between a valid backup and a corrupted one. The manifest provides authoritative metadata (version, date, hash) and allows the prune logic to make informed decisions about which backups to keep.
