# Task P1-05: Implement `apply_update.bat` — External Updater Script

> **Phase**: 1 — Core Logic | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

Windows locks running `.exe` and `.dll` files, preventing the application from replacing its own files while running. The solution is a lightweight external batch script that takes over after the main application exits, performs the file swap, and restarts the updated application.

This script is the most operationally critical file in the update system. A bug here can leave the application unable to launch. It must be extremely defensive, with error handling at every step and automatic rollback on any failure.

### Architectural Intent

- **Minimal complexity**: A batch script (not Python) to avoid dependency on the Python runtime being available during the swap
- **Defense in depth**: Every step validates success before proceeding; any failure triggers immediate rollback
- **Atomic-ish**: Uses directory rename (fast on NTFS) rather than file-by-file copy for the swap
- **Logging**: Writes to a log file for post-mortem debugging if something goes wrong
- **Self-cleaning**: Removes the staged update files after successful apply

---

## Affected Files

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/apply_update.bat` | External updater script |
| `scripts/restore_backup.bat` | Emergency manual recovery script |

---

## Dependencies & Prerequisites

- **P1-04**: `rollback_manager.py` concepts (backup directory structure)
- Understanding of Windows batch scripting, `tasklist`, `timeout`, `robocopy`, `rmdir`

---

## Implementation Details

### `scripts/apply_update.bat`

**Arguments**:
- `%1` = PID of the main application process
- `%2` = Path to the staged update directory (e.g., `.updates\staged\`)
- `%3` = Path to the application directory (e.g., `dist\Camplife DataLoader\`)
- `%4` = Path to the backup directory (e.g., `.backups\v1.1.0_2026-06-15T10-30-00\`)

**Logic flow**:

```batch
@echo off
setlocal EnableDelayedExpansion

REM === CAMPLIFE DATALOADER UPDATE SCRIPT ===
REM This script is launched by the application to perform file replacement.
REM It waits for the application to exit, swaps files, and restarts.

set "PID=%~1"
set "STAGED_DIR=%~2"
set "APP_DIR=%~3"
set "BACKUP_DIR=%~4"
set "LOG_FILE=%APP_DIR%\logs\update_apply.log"

echo [%DATE% %TIME%] Update script started >> "%LOG_FILE%"
echo [%DATE% %TIME%] PID=%PID% STAGED=%STAGED_DIR% APP=%APP_DIR% BACKUP=%BACKUP_DIR% >> "%LOG_FILE%"

REM 1. Wait for the main process to exit (max 30 seconds)
REM 2. Verify staged directory exists and contains main.py
REM 3. Backup current app files (robocopy to backup dir)
REM 4. Delete current app files (except protected: config.json, cache.json, logs, .backups, .updates)
REM 5. Copy staged files to app directory
REM 6. Verify critical files exist after copy
REM 7. If any step fails: restore from backup
REM 8. Clean up staged files
REM 9. Restart the application
```

**Critical rules**:
- NEVER delete `config.json`, `cache.json`, `logs\`, `.backups\`, `.updates\`, `*.xlsx`
- Use `robocopy` with `/MIR` for reliable directory copy (handles long paths, retries)
- Log every operation to `logs\update_apply.log` with timestamps
- If the application fails to start after update, leave the restored files in place

### `scripts/restore_backup.bat`

A standalone emergency script that users can double-click if the application is completely broken. Reads `.backups\manifest.json`, displays available versions, and restores the selected one.

---

## Validation Requirements

1. Script waits for process to exit before modifying files
2. Script creates backup before modifying files
3. Script preserves protected files
4. Script restores backup on any failure
5. Script restarts the application after successful update
6. Script works when run from the application directory
7. Manual test on Windows 10/11

---

## Expected Outcomes

- `scripts/apply_update.bat` handles the complete file swap lifecycle
- `scripts/restore_backup.bat` provides emergency recovery
- Both scripts are documented with inline comments for maintainability

---

## Reasoning

**Why batch instead of PowerShell?**

Batch scripts work on all Windows versions without configuration. PowerShell may have execution policies that prevent unsigned scripts from running. Since the updater script must work in the widest possible set of environments (including locked-down corporate machines), batch is the safest choice.

**Why not a compiled updater executable?**

A compiled updater would need to be built, signed, and distributed alongside the main application. This adds complexity to the build pipeline and creates another binary that antivirus may flag. A batch script is transparent, auditable, and understood by IT administrators.
