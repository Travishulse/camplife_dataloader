# 04 — Rollback & Recovery Strategy

> **Target Application**: Camplife DataLoader v1.1.0  
> **Status**: PLANNING  
> **Created**: 2026-05-27

---

## 1. Design Philosophy

> **Principle**: Every update operation must be reversible within 30 seconds without network access.

The rollback system is designed around three guarantees:

1. **No user data is ever lost** — `config.json`, `cache.json`, `logs/`, and `*.xlsx` are always preserved
2. **The previous working version is always recoverable** — at least one known-good backup exists at all times
3. **Recovery is automatic when possible, manual when necessary** — users should never need to reinstall

---

## 2. Backup Architecture

### 2.1 Backup Directory Structure

```
camplife_dataloader/
├── .backups/                          # Backup root (hidden directory)
│   ├── manifest.json                  # Tracks all backups and their metadata
│   ├── v1.1.0_2026-05-15T00-00-00/   # Backup of v1.1.0
│   │   ├── app/                       # Complete application directory snapshot
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── src/
│   │   │   └── ...
│   │   └── user_data/                 # Snapshot of user data at backup time
│   │       ├── config.json
│   │       ├── cache.json
│   │       └── logs/
│   ├── v1.0.0_2026-05-06T00-00-00/   # Backup of v1.0.0
│   │   └── ...
│   └── v0.9.0_2026-04-15T00-00-00/   # (would be pruned — beyond MAX_BACKUP_VERSIONS=3)
└── .updates/                          # Staging area for pending updates
    ├── update_state.json
    └── staged/                        # Extracted update ready for swap
```

### 2.2 Backup Manifest Schema (`manifest.json`)

```json
{
  "schema_version": 1,
  "max_backups": 3,
  "backups": [
    {
      "version": "1.1.0",
      "backup_date": "2026-06-15T10:30:00Z",
      "backup_path": "v1.1.0_2026-06-15T10-30-00",
      "app_hash": "sha256-of-directory-contents",
      "user_data_hash": "sha256-of-user-data-snapshot",
      "is_verified": true,
      "notes": "Pre-update backup before v1.2.0 installation"
    }
  ],
  "last_successful_version": "1.1.0",
  "pending_rollback": null
}
```

---

## 3. Rollback Triggers

### 3.1 Automatic Rollback

The system automatically initiates a rollback under these conditions:

| Trigger | Detection Method | Response |
|---------|-----------------|----------|
| **App crashes within 10s of post-update launch** | `update_state.json` has `"pending_verification": true` + process exit code ≠ 0 | Restore backup, show notification on next launch |
| **Critical import error** | `try/except` around core module imports in `main.py` | Log error, restore backup, restart |
| **Version mismatch after update** | `config.py:VERSION` doesn't match `update_state.json:staged_version` | Log error, restore backup |
| **Updater script failure** | `apply_update.bat` encounters error during swap | Immediately restore from backup directory |

### 3.2 Manual Rollback

Users can trigger a manual rollback via:

| Method | Description | Technical Detail |
|--------|-------------|-----------------|
| **In-app button** | "Revert to Previous Version" in update settings | Calls `rollback_manager.restore_latest_backup()` |
| **External script** | Double-click `restore_backup.bat` in the application directory | Standalone script that reads `manifest.json` and restores |
| **Emergency recovery** | Delete the entire app directory and extract the backup manually | Documented in user-facing FAQ |

### 3.3 Post-Update Health Check Flow

```
App Launch (after update)
      │
      ▼
┌─────────────────┐
│ Read update_state│
│ .json            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     NO
│ pending_         │───────────▶ Normal startup
│ verification?    │
└────────┬────────┘
         │ YES
         ▼
┌─────────────────┐
│ Start 10-second │
│ health timer    │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
    ▼                         ▼
┌─────────┐           ┌─────────────┐
│ Timer   │           │ App crashes  │
│ expires │           │ or import    │
│ (PASS)  │           │ error (FAIL) │
└────┬────┘           └──────┬──────┘
     │                       │
     ▼                       ▼
┌─────────────┐       ┌──────────────┐
│ Set          │       │ Rollback     │
│ pending =    │       │ Manager      │
│ false        │       │ restores     │
│ Update       │       │ backup       │
│ SUCCESS!     │       │              │
└─────────────┘       └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Restart app  │
                      │ (old version)│
                      │ Show dialog: │
                      │ "Update      │
                      │ reverted"    │
                      └──────────────┘
```

