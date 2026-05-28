# 02 — Risk Analysis

> **Target Application**: Camplife DataLoader v1.1.0  
> **Status**: PLANNING  
> **Created**: 2026-05-27

---

## Risk Matrix

| Severity | Likelihood: High | Likelihood: Medium | Likelihood: Low |
|----------|-----------------|-------------------|-----------------|
| **Critical** | — | R-01, R-02 | R-03, R-04 |
| **High** | R-05 | R-06, R-07 | R-08 |
| **Medium** | R-09 | R-10, R-11 | R-12 |
| **Low** | — | R-13 | R-14, R-15 |

---

## Critical Risks

### R-01: Corrupted Update Bricks Application
- **Severity**: Critical | **Likelihood**: Medium
- **Description**: A corrupted or incomplete update archive replaces the working application, leaving the user unable to launch the app. This is the highest-priority risk because users are non-technical campground staff who cannot debug or manually restore files.
- **Root Cause**: Network interruption during download, disk write failure during extraction, or bug in update application logic.
- **Mitigation**:
  1. **Pre-apply integrity check**: Verify SHA-256 checksum of downloaded archive before any file operations begin.
  2. **Backup before swap**: Always create a complete backup of the current application directory before applying any update.
  3. **Atomic swap pattern**: Use the external `apply_update.bat` script to perform the swap as a single logical operation with rollback on any failure.
  4. **Post-launch health check**: On first startup after an update, run a health check. If the check fails within 10 seconds (crash/import error), the rollback manager restores the backup automatically.
  5. **Manual recovery path**: Include a `restore_backup.bat` script that users can double-click to restore the most recent working version without any technical knowledge.
- **Residual Risk**: Low — multiple layers of defense make unrecoverable corruption extremely unlikely.

### R-02: User Data Loss During Update
- **Severity**: Critical | **Likelihood**: Medium
- **Description**: Update process overwrites or deletes `config.json` (encrypted API credentials), `cache.json` (cached resort data), `logs/` directory, or `*.xlsx` upload logs.
- **Root Cause**: Update extraction overwrites all files indiscriminately, or the protected file list is incomplete.
- **Mitigation**:
  1. **Explicit protected file list**: Maintain a hardcoded, well-tested list of files/directories that must never be touched (`PROTECTED_FILES` in `update_config.py`).
  2. **Pre-update snapshot**: Before any update, copy all protected files to the backup directory alongside the application backup.
  3. **Post-update restore**: After extracting the new version, explicitly copy protected files back from the snapshot.
  4. **Integration test**: Dedicated test that verifies `config.json` and `cache.json` survive a full update cycle.
  5. **Dry-run mode**: Add a `--dry-run` flag to the update process that logs what would be changed without modifying any files.
- **Residual Risk**: Very Low — explicit allow-list approach (not deny-list) ensures only known-safe operations occur.

### R-03: Man-in-the-Middle Attack on Update Channel
- **Severity**: Critical | **Likelihood**: Low
- **Description**: An attacker intercepts the update download and substitutes a malicious binary.
- **Root Cause**: Insufficient verification of update source and content.
- **Mitigation**:
  1. **TUF metadata verification**: Use tufup's TUF-based trust chain to verify all update metadata is signed by the project's root key.
  2. **SHA-256 content verification**: Every downloaded file is verified against its checksum before extraction.
  3. **HTTPS-only**: All update communication uses TLS 1.3. No HTTP fallback.
  4. **Pinned endpoints**: Update URLs are hardcoded in the application, not configurable by users or config files.
- **Residual Risk**: Very Low — TUF is specifically designed to defend against this class of attack.

### R-04: Supply Chain Attack via Compromised Dependency
- **Severity**: Critical | **Likelihood**: Low
- **Description**: A malicious version of `tufup`, `bsdiff4`, or other dependency is installed, compromising the update system itself.
- **Root Cause**: Dependency confusion, typosquatting, or upstream compromise.
- **Mitigation**:
  1. **Pin exact versions**: Use exact version pins in `requirements.txt` (e.g., `tufup==1.0.0`).
  2. **Hash verification**: Use `--require-hashes` in pip install commands for production builds.
  3. **Dependabot alerts**: Enable GitHub Dependabot for automated vulnerability monitoring.
  4. **Minimal new dependencies**: Only add `tufup` and `bsdiff4` — both are well-established libraries with active maintenance.
