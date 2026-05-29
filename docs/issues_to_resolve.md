# Technical Deep Dive: DLL Loading Failure post-Update

## 1. Executive Summary
A critical issue occurred during the auto-update workflow: after the user triggered the update, the application closed to apply the files but failed to relaunch. Upon manual relaunch, the operating system raised a fatal PyInstaller bootloader error:

```
Failed to load Python DLL 'C:\Users\travi\Downloads\Camplife DataLoader\_internal\python312.dll'.
LoadLibrary: The specified module could not be found.
```

This error indicates that either the core Python interpreter library (`python312.dll`) or one of its critical dependencies in the `_internal` directory was deleted, not copied, or corrupted during the update file swap.

---

## 2. Root Cause Analysis

A deep dive into the update swapper mechanism (`apply_update.bat` and `main_window.py`) highlights three interconnected vulnerabilities that lead to this failure.

### A. Race Condition & File Locking (Primary Cause)
When the PyInstaller-built executable runs, the Windows OS loads `_internal\python312.dll` into memory and places an exclusive read/execute lock on the physical file. 

1. When the user clicks **[Restart to Apply]**, the main application triggers `apply_update.bat` and immediately calls `self.close()` and `QApplication.quit()`.
2. The batch script uses a `tasklist` loop to wait for the parent process PID to terminate:
   ```batch
   :wait_loop
   tasklist /FI "PID eq %PID%" 2>NUL | find /I "%PID%" >NUL
   ```
3. **The Window vs. Process Lifecycle Gap**: When a PySide6 GUI application exits, the window closes immediately, and the process begins tearing down threads and unloading DLLs. However, Windows can take several seconds to fully unload DLLs and release the file handles.
4. `tasklist` may report the process has terminated *before* the OS has fully released the file locks on `python312.dll`.
5. The batch script immediately proceeds to:
   ```batch
   rmdir /S /Q "%DEST_DIR%\_internal" >NUL
   ```
6. Because `python312.dll` (or other DLLs) are still locked by the operating system, the `rmdir` command **fails to delete them** (raising an "Access is denied" error under the hood), but succeeds in deleting other non-locked files in `_internal`.
7. Next, the script runs `xcopy`:
   ```batch
   xcopy /E /I /H /R /Y "%TEMP_DIR%" "%DEST_DIR%" >NUL
   ```
   Since the original `python312.dll` is still locked or half-deleted, `xcopy` fails to overwrite it. The update package is left partially copied, leaving `_internal` corrupted and missing critical interpreter DLLs.

### B. Fatal Error Suppression via `>NUL`
The batch script redirects both stdout and stderr of the critical operations to null:
```batch
rmdir /S /Q "%DEST_DIR%\_internal" >NUL
xcopy /E /I /H /R /Y "%TEMP_DIR%" "%DEST_DIR%" >NUL
```
By redirecting all output to `NUL`, any file-locking errors ("Access is denied", "File in use", or "Path not found") are completely swallowed. The script silently fails the file-copy operation, assumes success, and attempts to relaunch the application.

### C. Vulnerable PID Substring Matching in `tasklist`
The check `find /I "%PID%"` matches any substring within the `tasklist` output. 
- If the parent application's PID is `8020`, but another unrelated system process has a PID like `18020` or memory usage like `8020 K`, the script will match it and wait indefinitely, or conversely, mismatch and proceed too early if the matching is unstable.

---

## 3. Resolution (Implemented 2026-05-29)

> [!NOTE]
> All three vulnerabilities have been resolved. The fixes are documented below with references to the exact changes made.

### A. Race Condition & File Locking — ✅ RESOLVED

**Fix: Rename-based transactional swap + post-exit safety delay**

In [apply_update.bat](file:///c:/Users/travi/.gemini/antigravity/scratch/camplife_dataloader/apply_update.bat):
- Added a **5-second post-exit safety delay** (`timeout /t 5 /nobreak`) after the process exits to guarantee that Windows has fully released all DLL file handles
- Replaced the destructive `rmdir /S /Q _internal` with a **safe rename**: `rename _internal _internal.old`
  - Rename is instantaneous and atomic — it either fully succeeds or fully fails
  - It never leaves the directory in a half-deleted, corrupted state
- If the subsequent `xcopy` fails, the script performs a **rollback**: `rename _internal.old _internal` — preserving the user's original working installation
- Added a **retry loop** (up to 3 attempts with 3-second delays) for the `xcopy` operation
- On startup, `main.py` calls `cleanup_stale_update_artifacts()` to remove any leftover `_internal.old` from a previous cycle

### B. Fatal Error Suppression — ✅ RESOLVED

**Fix: Full logging to a diagnostic file**

In [apply_update.bat](file:///c:/Users/travi/.gemini/antigravity/scratch/camplife_dataloader/apply_update.bat):
- All critical operations now log to `%TEMP%\camplife_update_log.txt` instead of `>NUL`
- Log includes timestamps, operation outcomes, error codes, and rollback actions
- Python-side logging was also added to `main_window.py`'s `apply_update_restart()` method via the `camplife` logger

### C. PID Substring Matching — ✅ RESOLVED

**Fix: Exact PID matching via CSV-formatted tasklist output**

In [apply_update.bat](file:///c:/Users/travi/.gemini/antigravity/scratch/camplife_dataloader/apply_update.bat):
- Changed from `find /I "%PID%"` (substring) to:
  ```batch
  tasklist /FI "PID eq %PID%" /FO CSV /NH | findstr /R /C:"\"%PID%\""
  ```
- The `/FO CSV /NH` flag outputs the PID as a quoted field (`"12345"`), and `findstr` matches the exact quoted value
- Added a **60-second timeout failsafe** — if the process somehow never disappears from `tasklist`, the script proceeds anyway instead of hanging forever

### Files Modified
| File | Changes |
|------|---------|
| [apply_update.bat](file:///c:/Users/travi/.gemini/antigravity/scratch/camplife_dataloader/apply_update.bat) | Complete rewrite: transactional rename swap, logging, hardened PID check, retry loop, rollback |
| [main_window.py](file:///c:/Users/travi/.gemini/antigravity/scratch/camplife_dataloader/src/gui/main_window.py) | Added logging to `apply_update_restart()`, added `cleanup_stale_update_artifacts()` static method |
| [main.py](file:///c:/Users/travi/.gemini/antigravity/scratch/camplife_dataloader/main.py) | Added startup call to `cleanup_stale_update_artifacts()` |
| [UPDATE_WORKFLOW.md](file:///c:/Users/travi/.gemini/antigravity/scratch/camplife_dataloader/docs/UPDATE_WORKFLOW.md) | Complete rewrite as comprehensive agent reference with troubleshooting guide |
