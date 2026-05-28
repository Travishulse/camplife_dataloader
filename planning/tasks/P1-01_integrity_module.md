# Task P1-01: Implement `integrity.py` — SHA-256 Verification & File Integrity

> **Phase**: 1 — Core Logic | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

Every downloaded update archive must be verified before any file operations occur. This module provides the cryptographic integrity verification layer — the first line of defense against corrupted downloads, tampered archives, and man-in-the-middle attacks.

The Camplife DataLoader already uses `cryptography` (Fernet) for credential encryption in `src/core/security.py`. This module uses Python's built-in `hashlib` for SHA-256 — no additional dependencies needed.

### Architectural Intent

- **Defense in depth**: This is one of multiple verification steps (size → hash → TUF signature → structure)
- **Fail-safe**: Any verification failure immediately rejects the file and logs the reason
- **Reusable**: Functions work on any file path — used by both update_manager and rollback_manager

---

## Affected Files

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/update/integrity.py` | Replace placeholder | SHA-256 hashing, verification, directory hashing |

### Files to Create (Tests)

| File | Purpose |
|------|---------|
| `tests/test_integrity.py` | Unit tests for hash computation, verification, corruption detection |

### Existing Files — NO Modifications

No existing files are modified.

---

## Dependencies & Prerequisites

- **P0-01**: `src/update/` package must exist
- **Python stdlib**: `hashlib`, `os`, `pathlib` — no external dependencies

---

## Implementation Details

### `src/update/integrity.py`

The module must provide these functions:

```python
"""
File integrity verification using SHA-256 checksums.

Used to verify downloaded update archives before applying them.
All functions operate on local file paths — no network access.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("camplife.update.integrity")

# Read files in 8 KB chunks to avoid loading large archives into memory
_HASH_CHUNK_SIZE = 8192


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the hex digest hash of a file.
    
    Args:
        file_path: Absolute path to the file.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Lowercase hex string of the file's hash.
    
    Raises:
        FileNotFoundError: If file_path does not exist.
        OSError: If file cannot be read.
    """
    # Implementation: open file in binary mode, read in chunks, return hexdigest
    ...


def verify_file_hash(file_path: str, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify that a file's hash matches the expected value.
    
    Args:
        file_path: Absolute path to the file.
        expected_hash: Expected hex digest string (case-insensitive).
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        True if hashes match, False otherwise.
    
    Logs:
        WARNING if hash mismatch (with first 12 chars of expected vs actual).
        INFO if hash matches.
    """
    ...


def verify_file_size(file_path: str, expected_size: int) -> bool:
    """
    Verify that a file's size matches the expected value.
    
    Args:
        file_path: Absolute path to the file.
        expected_size: Expected file size in bytes.
    
    Returns:
        True if sizes match, False otherwise.
    """
    ...


def compute_directory_hash(dir_path: str, algorithm: str = "sha256") -> str:
    """
    Compute a composite hash of all files in a directory (sorted, recursive).
    
    Used for backup verification — ensures the backup directory is complete
    and uncorrupted. Files are hashed in sorted order for deterministic results.
    
    Args:
        dir_path: Absolute path to the directory.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Hex digest of the composite hash.
    
    Raises:
        NotADirectoryError: If dir_path is not a directory.
    """
    # Implementation: walk directory sorted, hash each file, 
    # feed all hashes + relative paths into a final hash
    ...


def validate_archive_structure(extracted_dir: str, required_files: list[str]) -> tuple[bool, list[str]]:
    """
    Validate that an extracted archive contains all required files.
    
    Args:
        extracted_dir: Path to the extracted archive directory.
        required_files: List of relative paths that must exist.
    
    Returns:
        Tuple of (is_valid, missing_files).
        is_valid is True if all required files are present.
        missing_files is a list of paths that were not found.
    """
    ...
```

### Key Implementation Notes

1. **Chunk reading**: Use `_HASH_CHUNK_SIZE = 8192` to read files in chunks. This is critical because update archives can be 50-80 MB — loading them entirely into memory is wasteful.

2. **Case-insensitive hash comparison**: `expected_hash.lower() == actual_hash.lower()` — GitHub and different tools may produce upper or lowercase hex strings.

3. **Logging, not exceptions, for mismatches**: `verify_file_hash` returns `False` on mismatch rather than raising an exception. The caller (update_manager) decides what to do. But the mismatch is always logged as a WARNING.

4. **Directory hash determinism**: `compute_directory_hash` must sort file paths before hashing to ensure the same directory always produces the same hash regardless of filesystem enumeration order.

---

## Validation Requirements

1. **Unit tests pass**: `python -m pytest tests/test_integrity.py -v`
2. **Hash of known file**: Create a test file with known content, verify the hash matches the expected SHA-256
3. **Corruption detection**: Modify one byte of a test file, verify the hash no longer matches
4. **Large file performance**: Verify that hashing a ~50 MB file completes in < 5 seconds
5. **No regressions**: Existing tests still pass

---

## Expected Outcomes

- `src/update/integrity.py` provides 5 public functions for file integrity verification
- All functions are stateless and side-effect-free (except logging)
- Corruption detection is reliable — a single bit flip is caught
- Archive structure validation prevents applying an incomplete update

---

## Testing Expectations

Create `tests/test_integrity.py` with these test cases:

| Test Case | Description | Expected |
|-----------|-------------|----------|
| Hash of known content | Hash of `b"hello world"` file | Matches expected SHA-256 |
| Hash of empty file | Hash of 0-byte file | Valid hash (SHA-256 of empty input) |
| Verify matching hash | Correct hash matches | `True` |
| Verify mismatched hash | Wrong hash doesn't match | `False` |
| Verify case insensitive | Uppercase hash matches lowercase | `True` |
| File not found | Non-existent path | `FileNotFoundError` |
| Size verification pass | Correct size | `True` |
| Size verification fail | Wrong size | `False` |
| Directory hash deterministic | Same dir, hashed twice | Same result |
| Directory hash detects change | Modify one file in dir | Different result |
| Archive structure valid | All required files present | `(True, [])` |
| Archive structure invalid | One file missing | `(False, ["missing_file.py"])` |
| Archive structure empty dir | No files at all | `(False, [all required files])` |

---

## Reasoning

**Why not use the `cryptography` library already in the project?**

`hashlib` is Python stdlib and provides SHA-256 natively. Using `cryptography` for simple hashing would be over-engineering — `cryptography` is designed for encryption operations, not hash verification. Keeping the dependency surface small for the integrity module reduces the attack surface of the verification layer itself.

**Why return `bool` from `verify_file_hash` instead of raising on mismatch?**

The caller (update_manager) needs to orchestrate multiple verification steps. A boolean return allows the caller to combine results, log context, and decide the appropriate response (delete file, retry download, show error). Exceptions would force try/except blocks at every call site and make the orchestration code harder to read.

**Why include `validate_archive_structure`?**

A file can have a valid SHA-256 hash but still be the wrong file (e.g., an HTML error page from a CDN). Structure validation catches this class of error by verifying the extracted content looks like a Camplife DataLoader application.
