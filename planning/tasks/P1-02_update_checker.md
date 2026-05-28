# Task P1-02: Implement `update_checker.py` — UpdateChecker QThread Worker

> **Phase**: 1 — Core Logic | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The UpdateChecker is a background QThread worker that checks for available updates by fetching the remote update manifest and comparing versions. It follows the exact same threading pattern used throughout the Camplife DataLoader:

- `src/api/workers.py:AuthWorker` — QThread that authenticates with the Camplife API
- `src/core/uploader.py:UploadWorker` — QThread that uploads data row by row

The UpdateChecker must be non-blocking (never freeze the GUI), resilient to network failures, and respect the check interval to avoid excessive API calls.

### Architectural Intent

- **Consistency**: Follow the exact QThread + Signal pattern used by `AuthWorker` and `UploadWorker`
- **Non-disruptive**: Network failures are logged and silently ignored — the app continues normally
- **Cacheable**: Results are cached in `update_state.json` to avoid redundant network calls
- **Testable**: Network calls are isolated behind a method that can be mocked in tests

---

## Affected Files

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/update/update_checker.py` | Replace placeholder | QThread worker for checking remote update manifest |

### Files to Create (Tests)

| File | Purpose |
|------|---------|
| `tests/test_update_checker.py` | Unit tests with mocked HTTP responses |

### Existing Files — NO Modifications

No existing files are modified.

---

## Dependencies & Prerequisites

- **P0-01**: `src/update/` package must exist
- **P0-09**: `version_utils.py` must be implemented (for `is_update_available()`)
- **P1-01**: `integrity.py` must be implemented (for manifest hash verification, optional in Phase 1)
- **Existing**: `requests` library (already a project dependency)
- **Existing**: `PySide6.QtCore.QThread` (already a project dependency)

---

## Implementation Details

### Class Design

```python
"""
UpdateChecker — Background worker that checks for available updates.

Fetches the remote update manifest, compares versions, and emits signals
to notify the GUI of the result. Never blocks the main thread.

Threading pattern matches src/api/workers.py:AuthWorker.
"""
import json
import time
import logging
import requests
from PySide6.QtCore import QThread, Signal

from config import VERSION
from src.update.update_config import (
    UPDATE_CHECK_URL_PRIMARY,
    UPDATE_CHECK_URL_FALLBACK,
    UPDATE_CHECK_TIMEOUT_SECONDS,
    UPDATE_CHECK_INTERVAL_HOURS,
    UPDATE_STATE_FILE,
    UPDATE_STAGING_DIR,
)
from src.update.version_utils import is_update_available, AppVersion

logger = logging.getLogger("camplife.update.checker")


class UpdateCheckResult:
    """Data class for update check results."""
    def __init__(self):
        self.update_available: bool = False
        self.latest_version: str = ""
        self.changelog_summary: str = ""
        self.download_url: str = ""
        self.download_size: int = 0
        self.sha256: str = ""
        self.is_critical: bool = False
        self.patch_available: bool = False
        self.patch_url: str = ""
        self.patch_sha256: str = ""
        self.patch_size: int = 0
        self.error: str = ""


