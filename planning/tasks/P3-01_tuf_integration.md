# Task P3-01: Integrate tufup TUF Metadata Verification

> **Phase**: 3 — Security | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

This task adds cryptographic verification of update metadata using TUF (The Update Framework) via the `tufup` library. Until this point, the update system relies on SHA-256 checksums for integrity. TUF adds authenticity — proving that the update was signed by the project maintainer, not just that the bytes are correct.

### Architectural Intent

- **Defense in depth**: TUF verification supplements (not replaces) SHA-256 checksums
- **Isolated integration**: TUF logic is contained in `integrity.py` and `update_checker.py` — no other modules need to know about TUF
- **Graceful degradation**: If TUF metadata is unavailable (e.g., first-ever release), fall back to SHA-256 only with a logged warning

---

## Affected Files

### Files to Modify

| File | Change |
|------|--------|
| `src/update/integrity.py` | Add TUF metadata verification functions |
| `src/update/update_checker.py` | Add TUF verification step to manifest processing |

---

## Dependencies & Prerequisites

- **P0-04**: TUF repository must be initialized with keys and metadata
- **P1-01**: `integrity.py` base implementation
- **P1-02**: `update_checker.py` base implementation
- `tufup` library installed

---

## Implementation Details

1. Add `verify_tuf_metadata()` function to `integrity.py` that validates TUF metadata chain
2. Add TUF verification step to `UpdateChecker._parse_manifest()` between SHA-256 check and staging
3. Bundle `root.json` with the application (via PyInstaller spec)
4. Write tests that verify tampered metadata is rejected

---

## Validation Requirements

1. Valid TUF metadata passes verification
2. Tampered metadata (modified target hash) is rejected
3. Expired metadata is rejected
4. Missing root.json falls back to SHA-256 only (with warning)

---

## Reasoning

**Why Phase 3 and not Phase 1?** SHA-256 checksums provide sufficient security for initial development and testing. TUF adds defense against sophisticated attacks (key compromise, replay) that are less likely during early deployment. Adding it in Phase 3 allows the core update logic to be tested and stabilized first.
