# 00 — Master Architecture Plan: Application Update & Patching System

> **Version**: 1.0.0 | **Target Application**: Camplife DataLoader v1.1.0  
> **Status**: PLANNING — Do not implement without explicit approval  
> **Created**: 2026-05-27

---

## 1. Executive Summary

This document defines the complete architecture for adding a production-grade, secure update and patching system to the Camplife DataLoader desktop application. The system will allow end users to seamlessly receive incremental updates, hotfixes, feature patches, and full application overhauls through secure remote delivery while preserving application stability, user data integrity, rollback safety, and long-term maintainability.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Update framework | **tufup** (The Update Framework for Python) | Industry-standard security via TUF; active maintenance; PyInstaller compatible; replaces deprecated PyUpdater/Esky |
| Update hosting | **GitHub Releases** (primary) + **Firebase Hosting** (fallback/CDN) | Free tier sufficient; global CDN; HTTPS included; API-queryable |
| Update model | **Passive check → Background download → User-initiated apply** | Non-disruptive; preserves user control; handles locked executables |
| Rollback strategy | **Local version archive + manifest-based restore** | Instant recovery; no network dependency for rollback |
| Authentication | **Google OAuth 2.0 via Firebase Auth** (optional, Phase 3+) | Free tier; low complexity; aligns with Google ecosystem |
| Patching strategy | **Binary diff patches (bsdiff) + Full archive fallback** | Bandwidth-efficient for incremental updates; full archive for major versions |

---

## 2. Existing Application Audit

### 2.1 Application Profile

```
Application:     Camplife DataLoader
Version:         1.1.0
Platform:        Windows 10+ (desktop only)
Language:        Python 3.9+
GUI Framework:   PySide6 (Qt 6)
Packaging:       PyInstaller (directory mode, not single-file)
Distribution:    Manual executable distribution (dist/Camplife DataLoader/)
```

### 2.2 Current Architecture (Pre-Update System)

```
camplife_dataloader/
├── main.py                     # Entry point (QApplication bootstrap)
├── config.py                   # VERSION, API URLs, runtime paths (APP_DIR detection)
├── config.json                 # User credentials (encrypted, machine-specific)
├── cache.json                  # Cached resort/membership data
├── requirements.txt            # 5 dependencies (PySide6, requests, pandas, openpyxl, cryptography)
├── build.bat                   # PyInstaller build automation
├── Camplife DataLoader.spec    # PyInstaller spec (hidden imports for openpyxl)
├── src/
│   ├── api/
│   │   ├── client.py           # CamplifeAPIClient (QObject, singleton-like, thread-safe token refresh)
│   │   ├── workers.py          # AuthWorker (QThread for HMAC-SHA256 auth)
│   │   └── auth_utils.py       # Shared HMAC auth + credential loading helpers
│   ├── core/
│   │   ├── uploader.py         # UploadWorker (QThread, row-by-row API upload, pause/cancel)
│   │   ├── security.py         # Machine-specific Fernet encryption (MAC-address derived key)
│   │   └── logger.py           # Rotating file logger (1MB, 3 backups)
│   └── gui/
│       ├── main_window.py      # FramelessCamplifeLoader (custom title bar, drag-to-move)
│       ├── themes.py           # Light/dark QSS stylesheets + SVG icon constants
│       ├── loading_screen.py   # Translucent splash screen
│       ├── setup_dialog.py     # API credential setup
│       ├── preview_dialog.py   # Data preview + upload table + response inspector
│       └── progress_dialog.py  # Upload progress with ETA + cancel
├── tests/                      # Test suite + QA plan
├── docs/                       # Architecture, roadmap, version history, update protocol
└── logs/                       # Rotating application logs
```

### 2.3 Critical Observations for Update Integration

| Aspect | Current State | Integration Impact |
|--------|---------------|-------------------|
| **Version tracking** | `VERSION` in `config.py` (string literal `"1.1.0"`) | ✅ Ready — can compare against remote manifest |
| **Path resolution** | `APP_DIR` uses `sys.executable` (frozen) or `__file__` (dev) | ⚠️ Must ensure update paths respect this dual-mode detection |
| **User data** | `config.json` (credentials), `cache.json` (API cache), `logs/` (log files) | ⚠️ Must be preserved across all updates; never overwritten |
| **Build system** | `build.bat` + `.spec` file | ✅ Can extend for update artifact generation |
| **Dependencies** | 5 pip packages; `cryptography` already present | ✅ Can add `tufup` and `bsdiff4` without conflict |
| **Security model** | Machine-specific Fernet encryption (MAC-derived key) | ⚠️ Known limitation: key changes on NIC change. Does not affect update system. |
| **Packaging** | PyInstaller directory mode (not single-file) | ✅ Compatible with tufup; entire directory is the "bundle" |
| **Existing HTTP client** | `requests` library already a dependency | ✅ Can reuse for update checks without adding dependencies |
| **Threading model** | QThread-based workers with Qt signals | ✅ Update checker can follow the same pattern |
| **File locking** | Windows locks running `.exe` and `.dll` files | ⚠️ Must use external updater script to swap files while app is closed |