class UpdateChecker(QThread):
    """
    Background worker to check for application updates.
    
    Signals:
        check_complete(UpdateCheckResult): Emitted when check finishes (success or failure)
        status_msg(str): Emitted with human-readable status messages
    
    Usage:
        checker = UpdateChecker()
        checker.check_complete.connect(on_check_result)
        checker.start()
    """
    check_complete = Signal(object)  # UpdateCheckResult
    status_msg = Signal(str)

    def __init__(self, force: bool = False):
        """
        Args:
            force: If True, skip the interval check and always fetch from remote.
                   If False, respect UPDATE_CHECK_INTERVAL_HOURS.
        """
        super().__init__()
        self._force = force

    def run(self):
        """Main thread entry point. Do not call directly — use start()."""
        result = UpdateCheckResult()
        
        try:
            # 1. Check if we should skip (recent check exists)
            if not self._force and self._is_recent_check_available():
                result = self._load_cached_result()
                self.check_complete.emit(result)
                return

            self.status_msg.emit("Checking for updates...")

            # 2. Fetch manifest (primary, then fallback)
            manifest = self._fetch_manifest()
            if manifest is None:
                result.error = "Could not reach update server"
                self.check_complete.emit(result)
                return

            # 3. Parse and compare versions
            result = self._parse_manifest(manifest)

            # 4. Save result to cache
            self._save_check_result(result)

            self.check_complete.emit(result)

        except Exception as e:
            logger.exception("Update check failed")
            result.error = str(e)
            self.check_complete.emit(result)

    def _is_recent_check_available(self) -> bool:
        """Check if a recent check result exists within the interval."""
        # Read update_state.json, check last_check timestamp
        # Return True if last_check < UPDATE_CHECK_INTERVAL_HOURS ago
        ...

    def _load_cached_result(self) -> UpdateCheckResult:
        """Load the cached check result from update_state.json."""
        ...

    def _fetch_manifest(self) -> dict | None:
        """
        Fetch the update manifest from remote.
        Tries primary URL first, falls back to secondary.
        Returns parsed JSON dict or None on failure.
        """
        for url_template in [UPDATE_CHECK_URL_PRIMARY, UPDATE_CHECK_URL_FALLBACK]:
            try:
                # Note: URL templates contain {owner}/{repo}/{project} placeholders
                # These should be filled in update_config.py when repo is created
                url = url_template  # Will be formatted with actual values
                
                response = requests.get(
                    url,
                    timeout=UPDATE_CHECK_TIMEOUT_SECONDS,
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Update manifest fetched from {url}")
                    return response.json()
                else:
                    logger.warning(f"Update manifest fetch returned {response.status_code} from {url}")
                    
            except requests.Timeout:
                logger.warning(f"Update manifest fetch timed out from {url}")
            except requests.RequestException as e:
                logger.warning(f"Update manifest fetch failed from {url}: {e}")
            except json.JSONDecodeError:
                logger.warning(f"Update manifest contained invalid JSON from {url}")

        return None

    def _parse_manifest(self, manifest: dict) -> UpdateCheckResult:
        """
        Parse the update manifest and determine if an update is available.
        
        Expected manifest format (see 00-master-architecture-plan.md Section 3.4):
        {
            "latest": {
                "version": "1.2.0",
                "changelog_summary": "...",
                "is_critical": false,
                "assets": {
                    "full_archive": { "url": "...", "sha256": "...", "size_bytes": ... },
                    "patch_from": { "1.1.0": { "url": "...", "sha256": "...", "size_bytes": ... } }
                }
            }
        }
        """
        result = UpdateCheckResult()
        
        latest = manifest.get("latest", {})
        remote_version = latest.get("version", "")
        
        if not remote_version:
            result.error = "Manifest missing version field"
            return result
        
        result.latest_version = remote_version
        result.changelog_summary = latest.get("changelog_summary", "")
        result.is_critical = latest.get("is_critical", False)
        
        try:
            result.update_available = is_update_available(VERSION, remote_version)
        except ValueError as e:
            logger.error(f"Version comparison failed: {e}")
            result.error = f"Invalid version format: {e}"
            return result

        if result.update_available:
            assets = latest.get("assets", {})
            
            # Full archive (always available)
            full = assets.get("full_archive", {})
            result.download_url = full.get("url", "")
            result.sha256 = full.get("sha256", "")
            result.download_size = full.get("size_bytes", 0)
            
            # Patch (available only from specific versions)
            patches = assets.get("patch_from", {})
            if VERSION in patches:
                patch = patches[VERSION]
                result.patch_available = True
                result.patch_url = patch.get("url", "")
                result.patch_sha256 = patch.get("sha256", "")
                result.patch_size = patch.get("size_bytes", 0)
            
            logger.info(f"Update available: {VERSION} → {remote_version} (patch: {result.patch_available})")
        else:
            logger.info(f"Application is up to date ({VERSION})")

        return result

    def _save_check_result(self, result: UpdateCheckResult):
        """Save the check result and timestamp to update_state.json."""
        ...
```

### Signal Connection Pattern (for reference — implemented in P2-03)

```python
# In main.py (Phase 2):
checker = UpdateChecker()
checker.check_complete.connect(on_update_check_result)
checker.status_msg.connect(window.update_status)
checker.start()
```

---

## Validation Requirements

1. **Unit tests pass**: `python -m pytest tests/test_update_checker.py -v`
2. **Mock test**: UpdateChecker correctly parses a mock manifest and returns `update_available=True`
3. **Network failure**: UpdateChecker handles timeout/connection error gracefully (returns error, no crash)
4. **Interval caching**: When a recent check exists, UpdateChecker skips the network call
5. **No regressions**: Existing tests still pass

---

## Expected Outcomes

- `UpdateChecker` follows the established QThread pattern (consistent with AuthWorker/UploadWorker)
- Network failures are graceful — logged and silently handled
- Results are cached to avoid redundant network calls
- Primary/fallback URL pattern provides resilience

---

## Testing Expectations

Create `tests/test_update_checker.py` with mocked HTTP responses (use `unittest.mock.patch` to mock `requests.get`):

| Test Case | Mock Response | Expected |
|-----------|-------------|----------|
| Update available | Manifest with version > current | `update_available=True` |
| No update | Manifest with version == current | `update_available=False` |
| Older version on remote | Manifest with version < current | `update_available=False` |
| Patch available | Manifest with patch_from matching current version | `patch_available=True` |
| No patch available | Manifest without patch for current version | `patch_available=False, download_url set` |
| Network timeout (primary) | Primary times out, fallback succeeds | Result from fallback |
| Network timeout (both) | Both URLs time out | `error` field set, no crash |
| Invalid JSON | Response body is not JSON | `error` field set, no crash |
| Missing version field | Manifest without "version" | `error` field set |
| Invalid version format | Manifest with "abc" as version | `error` field set |
| Cached result used | Recent check in state file | Network not called, cached result returned |
| Force check | `force=True` with recent cache | Network called despite cache |
| Critical update flag | Manifest with `is_critical: true` | `is_critical=True` |

---

## Reasoning

**Why QThread instead of `asyncio` or `threading.Thread`?**

The Camplife DataLoader exclusively uses PySide6's QThread for all background work (AuthWorker, UploadWorker). Using `asyncio` or `threading.Thread` would introduce an inconsistent concurrency model and require new signal/callback patterns. QThread integrates natively with Qt's signal/slot system, which is already the application's event bus.

**Why primary + fallback URLs?**

GitHub's API has a 60 request/hour rate limit for unauthenticated requests. For most users this is fine (one check per day), but in corporate environments where many users share an IP (NAT), rate limiting is a real risk. Firebase Hosting has no such rate limit and serves from a global CDN, making it an ideal fallback.

**Why cache results in `update_state.json`?**

Without caching, every app launch triggers a network request. This adds startup latency (even with async), increases the chance of hitting rate limits, and wastes bandwidth. A 24-hour cache interval means the app checks at most once per day — sufficient for a desktop tool that doesn't need real-time update notifications.
