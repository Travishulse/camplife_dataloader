# Task P0-09: Implement `version_utils.py` — Semantic Version Parsing & Comparison

> **Phase**: 0 — Foundation | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The Camplife DataLoader uses semantic versioning (currently `VERSION = "1.1.0"` in `config.py`). The update system needs to compare the local version against the remote manifest's latest version to determine if an update is available.

This module provides reliable semver parsing, comparison, and ordering — essential for:
- Determining if an update is available (remote > local)
- Finding the correct patch path (e.g., "patch from 1.1.0 to 1.2.0")
- Enforcing `forced_update_below` minimum version requirements
- Ordering backup versions for retention policy

### Architectural Intent

- **No external dependencies**: Use Python's stdlib only (no `semver` package needed for our simple case)
- **Strict validation**: Reject malformed version strings early with clear errors
- **Immutable**: `AppVersion` instances are compared by value, not identity

---

## Affected Files

### Files to Create

| File | Purpose |
|------|---------|
| `src/update/version_utils.py` | Replaces placeholder from P0-01 |

### Files to Create (Tests)

| File | Purpose |
|------|---------|
| `tests/test_version_utils.py` | Unit tests for version parsing, comparison, ordering |

### Existing Files — NO Modifications

No existing files are modified in this task.

---

## Dependencies & Prerequisites

- **P0-01**: `src/update/` package must exist
- **Python 3.9+**: Uses `dataclass` and `__post_init__`

---

## Implementation Details

### `src/update/version_utils.py`

```python
"""
Semantic version parsing, comparison, and ordering utilities.

Supports standard semver format: MAJOR.MINOR.PATCH (e.g., "1.2.3").
Pre-release and build metadata are not supported (not needed for this application).
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, order=True)
class AppVersion:
    """
    Immutable semantic version representation.
    
    Supports comparison operators (<, >, ==, !=, <=, >=) and sorting.
    Ordering is: major → minor → patch (standard semver precedence).
    """
    major: int
    minor: int
    patch: int

    def __post_init__(self):
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError(
                f"Version components must be non-negative: {self.major}.{self.minor}.{self.patch}"
            )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> "AppVersion":
        """
        Parse a version string into an AppVersion.
        
        Accepts formats: "1.2.3", "v1.2.3", "V1.2.3"
        Raises ValueError for invalid formats.
        """
        if not isinstance(version_str, str):
            raise TypeError(f"Expected str, got {type(version_str).__name__}")
        
        cleaned = version_str.strip().lstrip("vV")
        
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", cleaned)
        if not match:
            raise ValueError(
                f"Invalid version format: '{version_str}'. Expected 'X.Y.Z' or 'vX.Y.Z'."
            )
        
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
        )


def is_update_available(current: str, remote: str) -> bool:
    """
    Check if the remote version is newer than the current version.
    
    Args:
        current: Current application version string (e.g., "1.1.0")
        remote: Remote manifest version string (e.g., "1.2.0")
    
    Returns:
        True if remote > current, False otherwise.
    
    Raises:
        ValueError: If either version string is invalid.
    """
    return AppVersion.from_string(remote) > AppVersion.from_string(current)


def is_version_below_minimum(current: str, minimum: str) -> bool:
    """
    Check if the current version is below a required minimum.
    Used for forced_update_below enforcement.
    
    Args:
        current: Current application version string
        minimum: Minimum required version string
    
    Returns:
        True if current < minimum, False otherwise.
    """
    return AppVersion.from_string(current) < AppVersion.from_string(minimum)


def get_version_jump_type(current: str, target: str) -> str:
    """
    Determine the type of version jump.
    
    Returns:
        "major" — breaking change (e.g., 1.x.x → 2.x.x)
        "minor" — new feature (e.g., 1.1.x → 1.2.x)
        "patch" — bug fix (e.g., 1.1.0 → 1.1.1)
        "none"  — same version
        "downgrade" — target is older than current
    """
    curr = AppVersion.from_string(current)
    tgt = AppVersion.from_string(target)
    
    if tgt < curr:
        return "downgrade"
    if tgt == curr:
        return "none"
    if tgt.major > curr.major:
        return "major"
    if tgt.minor > curr.minor:
        return "minor"
    return "patch"
```

