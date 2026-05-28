# Task P4-01: Update All Project Documentation

> **Phase**: 4 — Polish | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The update system is a significant addition to the Camplife DataLoader. All existing documentation must be updated to reflect the new modules, build process, and operational procedures. This follows the project's update protocol (`docs/update-protocol.md`) which requires architecture, version history, roadmap, and known issues updates.

### Architectural Intent

- **Single source of truth**: Documentation matches the actual code
- **Update protocol compliance**: All required documentation updates per `docs/update-protocol.md`
- **Future agent readability**: Updated docs enable future AI agents to understand the system without scanning all source files

---

## Affected Files

### Files to Modify

| File | Change |
|------|--------|
| `docs/architecture.md` | Add update system module descriptions, updated system diagram |
| `docs/version-history.md` | Add v2.0.0 release entry |
| `docs/roadmap.md` | Mark update system as complete; add future update system enhancements |
| `docs/known-issues.md` | Add any new limitations discovered during implementation |
| `docs/update-protocol.md` | Add build/release procedures for the CI/CD pipeline |
| `README.md` | Add update system section; update project structure diagram |
| `config.py` | Bump `VERSION` to `"2.0.0"` |
| `tests/qa_test_plan.md` | Add Phase 5: Update System testing procedures |

---

## Dependencies & Prerequisites

- All Phases 0-3 must be complete
- All tests must pass

---

## Implementation Details

### `docs/architecture.md` Updates

1. Add `src/update/` module descriptions (update_config, update_checker, update_manager, rollback_manager, integrity, version_utils)
2. Update the system diagram to include the update subsystem
3. Add update data flow description
4. Update dependencies table with tufup and bsdiff4

### `docs/version-history.md` Updates

Add v2.0.0 entry with all Added/Updated/Fixed/Removed sections documenting every change across all phases.

### `config.py` Update

```python
VERSION = "2.0.0"  # Major version bump — new update system
```

### `README.md` Updates

1. Update version badge
2. Add "Auto-Update" to Features list
3. Add update system section explaining how updates work from the user's perspective
4. Update project structure diagram to include `src/update/`, `scripts/`, `.updates/`, `.backups/`

---

## Validation Requirements

1. All documentation references correct file paths and module names
2. Version numbers are consistent across all files
3. Project structure diagrams match actual directory layout
4. No stale information from pre-update-system state
5. All links in documentation are valid

---

## Reasoning

**Why a dedicated documentation task instead of updating docs alongside code?** During rapid implementation across 4 phases, documentation written alongside code often becomes inconsistent as later phases modify earlier decisions. A single documentation pass at the end ensures consistency and completeness.
