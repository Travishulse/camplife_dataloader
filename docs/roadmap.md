# Camplife DataLoader — Roadmap

> This document tracks planned features and improvements beyond v1.0.0.

---

## v1.1.0 — Stability & UX Improvements

| Feature | Description | Priority | Status |
|---------|-------------|----------|--------|
| ~~Logging framework~~ | ~~Replace remaining `print()` calls and add file-based logging with rotation~~ | ~~High~~ | ✅ Complete |
| ~~Token auto-refresh during upload~~ | ~~`UploadWorker` should request a fresh token mid-upload if the current one expires~~ | ~~High~~ | ✅ Complete |
| ~~Upload log directory~~ | ~~Save upload logs to a dedicated `logs/` directory instead of the project root~~ | ~~Medium~~ | ✅ Complete |
| ~~Row validation pre-upload~~ | ~~Highlight rows with missing required fields before starting the upload~~ | ~~Medium~~ | ✅ Complete |
| Keyboard shortcuts | Add Ctrl+O (open file), Ctrl+Q (quit), Ctrl+T (toggle theme) | Low | 🔴 Mothballed |

## v2.0.0 — Major Enhancements (Breaking)

| Feature | Description | Priority |
|---------|-------------|----------|
| Multi-property support | Upload to multiple resorts in a single session | High |
| Config migration | Move from flat `config.json` to a versioned config schema | Medium |
| Plugin-based field mapping | Allow custom field transformations via user-defined scripts | Low |
| REST API rate limiting | Implement configurable rate limiting with backoff strategy | Medium |

---

> Items are subject to change based on user feedback and operational requirements.