---

## 4. Data Preservation Strategy

### 4.1 Protected Files (Never Modified by Updates)

```python
# update_config.py
PROTECTED_FILES = [
    "config.json",        # Encrypted API credentials
    "cache.json",         # Cached resort/membership data
]

PROTECTED_DIRS = [
    "logs/",              # Application log files
]

PROTECTED_PATTERNS = [
    "*.xlsx",             # Upload log files (in app root)
    "Camplife_Upload_Log_*.xlsx",  # Specific log pattern
]
```

### 4.2 Preservation Flow During Update

```
1. PRE-UPDATE
   ├── Copy config.json → .backups/v1.1.0_*/user_data/config.json
   ├── Copy cache.json  → .backups/v1.1.0_*/user_data/cache.json
   └── Copy logs/       → .backups/v1.1.0_*/user_data/logs/

2. UPDATE (apply_update.bat)
   ├── Remove old application files (NOT config.json, cache.json, logs/)
   └── Extract new version to application directory

3. POST-UPDATE
   ├── Verify config.json still exists → if missing, restore from backup
   ├── Verify cache.json still exists  → if missing, restore from backup
   └── Verify logs/ still exists       → if missing, restore from backup
```

### 4.3 Data Integrity Verification

After every update, the rollback manager verifies:

| Check | Action if Failed |
|-------|-----------------|
| `config.json` exists and is valid JSON | Restore from user_data backup |
| `cache.json` exists and is valid JSON | Restore from user_data backup |
| `logs/` directory exists | Create it (same as `main.py` startup behavior) |
| `config.py` contains `VERSION` constant | Trigger full rollback (corrupted update) |
| `main.py` is importable without errors | Trigger full rollback (corrupted update) |

---

## 5. External Updater Script: `apply_update.bat`

### 5.1 Full Script Logic (Pseudocode)

```
ARGUMENTS: %PID% %STAGED_PATH% %APP_DIR% %BACKUP_DIR%

1. WAIT for process %PID% to exit (timeout 30s)
   └── If timeout: ABORT with error, do not modify any files

2. BACKUP current application
   ├── Copy %APP_DIR%\main.py, config.py, src\, scripts\ → %BACKUP_DIR%\app\
   ├── Copy %APP_DIR%\config.json → %BACKUP_DIR%\user_data\
   ├── Copy %APP_DIR%\cache.json  → %BACKUP_DIR%\user_data\
   └── Copy %APP_DIR%\logs\       → %BACKUP_DIR%\user_data\

3. APPLY update
   ├── Delete application files (main.py, config.py, src\, scripts\)
   │   ├── Do NOT delete: config.json, cache.json, logs\, .backups\, .updates\, *.xlsx
   ├── Extract %STAGED_PATH% to %APP_DIR%
   └── If extraction fails:
       └── GOTO step 5 (RESTORE)

4. VERIFY post-update
   ├── Check main.py exists
   ├── Check config.py exists
   ├── Check config.json exists (restore from backup if missing)
   ├── Check cache.json exists (restore from backup if missing)
   └── If critical files missing:
       └── GOTO step 5 (RESTORE)

5. RESTORE (on failure)
   ├── Delete partially-applied files
   ├── Copy %BACKUP_DIR%\app\ → %APP_DIR%\
   ├── Copy %BACKUP_DIR%\user_data\ → %APP_DIR%\
   └── Write "rollback_performed" to update_state.json

6. RESTART application
   └── Start %APP_DIR%\Camplife DataLoader.exe

7. EXIT
```

