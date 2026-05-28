# Camplife DataLoader — Architecture

> Version: 1.1.0 | Last Updated: 2026-05-15

## Overview

The Camplife DataLoader is a desktop application for bulk-uploading customer membership data, notes, and tags to the [Camplife](https://www.camplife.com) property management platform via its REST API. It is built for **Windows** using Python and the **PySide6** (Qt 6) GUI framework.

## System Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    main.py (Entry Point)                 │
│         LoadingScreen → FramelessCamplifeLoader          │
└────────────────┬─────────────────────────────────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
┌────▼────────┐     ┌───────▼──────────┐
│  src/gui/   │     │    src/api/      │
│             │     │                  │
│ main_window │────▶│ client.py        │
│ themes      │     │   (CamplifeAPI-  │
│ loading_scr │     │    Client)       │
│ setup_dlg   │     │                  │
│ preview_dlg │     │ workers.py       │
│ progress_dlg│     │   (AuthWorker)   │
└──────┬──────┘     └───────┬──────────┘
       │                    │
       │            ┌───────▼──────────┐
       │            │    src/core/     │
       │            │                  │
       └───────────▶│ uploader.py      │
                    │   (UploadWorker) │
                    │ security.py      │
                    │   (Fernet enc)   │
                    └──────────────────┘
                            │
                    ┌───────▼──────────┐
                    │    config.py     │
                    │  VERSION, URLs,  │
                    │  paths           │
                    └──────────────────┘
```

## Module Descriptions

### `main.py` — Application Entry Point
- Initializes `QApplication` with the light theme.
- Shows a `LoadingScreen` splash, then transitions to `FramelessCamplifeLoader`.
- Auto-connects to the Camplife API if saved credentials exist.
- Includes a 15-second safety timeout for connection.

### `config.py` — Centralized Configuration
- `VERSION` — Semantic version string (`1.1.0`).
- `BASE_API` / `TOKEN_ENDPOINT` — Camplife API URLs.
- `APP_DIR` / `CONFIG_FILE` — Runtime paths, PyInstaller-compatible.

### `src/api/client.py` — `CamplifeAPIClient`
- Singleton-like QObject managing auth state and API calls.
- Delegates authentication to `AuthWorker` (background thread).
- Provides `make_api_call_with_retry()` for use by `UploadWorker`.
- Emits Qt signals: `status_msg`, `connection_changed`, `resorts_loaded`, `memberships_loaded`.

### `src/api/workers.py` — `AuthWorker`
- Background `QThread` that: authenticates via HMAC-SHA256 signature, fetches resort list, fetches membership types.
- Emits results back to `CamplifeAPIClient` via signals.

### `src/core/uploader.py` — `UploadWorker`
- Background `QThread` for row-by-row data upload.
- Processes Membership (PUT), Note (POST), and Tag (PUT) API calls per row.
- Supports cancellation, progress reporting, and per-row log emission.

### `src/core/security.py` — Credential Encryption
- Machine-specific Fernet encryption using hardware MAC address as seed.
- `encrypt_secret()` / `decrypt_secret()` — used to protect API secrets stored in `config.json`.

### `src/gui/main_window.py` — `FramelessCamplifeLoader`
- Custom frameless main window with drag-to-move, min/max/close via SVG icons.
- File loading (CSV/Excel), column auto-mapping, override fields.
- Theme toggling (light/dark).

### `src/gui/themes.py` — Theme Stylesheets
- `LIGHT_THEME` / `DARK_THEME` — Complete Qt stylesheets with nature-inspired color palettes.
- SVG icon constants for window controls.

### `src/gui/loading_screen.py` — `LoadingScreen`
- Translucent frameless splash screen with animated loading dots.

### `src/gui/setup_dialog.py` — `SetupDialog`
- Modal dialog for entering/saving API Key and Secret.
- Secrets are encrypted before writing to `config.json`.

### `src/gui/preview_dialog.py` — `PreviewDialog` / `ResponseDialog`
- Data preview table showing only utilized Camplife fields (ID, Member #, Type, Dates, Tag, Note) plus Status/Response columns.
- Unmarked columns and fields with no mapped value are hidden; override fields display the override value with `(Override)` header suffix.
- Triggers `UploadWorker` and updates the table row-by-row.
- `ResponseDialog` — detailed per-row request/response inspector.
- Saves upload logs to Excel files.

### `src/gui/progress_dialog.py` — `UploadProgressDialog`
- Modal progress bar with ETA calculation.
- Color-coded HTTP status code grid.
- Cancel support.

## Data Flow

1. User enters API credentials → saved encrypted to `config.json`.
2. User clicks **Connect** → `AuthWorker` authenticates and loads resorts/memberships.
3. User loads a CSV/Excel file → columns auto-mapped to Camplife fields.
4. User optionally sets overrides (Membership Type, Tag, Note).
5. User clicks **Preview** → `PreviewDialog` opens with a data table.
6. User clicks **Start Upload** → `UploadWorker` processes each row in a background thread.
7. Results appear live in the preview table; a full Excel log is saved on completion.

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| PySide6 over Tkinter | Modern Qt widgets, native look, rich styling via QSS |
| Background QThreads | Non-blocking UI during API calls (auth + upload) |
| Fernet (machine-key) | Secrets encrypted at rest; tied to specific machine |
| Frameless window | Custom branded title bar with theme toggling |
| Semantic Versioning | Clear, predictable release management |

## Dependencies

| Package | Purpose |
|---------|---------|
| `PySide6` ≥ 6.0.0 | Qt 6 GUI framework |
| `requests` ≥ 2.25.0 | HTTP client for Camplife API |
| `pandas` ≥ 1.2.0 | CSV/Excel file parsing and DataFrame operations |
| `openpyxl` ≥ 3.0.0 | Excel file read/write support |
| `cryptography` ≥ 42.0.0 | Fernet symmetric encryption |