### 2.4 Files That Must NEVER Be Modified by Updates

These files contain user-generated data and must be explicitly excluded from all update operations:

```
config.json      → Encrypted API credentials + resort alias
cache.json       → Cached resort/membership data (regenerable, but user-convenient)
logs/            → Application log files (rotating, user diagnostic data)
*.xlsx           → Upload log files (user-generated operation records)
```

---

## 3. Update System Architecture

### 3.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CAMPLIFE DATALOADER APPLICATION                  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │  main.py     │  │  config.py   │  │  src/update/            │  │
│  │  (bootstrap) │  │  VERSION     │──│                         │  │
│  │              │──│  APP_DIR     │  │  update_checker.py      │  │
│  └──────────────┘  └──────────────┘  │    (UpdateChecker)      │  │
│         │                             │    → QThread worker     │  │
│         │                             │    → version compare    │  │
│  ┌──────▼──────┐                     │    → metadata verify    │  │
│  │  src/gui/   │                     │                         │  │
│  │             │  signals            │  update_manager.py      │  │
│  │ main_window │◄════════════════════│    (UpdateManager)      │  │
│  │   (UI bar,  │                     │    → download handler   │  │
│  │   notifier) │                     │    → integrity verify   │  │
│  └─────────────┘                     │    → apply orchestrator │  │
│                                      │                         │  │
│                                      │  update_config.py       │  │
│                                      │    (URLs, channels,     │  │
│                                      │     paths, constants)   │  │
│                                      │                         │  │
│                                      │  rollback_manager.py    │  │
│                                      │    (backup, restore,    │  │
│                                      │     manifest tracking)  │  │
│                                      └─────────────────────────┘  │
│                                                │                    │
│                                      ┌─────────▼─────────┐        │
│                                      │  scripts/          │        │
│                                      │  apply_update.bat  │        │
│                                      │  (external updater │        │
│                                      │   swap-and-restart) │       │
│                                      └───────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    HTTPS (TLS 1.3)
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                     REMOTE UPDATE SERVER                            │
│                                                                     │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐  │
│  │  GitHub Releases    │    │  Firebase Hosting (CDN)          │  │
│  │                     │    │                                  │  │
│  │  • Release metadata │    │  • update-manifest.json          │  │
│  │  • Binary archives  │    │  • version-catalog.json          │  │
│  │  • Checksums        │    │  • TUF metadata (root.json etc)  │  │
│  │  • Patch diffs      │    │  • Patch/archive mirror          │  │
│  │  • Changelogs       │    │                                  │  │
│  └─────────────────────┘    └──────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  GitHub Actions (CI/CD Pipeline)                             │  │
│  │                                                              │  │
│  │  • Build on tag push → PyInstaller                           │  │
│  │  • Generate checksums (SHA-256)                              │  │
│  │  • Create binary diff patches (bsdiff)                       │  │
│  │  • Sign TUF metadata                                         │  │
│  │  • Upload to GitHub Releases                                 │  │
│  │  • Deploy manifest to Firebase Hosting                       │  │
│  │  • Run automated tests                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 New Module: `src/update/`

This is the sole new package added to the project. All update logic is encapsulated here to maintain the existing module boundaries.

```
src/update/
├── __init__.py              # Package marker
├── update_config.py         # Constants: URLs, paths, channels, intervals
├── update_checker.py        # UpdateChecker (QThread) — polls for new versions
├── update_manager.py        # UpdateManager (QObject) — orchestrates download + apply
├── rollback_manager.py      # RollbackManager — backup/restore/manifest
├── version_utils.py         # Semantic version parsing + comparison
└── integrity.py             # SHA-256 checksum verification + TUF metadata validation
```

