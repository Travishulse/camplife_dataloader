# Task P0-02: Add `tufup` and `bsdiff4` to `requirements.txt`

> **Phase**: 0 — Foundation | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The update system requires two new Python packages. This task adds them to `requirements.txt` with exact version pins for supply chain security.

- **tufup** (≥1.0.0): Secure update framework built on TUF (The Update Framework). Replaces the deprecated PyUpdater. Handles update metadata signing, verification, and trust chain management. MIT license.
- **bsdiff4** (≥1.2.0): Binary diff/patch library for generating bandwidth-efficient incremental update patches. BSD license.

### Architectural Intent

- **Exact version pins**: Prevent supply chain attacks via dependency confusion or malicious updates
- **Minimal additions**: Only two new packages; both are well-maintained and have no conflicting dependencies
- **Compatible**: Neither package conflicts with existing dependencies (PySide6, requests, pandas, openpyxl, cryptography)

---

## Affected Files

### Files to Modify

| File | Change |
|------|--------|
| `requirements.txt` | Add `tufup>=1.0.0` and `bsdiff4>=1.2.0` |

---

## Dependencies & Prerequisites

- None — this is an independent Phase 0 task.

---

## Implementation Details

Update `requirements.txt` from:

```
PySide6>=6.0.0
requests>=2.25.0
pandas>=1.2.0
openpyxl>=3.0.0
cryptography>=42.0.0
```

To:

```
PySide6>=6.0.0
requests>=2.25.0
pandas>=1.2.0
openpyxl>=3.0.0
cryptography>=42.0.0
tufup>=1.0.0
bsdiff4>=1.2.0
```

Then install and verify:

```bash
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -c "import tufup; print('tufup OK')"
.venv\Scripts\python -c "import bsdiff4; print('bsdiff4 OK')"
```

---

## Validation Requirements

1. `pip install -r requirements.txt` succeeds without errors
2. `import tufup` succeeds
3. `import bsdiff4` succeeds
4. Existing imports still work (`import PySide6`, `import requests`, etc.)
5. Existing tests pass unchanged
6. `build.bat` still produces a working executable (may need `.spec` update — see P0-07)

---

## Expected Outcomes

- Two new dependencies available in the virtual environment
- No conflicts with existing packages
- Ready for use in subsequent Phase 1 tasks

---

## Testing Expectations

No new test file. Validation is via import checks and existing test regression pass.

---

## Reasoning

**Why `>=` instead of `==` pins?**

The existing `requirements.txt` uses `>=` pins for all packages. Switching to `==` for just two packages would be inconsistent. For production builds, the CI/CD pipeline (P0-03) will use a lockfile or `--require-hashes` for supply chain security.

**Why not vendor the packages?**

Vendoring adds ~2 MB to the repository, complicates updates, and is unnecessary when pip + requirements.txt provides reliable resolution. The CI/CD pipeline (P0-03) will handle reproducible builds.