- **Residual Risk**: Low — standard supply chain hygiene reduces risk to acceptable levels.

---

## High Risks

### R-05: Windows File Locking Prevents Update
- **Severity**: High | **Likelihood**: High
- **Description**: Windows locks `.exe`, `.dll`, and `.pyd` files while the application is running, preventing in-place replacement.
- **Mitigation**:
  1. **External updater script**: The `apply_update.bat` script runs as a separate process after the main application exits.
  2. **Process wait with timeout**: The script waits for the main process PID to exit (with a 30-second timeout) before attempting file operations.
  3. **Retry logic**: If file operations fail, retry up to 3 times with 2-second delays.
- **Residual Risk**: Low — this is a well-understood problem with proven solutions.

### R-06: Update Fails Silently, User Stays on Old Version
- **Severity**: High | **Likelihood**: Medium
- **Description**: Network errors, firewall blocks, or API rate limits prevent the update check from completing, and the user is never notified.
- **Mitigation**:
  1. **Structured error handling**: All network failures are caught and logged with specific error codes.
  2. **Manual check option**: Users can trigger an update check manually via the UI.
  3. **Last-check timestamp**: The app stores `last_check` time. If > 7 days since last successful check, show a subtle warning.
  4. **GitHub API rate limiting**: Unauthenticated GitHub API allows 60 requests/hour — more than sufficient for daily checks. Cache the last-known result.
- **Residual Risk**: Medium — network availability is outside our control, but users have manual fallback.

### R-07: Antivirus/EDR Blocks Update Process
- **Severity**: High | **Likelihood**: Medium
- **Description**: Enterprise antivirus or Windows Defender flags the update download or the `apply_update.bat` script as suspicious behavior (downloading executables, replacing files, launching batch scripts).
- **Mitigation**:
  1. **Code signing**: Sign the executable with a trusted certificate (Azure Artifact Signing at ~$10/month, see cost analysis).
  2. **Consistent file naming**: Use predictable, professional file names that don't trigger heuristic detection.
  3. **No obfuscation**: Keep all scripts human-readable and well-commented.
  4. **Documentation for IT departments**: Provide whitelisting instructions for enterprise deployment.
- **Residual Risk**: Medium — antivirus behavior varies widely and cannot be fully controlled.

### R-08: Partial Update Leaves Application in Inconsistent State
- **Severity**: High | **Likelihood**: Low
- **Description**: Power failure or system crash during the file swap phase leaves the application directory in a partial state (some files from old version, some from new).
- **Mitigation**:
  1. **Backup-first**: Complete backup exists before any files are modified.
  2. **Ordered operations**: Extract to temp directory first, then perform directory rename (which is nearly atomic on NTFS).
  3. **State file tracking**: `update_state.json` tracks the current phase of the update. On next launch, the app can detect an incomplete update and trigger rollback.
  4. **Manual recovery**: `restore_backup.bat` script available as a last resort.
- **Residual Risk**: Low — multiple recovery mechanisms available.

---

## Medium Risks

### R-09: GitHub API Rate Limiting
- **Severity**: Medium | **Likelihood**: High
- **Description**: GitHub's unauthenticated API rate limit is 60 requests/hour per IP. If many users share an IP (corporate NAT), rate limiting may block update checks.
- **Mitigation**:
  1. **Cache update manifest locally**: Only check once per 24 hours.
  2. **Firebase Hosting fallback**: If GitHub API fails, fall back to Firebase-hosted manifest (not rate-limited).
  3. **Graceful degradation**: Rate limiting is logged but does not produce an error dialog — the app continues to function normally.
- **Residual Risk**: Low — caching + fallback effectively eliminates this risk.

### R-10: Build Pipeline Produces Incorrect Artifacts
- **Severity**: Medium | **Likelihood**: Medium
- **Description**: CI/CD pipeline generates wrong checksums, mismatched manifests, or corrupted archives due to a configuration error.
- **Mitigation**:
  1. **Automated validation step**: After building, run a validation step that downloads the published artifacts and verifies their checksums.
  2. **Staging channel**: Test releases on a `beta` channel before promoting to `stable`.
  3. **Manual release approval**: Require a human to approve the GitHub Release before it becomes public.