### 3.3 Data Flow: Update Lifecycle

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ App Boot │────▶│ Check Remote │────▶│ Compare      │────▶│ Update   │
│          │     │ Manifest     │     │ Versions     │     │ Available│
└─────────┘     └──────────────┘     └──────────────┘     └────┬─────┘
                                                               │
                      ┌────────────────────────────────────────┘
                      │
               ┌──────▼──────┐     ┌──────────────┐     ┌──────────────┐
               │ Background  │────▶│ Verify       │────▶│ Stage in     │
               │ Download    │     │ Integrity    │     │ Temp Dir     │
               └─────────────┘     └──────────────┘     └──────┬───────┘
                                                               │
                      ┌────────────────────────────────────────┘
                      │
               ┌──────▼──────┐     ┌──────────────┐     ┌──────────────┐
               │ Notify User │────▶│ User Clicks  │────▶│ Backup       │
               │ (Status Bar)│     │ "Update Now" │     │ Current Ver  │
               └─────────────┘     └──────────────┘     └──────┬───────┘
                                                               │
                      ┌────────────────────────────────────────┘
                      │
               ┌──────▼──────┐     ┌──────────────┐     ┌──────────────┐
               │ Launch      │────▶│ Swap Files   │────▶│ Restart App  │
               │ apply_update│     │ (old → new)  │     │ (new version)│
               │ .bat        │     │              │     │              │
               └─────────────┘     └──────────────┘     └──────┬───────┘
                                                               │
                      ┌────────────────────────────────────────┘
                      │
               ┌──────▼──────┐     ┌──────────────┐
               │ Post-Update │────▶│ Verify       │
               │ Health Check│     │ Success      │
               └─────────────┘     └──────────────┘
```

### 3.4 Update Manifest Schema

The remote manifest is the single source of truth for available updates. It is a JSON file hosted on both GitHub Releases and Firebase Hosting.

```json
{
  "schema_version": 1,
  "application": "camplife-dataloader",
  "latest": {
    "version": "1.2.0",
    "channel": "stable",
    "release_date": "2026-06-15T00:00:00Z",
    "min_app_version": "1.0.0",
    "changelog_url": "https://github.com/owner/repo/releases/tag/v1.2.0",
    "changelog_summary": "Added auto-update system and improved error handling.",
    "is_critical": false,
    "assets": {
      "full_archive": {
        "url": "https://github.com/owner/repo/releases/download/v1.2.0/camplife-dataloader-1.2.0-win64.zip",
        "sha256": "abc123...",
        "size_bytes": 52428800
      },
      "patch_from": {
        "1.1.0": {
          "url": "https://github.com/owner/repo/releases/download/v1.2.0/patch-1.1.0-to-1.2.0.bsdiff",
          "sha256": "def456...",
          "size_bytes": 2097152
        }
      }
    }
  },
  "supported_versions": ["1.0.0", "1.1.0", "1.2.0"],
  "deprecated_versions": [],
  "forced_update_below": null,
  "manifest_signature": "base64-encoded-signature..."
}
```

### 3.5 Version Catalog Schema

A companion file tracking all historical versions for rollback and compatibility:

```json
{
  "versions": [
    {
      "version": "1.2.0",
      "release_date": "2026-06-15",
      "channel": "stable",
      "breaking_changes": false,
      "requires_config_migration": false,
      "assets_url": "https://github.com/owner/repo/releases/tag/v1.2.0"
    },
    {
      "version": "1.1.0",
      "release_date": "2026-05-15",
      "channel": "stable",
      "breaking_changes": false,
      "requires_config_migration": false,
      "assets_url": "https://github.com/owner/repo/releases/tag/v1.1.0"
    }
  ]
}
```

---

## 4. Integration Points

### 4.1 Safest Integration Points (Ordered by Risk)

| Priority | Integration Point | File | Change Description | Risk |
|----------|------------------|------|-------------------|------|
| 1 | Version constant | `config.py` | Already exists as `VERSION = "1.1.0"` — no change needed | None |
| 2 | New update package | `src/update/` (new) | Entirely new package — zero impact on existing code | None |
| 3 | Build script extension | `build.bat` | Add post-build step to generate checksums + manifest | Low |
| 4 | PyInstaller spec | `Camplife DataLoader.spec` | Add `tufup` root metadata to `datas` list | Low |
| 5 | Main window UI | `src/gui/main_window.py` | Add update notification widget to status bar area | Low |
| 6 | Entry point bootstrap | `main.py` | Add update checker initialization after app startup | Low |
| 7 | Requirements | `requirements.txt` | Add `tufup` and `bsdiff4` dependencies | Low |
| 8 | External updater script | `scripts/apply_update.bat` (new) | New file — handles file swap while app is closed | None |

### 4.2 Files That Will NOT Be Modified

The following existing files require zero modifications:

```
src/api/client.py          # API client — completely independent of update system
src/api/workers.py         # Auth worker — no update interaction
src/api/auth_utils.py      # Auth utilities — no update interaction
src/core/uploader.py       # Upload engine — no update interaction
src/core/security.py       # Encryption — no update interaction
src/core/logger.py         # Logger — reused as-is (update module gets own logger)
src/gui/themes.py          # Theme stylesheets — no update interaction
src/gui/loading_screen.py  # Splash screen — no update interaction
src/gui/setup_dialog.py    # Setup dialog — no update interaction
src/gui/preview_dialog.py  # Preview dialog — no update interaction
src/gui/progress_dialog.py # Progress dialog — no update interaction
config.json                # User data — explicitly protected
cache.json                 # User data — explicitly protected
```

---

## 5. Update Delivery Models Evaluation

### 5.1 Model Comparison

| Model | Bandwidth Cost | User Friction | Complexity | Rollback Ease | Recommendation |
|-------|---------------|---------------|------------|---------------|----------------|
| **Full archive replacement** | High (50+ MB per update) | Low (one download) | Low | High (keep old archive) | ✅ For major versions |
| **Binary diff patches (bsdiff)** | Very Low (1-5 MB typical) | Low (transparent) | Medium | Medium (need base + patch) | ✅ For minor/patch updates |
| **In-place file replacement** | Medium | Medium | High | Low (partial state) | ❌ Risky on Windows (file locking) |
| **MSI/MSIX installer** | Medium | Higher (install wizard) | High | Medium (Windows rollback) | ❌ Over-engineered for this app |
| **Delta updates (rsync-style)** | Low | Low | Very High | Low | ❌ Too complex for scope |

### 5.2 Recommended Hybrid Strategy

```
┌──────────────────────────────────────────────────────────────┐
│                    UPDATE DECISION TREE                        │
│                                                               │
│  Is update MAJOR (X.0.0)?                                     │
│  ├── YES → Full archive download + replace                    │
│  │         (complete application overhaul)                     │
│  │                                                            │
│  └── NO → Is binary diff patch available for user's version?  │
│       ├── YES → Download patch + apply (bandwidth efficient)  │
│       │                                                       │
│       └── NO → Fall back to full archive download             │
│                (user is too many versions behind)              │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. External Updater Script Design

