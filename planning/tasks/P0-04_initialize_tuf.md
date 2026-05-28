# Task P0-04: Initialize TUF Repository & Generate Keys

> **Phase**: 0 — Foundation | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

TUF (The Update Framework) requires a set of cryptographic signing keys and initial metadata files to establish the chain of trust for update verification. This task generates those keys and creates the initial metadata structure.

### Architectural Intent

- **Offline root key**: The root key never touches a network-connected machine or CI/CD system
- **Separated roles**: Root, targets, snapshot, and timestamp keys have different trust levels
- **Initial metadata**: `root.json` is bundled with the application; other metadata is hosted remotely

---

## Affected Files

### Files to Create

| File | Purpose |
|------|---------|
| `tuf_repo/` (local, NOT committed) | TUF repository metadata and keys |
| `tuf_repo/root.json` | Initial root metadata (to be copied into app bundle) |

### Files to Modify

| File | Change |
|------|--------|
| `.gitignore` | Add `tuf_repo/keys/` to prevent key commitment |
| `Camplife DataLoader.spec` | Add `root.json` to `datas` list |

---

## Dependencies & Prerequisites

- **P0-02**: `tufup` must be installed
- **P0-03**: GitHub repository must exist (for storing targets/snapshot/timestamp keys as secrets)
- Encrypted USB drive for root key backup

---

## Implementation Details

1. Use `tufup` CLI to initialize a new TUF repository
2. Generate root key → store on encrypted USB drive
3. Generate targets, snapshot, timestamp keys → store as GitHub Actions secrets
4. Create initial `root.json` with all public keys
5. Add `root.json` to PyInstaller `.spec` datas list
6. Add key directories to `.gitignore`

---

## Validation Requirements

1. `root.json` is generated and contains valid TUF metadata
2. All keys are generated and stored securely
3. `root.json` is included in PyInstaller build output
4. No keys are committed to the repository

---

## Reasoning

**Why offline root key?** The root key can revoke all other keys. If compromised, the entire trust chain is broken. Keeping it offline limits the attack surface to physical access.
