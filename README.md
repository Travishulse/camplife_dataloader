# Camplife DataLoader

**Version 1.2.4** | A desktop application for bulk-uploading membership data, notes, and tags to the Camplife property management platform.

---

## Features

- **Bulk Data Upload** — Load a CSV or Excel file, map columns to Camplife fields, and upload memberships, notes, and tags in one operation.
- **Async & Non-Blocking** — All API calls (authentication, upload) run on background threads. The UI never freezes.
- **Encrypted Credentials** — API secrets are encrypted with machine-specific Fernet keys before saving to disk.
- **Live Progress** — Upload progress dialog with ETA, color-coded HTTP status grid, and cancel support.
- **Detailed Logging** — Per-row request/response inspector and automatic Excel log generation.
- **Themed UI** — Light and dark nature-inspired themes with a custom frameless window.

## Requirements

- **OS**: Windows 10 or later
- **Python**: 3.9+
- **Dependencies**: Listed in `requirements.txt`

## Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to the project directory
cd camplife_dataloader

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python main.py
```

### 3. Configure API Credentials

1. Click **⚙️ Setup** in the title bar.
2. Enter your Camplife API Key and API Secret.
3. Click **Save** — credentials are encrypted and stored in `config.json`.

### 4. Connect & Upload

1. Click **Connect** — the app authenticates and loads resort/membership data.
2. Click **Select File** — load your CSV or Excel file.
3. Verify the auto-mapped columns and set any overrides.
4. Click **Preview Data** → **Start Upload**.

## Building an Executable

```bash
# Run the build script (installs PyInstaller if needed)
build.bat
```

The executable will be in `dist/Camplife DataLoader/`.

## Project Structure

```
camplife_dataloader/
├── main.py              # Application entry point
├── config.py            # Version, API URLs, runtime paths
├── config.json          # User credentials (encrypted, not committed)
├── requirements.txt     # Python dependencies
├── build.bat            # PyInstaller build script
├── src/
│   ├── api/
│   │   ├── client.py    # CamplifeAPIClient — auth state & API calls
│   │   └── workers.py   # AuthWorker — background authentication
│   ├── core/
│   │   ├── uploader.py  # UploadWorker — row-by-row data upload
│   │   └── security.py  # Machine-specific Fernet encryption
│   └── gui/
│       ├── main_window.py    # Main application window
│       ├── themes.py         # Light & dark theme stylesheets
│       ├── loading_screen.py # Startup splash screen
│       ├── setup_dialog.py   # API credential setup dialog
│       ├── preview_dialog.py # Data preview & upload table
│       └── progress_dialog.py# Upload progress with ETA
├── tests/
│   ├── test_app.py      # GUI smoke test
│   ├── test_security.py # Encryption round-trip test
│   ├── test_data.csv    # Sample test data
│   └── qa_test_plan.md  # Full QA testing procedure
└── docs/
    └── UPDATE_WORKFLOW.md  # Step-by-step developer release & update workflow
```

## Documentation

| Document | Description |
|----------|-------------|
| [Update Workflow](docs/UPDATE_WORKFLOW.md) | Step-by-step developer release & update workflow |
| [QA Test Plan](tests/qa_test_plan.md) | Step-by-step testing procedure |

## License

Internal use only. © 2026 Camplife DataLoader.