Because Windows locks running executables, the actual file swap must happen outside the main application process. A lightweight batch script handles this:

### `scripts/apply_update.bat`

```
Purpose:
  1. Wait for main application process to exit
  2. Back up current application directory
  3. Apply update (extract new archive or apply patch)
  4. Preserve user data files (config.json, cache.json, logs/)
  5. Restart the updated application
  6. If anything fails → restore backup automatically

Arguments:
  %1 = PID of the application process to wait for
  %2 = Path to staged update archive/patch
  %3 = Path to application directory
  %4 = Path to backup directory
```

---

## 7. User Experience Design

### 7.1 Update Notification Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  🏕️ Camplife Data Loader v1.1.0          [Resort] [Connect]    │
│                                    [⚙️ Setup] [🌓 Theme] [_][□][X] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [File Upload & Column Mapping]                                 │
│  [Optional Overrides]                                           │
│  [Review and Upload]                                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Ready                                 ✔ Connected              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  ⬆️ Update Available: v1.2.0              [Update Now]│      │
│  │     "Added auto-update system and improved error..."  │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Update States

| State | UI Behavior | User Action Required |
|-------|------------|---------------------|
| **Checking** | Spinner in status bar: "Checking for updates..." | None |
| **Up to date** | Brief message: "✔ You're up to date" (auto-dismiss 3s) | None |
| **Available** | Persistent banner above status bar with version + summary | Optional: click "Update Now" |
| **Downloading** | Progress bar in banner: "Downloading v1.2.0... 45%" | Optional: click "Cancel" |
| **Ready** | Banner: "⬆️ v1.2.0 ready to install. [Restart to Update]" | Click "Restart to Update" |
| **Applying** | App closes; batch script shows brief console window | Wait ~5-15 seconds |
| **Failed** | Dialog on next launch: "Update failed. Running previous version." | Acknowledge |
| **Rolled back** | Dialog: "Update was reverted to v1.1.0 due to startup failure." | Acknowledge |

---

## 8. Configuration & Settings

### 8.1 Update Configuration (`src/update/update_config.py`)

```python
# Update system constants
UPDATE_CHECK_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
UPDATE_MANIFEST_URL = "https://{project}.web.app/update-manifest.json"
UPDATE_CHECK_INTERVAL_HOURS = 24  # Check once per day on app startup
UPDATE_STAGING_DIR = os.path.join(APP_DIR, ".updates")
UPDATE_BACKUP_DIR = os.path.join(APP_DIR, ".backups")
UPDATE_CHANNEL = "stable"  # stable | beta | dev

# Files to preserve during updates (never overwritten)
PROTECTED_FILES = [
    "config.json",
    "cache.json",
    "logs/",
]

# Maximum number of backup versions to retain
MAX_BACKUP_VERSIONS = 3
```