### 5.2 Error Handling

| Error Condition | Behavior |
|----------------|----------|
| Process didn't exit within 30s | Abort — no files touched, error logged |
| Backup directory creation fails | Abort — no files touched, error logged |
| File deletion fails (still locked) | Retry 3x with 2s delay, then abort with rollback |
| Archive extraction fails | Rollback from backup |
| Post-update verification fails | Rollback from backup |
| Restart fails | Leave restored files in place; user can launch manually |

---

## 6. Manual Recovery Script: `restore_backup.bat`

A standalone script that users can run if the application is completely broken:

```
PURPOSE: Emergency recovery when the application won't launch at all.

BEHAVIOR:
1. Read .backups\manifest.json
2. Display available backup versions
3. Prompt: "Restore to v1.1.0? (Y/N)"
4. If Y:
   ├── Copy backup\app\ files to application directory
   ├── Restore backup\user_data\ files
   └── Display: "Restored to v1.1.0. You can now launch the application."
5. If N: Exit
```

---

## 7. Backup Retention Policy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `MAX_BACKUP_VERSIONS` | 3 | Covers current + 2 previous; sufficient for rollback chains |
| Cleanup trigger | After successful update + 7-day grace period | Gives time to discover delayed issues |
| Cleanup order | Oldest first | Most recent backups are most likely needed |
| Disk space estimate | ~50 MB per backup × 3 = ~150 MB total | Acceptable for a desktop application |
| Backup directory location | `APP_DIR/.backups/` | Portable with the application; no system directory dependency |

---

## 8. Recovery Scenarios

### Scenario 1: Normal Successful Update

```
v1.1.0 running → check → v1.2.0 available → download → verify → stage
→ user clicks "Update Now" → backup v1.1.0 → apply v1.2.0 → restart
→ health check passes → update_state: success → prune old backups
```

### Scenario 2: Update Crashes on First Launch

```
v1.2.0 applied → app launches → import error within 10s
→ health check FAILS → rollback_manager restores v1.1.0 backup
→ app restarts with v1.1.0 → shows "Update to v1.2.0 was reverted due to an error"
→ logs contain crash details for developer diagnosis
```

### Scenario 3: Corrupted Download

```
v1.2.0 download completes → SHA-256 mismatch detected
→ staged archive deleted → user notified: "Download failed. Will retry later."
→ no files modified, app continues running v1.1.0
```

### Scenario 4: Power Failure During Update

```
apply_update.bat running → power cut after partial file deletion
→ next boot: app won't launch (missing files)
→ user double-clicks restore_backup.bat → selects v1.1.0 → restored
→ app launches normally on v1.1.0
```

### Scenario 5: User Wants to Downgrade

```
v1.2.0 running → user clicks "Revert to Previous Version"
→ rollback_manager reads manifest → v1.1.0 backup available
→ confirmation dialog → backup current v1.2.0 → restore v1.1.0
→ restart → running v1.1.0
```

---

## 9. Testing Requirements for Rollback System

| Test | Type | Validates |
|------|------|-----------|
| Backup creation produces complete, extractable archive | Unit | RollbackManager.create_backup() |
| Restore from backup produces runnable application | Integration | Full backup → corrupt → restore → launch cycle |
| Protected files survive update cycle | Integration | config.json, cache.json present after update |
| Protected files survive rollback cycle | Integration | config.json, cache.json present after rollback |
| Manifest tracks all backups correctly | Unit | Backup creation/deletion updates manifest.json |
| Old backups are pruned after MAX_BACKUP_VERSIONS | Unit | 4th backup triggers deletion of 1st |
| Post-update health check triggers rollback on crash | Integration | Simulate crash within 10s → verify rollback |
| apply_update.bat handles locked files | Manual | Run while DLLs are loaded → verify retry/abort behavior |
| restore_backup.bat works standalone | Manual | Delete main.py → run script → verify recovery |

---

> **Next**: See [05-ai-governance.md](./05-ai-governance.md) for AI governance considerations.