- **Residual Risk**: Low — automated validation catches most issues.

### R-11: tufup Library Becomes Unmaintained
- **Severity**: Medium | **Likelihood**: Medium
- **Description**: tufup, like its predecessors PyUpdater and Esky, could become unmaintained in the future.
- **Mitigation**:
  1. **Loose coupling**: The update system's interface to tufup is isolated in `integrity.py` and `update_checker.py`. Replacing tufup requires changes to only these two files.
  2. **Core logic is custom**: The update checker, downloader, rollback manager, and UI integration are all custom code that does not depend on tufup's high-level API.
  3. **Fallback to manual verification**: If tufup is dropped, SHA-256 verification alone provides reasonable security for this application's threat model.
- **Residual Risk**: Low — modular design limits blast radius.

### R-12: Backward Compatibility Break in Config Format
- **Severity**: Medium | **Likelihood**: Low
- **Description**: A future update changes the `config.json` schema in a way that causes the old version (after rollback) to fail to read it.
- **Mitigation**:
  1. **Schema versioning**: Add a `"config_version"` field to `config.json`.
  2. **Forward-compatible writes**: New versions must write config in a format that old versions can still read (ignore unknown fields).
  3. **Migration scripts**: Version-specific migration functions in the update manager.
  4. **Config backup**: Config is always backed up before update, so rollback restores the old config too.
- **Residual Risk**: Very Low — defensive coding + backup provides multiple safety nets.

---

## Low Risks

### R-13: Excessive Disk Usage from Backups
- **Severity**: Low | **Likelihood**: Medium
- **Description**: Accumulated backup versions consume significant disk space over time.
- **Mitigation**:
  1. **Retention policy**: Keep only the last 3 backup versions (configurable via `MAX_BACKUP_VERSIONS`).
  2. **Automatic cleanup**: Oldest backups are deleted after successful update + 7-day grace period.
  3. **Size monitoring**: Log total backup directory size on startup.
- **Residual Risk**: Very Low.

### R-14: User Defers Updates Indefinitely
- **Severity**: Low | **Likelihood**: Low
- **Description**: Users dismiss update notifications repeatedly, running increasingly outdated versions.
- **Mitigation**:
  1. **Non-aggressive approach**: Updates are always optional (except if `forced_update_below` is set for critical security patches).
  2. **Persistent but polite**: Show the notification once per session, not repeatedly.
  3. **Critical update override**: For genuine security emergencies, the manifest can set `"is_critical": true` which shows a more prominent (but still dismissible) warning.
- **Residual Risk**: Low — acceptable trade-off for user autonomy.

### R-15: Update System Increases Application Startup Time
- **Severity**: Low | **Likelihood**: Low
- **Description**: Network calls during startup delay the loading screen transition.
- **Mitigation**:
  1. **Async check**: Update check runs on a background QThread, never blocking the UI.
  2. **Timeout**: Update check has a 5-second network timeout. On failure, the app proceeds normally.
  3. **Cached result**: If a recent check (< 24h) exists in `update_state.json`, skip the network call entirely.
- **Residual Risk**: Very Low — update check adds < 1 second to startup in worst case.

---

## Risk Summary

| Risk Level | Count | Key Takeaway |
|-----------|-------|-------------|
| Critical | 4 | All mitigated to Low/Very Low residual risk via backup + verification + TUF |
| High | 4 | File locking (solved via external script), AV blocking (mitigated by code signing) |
| Medium | 4 | Mostly operational (rate limits, CI/CD errors) — mitigated by caching and validation |
| Low | 3 | Acceptable trade-offs (disk usage, user deferral, startup time) |

**Overall Assessment**: The proposed architecture addresses all identified risks with multiple layers of defense. The highest residual risk is antivirus interference (R-07), which is partially outside our control but mitigated by code signing and clear documentation.

---

> **Next**: See [03-security-considerations.md](./03-security-considerations.md) for the security model.
