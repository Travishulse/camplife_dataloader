# Camplife DataLoader — Update Protocol

> This document defines the mandatory rules for all future modifications to the codebase. Any agent or developer making changes **must** follow this protocol.

---

## Pre-Change Checklist

Before modifying any file:

1. **Read the current version** from `config.py` → `VERSION`.
2. **Identify impacted modules** — list every file that will be touched or whose behavior will change.
3. **Verify variable/interface consistency** — confirm that function signatures, signal names, import paths, and config keys remain compatible with all callers.
4. **Check `docs/known-issues.md`** — ensure your change doesn't conflict with documented limitations.

## During Changes

1. **No partial features** — every change must be complete and functional. Do not leave TODO placeholders, stub functions, or commented-out experimental code.
2. **No duplicate documentation** — update existing docs rather than creating new ones that overlap.
3. **Preserve existing comments and docstrings** that are unrelated to the change.
4. **Follow existing naming conventions**:
   - Python: `snake_case` for variables/functions, `PascalCase` for classes.
   - Signals: `verb_noun` pattern (e.g., `connection_changed`, `resorts_loaded`).
   - Object names: `camelCase` for Qt `setObjectName()` values.

## Post-Change Requirements

Every change **must** include the following:

### 1. Version Bump
Update `VERSION` in `config.py` following semantic versioning:
- **MAJOR** (X.0.0) — Breaking changes to config format, API contract, or data flow.
- **MINOR** (x.Y.0) — New features, backward-compatible.
- **PATCH** (x.y.Z) — Bug fixes, backward-compatible.

### 2. Version History Entry
Add a new entry to `docs/version-history.md` using the standard format:

```markdown
## [vX.Y.Z] - YYYY-MM-DD
### Added
- ...
### Updated
- ...
### Fixed
- ...
### Removed
- ...
```

### 3. Known Issues Update
- If the change resolves a known issue, move it to the "Resolved Issues" section.
- If the change introduces a new limitation, add it to "Active Issues".

### 4. Architecture Update (if applicable)
If the change adds, removes, or significantly modifies a module, update `docs/architecture.md`.

### 5. Roadmap Update (if applicable)
If a planned feature from `docs/roadmap.md` is implemented, mark it as complete or remove it.

## Backward Compatibility

- All changes **must** maintain backward compatibility unless the MAJOR version is being bumped.
- If a breaking change is necessary:
  - Bump MAJOR version.
  - Document the migration path in the version history entry.
  - Update `docs/architecture.md` with the new interface/contract.

## Testing

- Run `tests/test_security.py` after any change to `src/core/security.py` or `config.py`.
- Run `tests/test_app.py` after any GUI or import path change.
- Follow the QA test plan in `tests/qa_test_plan.md` before any release build.

## File Organization Rules

```
camplife_dataloader/
├── main.py              # Entry point — do not add business logic here
├── config.py            # Version, URLs, paths — single source of truth
├── config.json          # Runtime credentials (gitignored, user-generated)
├── requirements.txt     # Python dependencies
├── build.bat            # PyInstaller build script
├── src/
│   ├── api/             # API client and background auth workers
│   ├── core/            # Upload engine and security utilities
│   └── gui/             # All UI components and themes
├── tests/               # Test scripts, test data, QA plan
└── docs/                # Architecture, version history, roadmap, known issues
```

- **Do not** create files outside this structure without updating this protocol.
- **Do not** place test files in the project root.
- **Do not** commit `__pycache__/`, `build/`, `dist/`, or `*.xlsx` log files.