### Key Design Decisions

1. **`frozen=True`**: Versions are immutable. Once parsed, they can't be accidentally mutated.
2. **`order=True`**: Enables `<`, `>`, `==` operators automatically via `dataclass` ordering.
3. **No pre-release support**: The Camplife DataLoader uses simple `X.Y.Z` versioning. Adding pre-release (`-beta.1`) complexity is unnecessary and would increase the testing surface.
4. **`from_string` accepts `v` prefix**: GitHub tags typically use `v1.2.0` format, while `config.py` uses `1.2.0`. Both must work.

---

## Validation Requirements

1. **Unit tests pass**: `python -m pytest tests/test_version_utils.py -v`
2. **Integration check**: `python -c "from src.update.version_utils import is_update_available; print(is_update_available('1.1.0', '1.2.0'))"` prints `True`
3. **No regressions**: Existing tests still pass

---

## Expected Outcomes

- `src/update/version_utils.py` is a fully functional module with 3 public functions and 1 data class
- Comprehensive test coverage for edge cases (invalid strings, v-prefix, same version, downgrades)
- Module is importable and usable by `update_checker.py` (Task P1-02)

---

## Testing Expectations

Create `tests/test_version_utils.py` with at minimum these test cases:

| Test Case | Input | Expected |
|-----------|-------|----------|
| Parse valid version | `"1.2.3"` | `AppVersion(1, 2, 3)` |
| Parse v-prefixed | `"v1.2.3"` | `AppVersion(1, 2, 3)` |
| Parse V-prefixed | `"V1.2.3"` | `AppVersion(1, 2, 3)` |
| Parse with whitespace | `" 1.2.3 "` | `AppVersion(1, 2, 3)` |
| Reject two-part | `"1.2"` | `ValueError` |
| Reject empty | `""` | `ValueError` |
| Reject non-numeric | `"a.b.c"` | `ValueError` |
| Reject negative | Via constructor with `-1` | `ValueError` |
| Reject None | `None` | `TypeError` |
| Compare equal | `1.0.0 == 1.0.0` | `True` |
| Compare less than | `1.0.0 < 1.0.1` | `True` |
| Compare greater than | `1.1.0 > 1.0.9` | `True` |
| Compare major precedence | `2.0.0 > 1.99.99` | `True` |
| is_update_available: yes | `("1.1.0", "1.2.0")` | `True` |
| is_update_available: no | `("1.2.0", "1.1.0")` | `False` |
| is_update_available: same | `("1.1.0", "1.1.0")` | `False` |
| Jump type: major | `("1.1.0", "2.0.0")` | `"major"` |
| Jump type: minor | `("1.1.0", "1.2.0")` | `"minor"` |
| Jump type: patch | `("1.1.0", "1.1.1")` | `"patch"` |
| Jump type: none | `("1.1.0", "1.1.0")` | `"none"` |
| Jump type: downgrade | `("1.2.0", "1.1.0")` | `"downgrade"` |
| Sorting list | `[v1.2.0, v1.0.0, v1.1.0]` | `[v1.0.0, v1.1.0, v1.2.0]` |
| String representation | `str(AppVersion(1, 2, 3))` | `"1.2.3"` |

---

## Reasoning

**Why not use the `semver` PyPI package?**

Adding a dependency for simple `X.Y.Z` comparison is overkill. The Camplife DataLoader doesn't use pre-release tags, build metadata, or version ranges. A 60-line custom implementation is easier to understand, has zero dependency risk, and is sufficient for all foreseeable needs.

**Why `dataclass(frozen=True, order=True)` instead of a plain class?**

Frozen dataclasses provide immutability and comparison operators for free. This eliminates an entire class of bugs (accidental mutation) and reduces boilerplate (no custom `__lt__`, `__eq__`, etc.). The ordering follows field declaration order (major → minor → patch), which is exactly semver precedence.

**Why `from_string` instead of `__init__` accepting strings?**

Separating parsing from construction keeps the constructor simple and type-safe. `AppVersion(1, 2, 3)` is always valid by construction. String parsing — which can fail — is explicit via `from_string()`. This is a standard Python pattern for value objects.
