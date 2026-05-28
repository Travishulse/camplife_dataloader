# Camplife DataLoader — Version History

> Versioning follows [Semantic Versioning 2.0.0](https://semver.org):
> - **MAJOR** — Breaking changes to interfaces, config format, or data flow.
> - **MINOR** — New features added in a backward-compatible manner.
> - **PATCH** — Backward-compatible bug fixes.

---

## Patch Notes Format

All entries follow this structure:

```
## [vX.Y.Z] - YYYY-MM-DD
### Added
- New features or capabilities
### Updated
- Changes to existing features
### Fixed
- Bug fixes
### Removed
- Deprecated code or features
```

---

## [v1.1.0] - 2026-05-15

### Added
- **Dedicated upload logs directory** — Upload log files (`Camplife_Upload_Log_*.xlsx`) are now saved to `APP_DIR/logs/` instead of the current working directory, ensuring consistent file placement across source and packaged executable environments.
- **File-based logging framework** — New `src/core/logger.py` module with rotating file handler (1 MB max, 3 backups). Logs all authentication, API retry attempts, and upload processing to `logs/camplife_dataloader.log`. Log level defaults to `INFO`; enable `DEBUG` with `--debug` flag or `CAMPLIFE_DEBUG=1` environment variable. Log format includes ISO 8601 timestamps and module-level loggers for organization (`camplife.auth`, `camplife.api`, `camplife.upload`).
- **Token auto-refresh during upload** — New `src/api/auth_utils.py` module with shared HMAC authentication and credential loading helpers. `CamplifeAPIClient` now includes a synchronous `refresh_token_sync()` method that is safe to call from background threads (uses `threading.Lock` for thread safety). On 401/403 errors during upload, the client automatically attempts to refresh the token and retry the request before giving up. This resolves the limitation where long uploads (>1 hour) would fail when tokens expired.
- **Row validation pre-upload** — New `validate_dataframe()` function in `src/core/uploader.py` validates rows for required fields (Camplife ID, Member Number, Membership Type, Effective From) before upload begins. Invalid rows are highlighted with a red background (`#FFE0E0`) in the preview table, and a warning dialog lists each invalid row number with specific missing field names. Users can choose to proceed with the upload anyway or cancel.

### Updated
- **Preview Data dialog** now displays only the utilized fields (Camplife ID, Member Number, Membership Type, Effective From, Effective To, Tag, Note) instead of every column from the loaded file. Columns whose mapping is set to `N/A` and have no override are hidden.
- **Override visibility** — when a global override is set for Membership Type, Tag, or Note, the corresponding preview column header is suffixed with `(Override)` and every row shows the override value, making it visually clear that the override replaces per-row data.
- **Configuration** — Added `LOG_DIR` constant to `config.py` for centralized log directory management.
- **API Client logging** — `src/api/client.py` now logs all retry attempts, 401/403 credential errors, and request exceptions.
- **Auth Worker logging** — `src/api/workers.py` now logs authentication steps, resort/membership loading, and validation failures.
- **Upload Worker logging** — `src/core/uploader.py` now logs row processing start, missing field warnings, and upload exceptions.

---

## [v1.0.0] - 2026-05-06

**Initial stable release.** The application has passed all QA testing and is ready for production use.

### Added
- **Frameless GUI** with custom title bar, SVG window controls, and drag-to-move support.
- **Light & Dark themes** with nature-inspired color palettes, toggled via the Theme button.
- **API Credential Setup** dialog with machine-specific Fernet encryption for secrets stored in `config.json`.
- **Async API Connection** — Authentication, resort loading, and membership loading all run on a background `QThread` (no UI freezing).
- **File Ingestion** — CSV and Excel (`.xlsx`/`.xls`) file loading with automatic column header matching.
- **Column Auto-Mapping** — Intelligent fuzzy matching of file headers to Camplife fields.
- **Optional Override Fields** — Global Membership Type, Tag, and Note overrides that apply to all rows.
- **Data Preview Dialog** — Full data table with live Status/Response columns updated per-row during upload.
- **Background Upload Engine** (`UploadWorker`) — Row-by-row processing of Membership (PUT), Note (POST), and Tag (PUT) API calls.
- **Upload Progress Dialog** — Modal progress bar with live ETA calculation, color-coded HTTP status grid, and cancel support.
- **Per-Row Response Inspector** (`ResponseDialog`) — Click any row post-upload to view detailed request/response logs.
- **Excel Upload Logs** — Automatic generation of timestamped `.xlsx` log files after each upload run.
- **Emergency Log Fallback** — If Excel log generation fails, raw JSON is written to a `.txt` file.
- **Retry Logic** — API calls retry up to 6 times on 401/403 errors.
- **Loading Screen** — Translucent splash screen with animated dots, shown during application startup.
- **PyInstaller Support** — `build.bat` and `.spec` file for building a distributable Windows executable.

### Fixed
- Status code recording in `PreviewDialog` was executing before values were extracted from API responses — now correctly records after extraction.

### Removed
- Debug `print()` statements from `security.py` and `setup_dialog.py`.
- Stale code comments referencing removed methods in `client.py`.
- Old date-based version format (`01.19.26`) replaced with semantic versioning (`1.0.0`).