### 8.2 Local State File (`update_state.json`)

Stored in `APP_DIR/.updates/update_state.json`:

```json
{
  "last_check": "2026-06-15T10:30:00Z",
  "last_check_result": "update_available",
  "staged_version": "1.2.0",
  "staged_archive_path": ".updates/camplife-dataloader-1.2.0-win64.zip",
  "staged_archive_sha256": "abc123...",
  "current_version": "1.1.0",
  "update_history": [
    {
      "from": "1.0.0",
      "to": "1.1.0",
      "date": "2026-05-15T00:00:00Z",
      "method": "full_archive",
      "success": true
    }
  ],
  "user_deferred_version": null,
  "channel": "stable"
}
```

---

## 9. Dependency Impact

### 9.1 New Dependencies

| Package | Version | Purpose | Size Impact | License |
|---------|---------|---------|-------------|---------|
| `tufup` | ≥ 1.0.0 | Secure update framework (TUF-based) | ~2 MB | MIT |
| `bsdiff4` | ≥ 1.2.0 | Binary diff/patch for incremental updates | ~0.5 MB | BSD |

### 9.2 Existing Dependencies (No Changes)

| Package | Currently Used For | Also Used By Update System |
|---------|-------------------|--------------------------|
| `requests` | Camplife API calls | Update manifest fetch, archive download |
| `cryptography` | Fernet credential encryption | TUF signature verification (via tufup) |

### 9.3 Updated `requirements.txt`

```
PySide6>=6.0.0
requests>=2.25.0
pandas>=1.2.0
openpyxl>=3.0.0
cryptography>=42.0.0
tufup>=1.0.0
bsdiff4>=1.2.0
```

---

## 10. Build Pipeline Changes

### 10.1 Current Pipeline

```
Developer → build.bat → PyInstaller → dist/Camplife DataLoader/ → Manual distribution
```

### 10.2 Updated Pipeline

```
Developer → git tag vX.Y.Z → GitHub Actions trigger
                                    │
                              ┌─────▼─────┐
                              │ Build Step │
                              │ PyInstaller│
                              └─────┬─────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐ ┌──────▼──────┐ ┌──────▼──────┐
              │ Checksum   │ │ Patch Gen   │ │ TUF Metadata│
              │ SHA-256    │ │ bsdiff      │ │ Sign + Push │
              └─────┬─────┘ └──────┬──────┘ └──────┬──────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                              ┌─────▼─────┐
                              │ GitHub     │
                              │ Release    │
                              │ + Firebase │
                              │ Deploy     │
                              └───────────┘
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

| Test | Module | Validates |
|------|--------|-----------|
| `test_version_utils.py` | `version_utils.py` | Semantic version parsing, comparison, ordering |
| `test_integrity.py` | `integrity.py` | SHA-256 verification, corrupted file detection |
| `test_update_checker.py` | `update_checker.py` | Manifest parsing, version comparison, network error handling |
| `test_rollback_manager.py` | `rollback_manager.py` | Backup creation, restore, manifest tracking, cleanup |

### 11.2 Integration Tests

| Test | Validates |
|------|-----------|
| Full update cycle (mock server) | Check → Download → Stage → Apply → Verify |
| Rollback on startup failure | Corrupted update → automatic restore → healthy launch |
| Protected file preservation | `config.json` and `cache.json` survive update |
| Patch application | bsdiff patch applies correctly to known version |
| Network failure recovery | Interrupted download resumes or retries cleanly |

### 11.3 Manual QA (Extension to existing `tests/qa_test_plan.md`)

Add Phase 5: Update System to the existing QA test plan.

---

## 12. Future Scalability

This architecture is designed to scale beyond a single application:

| Capability | Current Design | Future Extension |
|-----------|---------------|-----------------|
| Multi-app fleet | Single manifest per app | Manifest registry with app-id routing |
| Update channels | `stable` only | `stable`, `beta`, `dev` channels with user opt-in |
| Telemetry | None | Optional anonymous update success/failure reporting |
| Forced updates | `forced_update_below` field (unused) | Enforce minimum version for critical security patches |
| Config migration | Not needed (v1.x compatible) | Versioned config schema with automated migration scripts |
| Cross-platform | Windows only | macOS/Linux updater scripts + platform-specific archive formats |

---

> **Next**: See [01-implementation-phases.md](./01-implementation-phases.md) for the phased rollout plan.
