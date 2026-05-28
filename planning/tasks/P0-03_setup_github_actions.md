# Task P0-03: Configure GitHub Actions CI/CD Workflow

> **Phase**: 0 — Foundation | **Priority**: High | **Status**: ⬜ Not Started

---

## Context

The Camplife DataLoader is currently built manually via `build.bat`. The update system requires an automated CI/CD pipeline that builds, tests, packages, and publishes releases when a version tag is pushed.

GitHub Actions is recommended because:
- Free for public and private repos (2,000 min/month private; unlimited public)
- Native integration with GitHub Releases
- Windows runners available (`windows-latest`)
- No additional infrastructure to manage

### Architectural Intent

- **Tag-triggered**: Releases are created by pushing a `v*.*.*` tag — no manual builds
- **Test-first**: Tests must pass before any build artifacts are created
- **Reproducible**: Pinned Python version, deterministic dependency installation
- **Secure**: Signing keys stored as GitHub Actions encrypted secrets

---

## Affected Files

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/test.yml` | Run tests on push to main and on pull requests |
| `.github/workflows/release.yml` | Full release pipeline on tag push |
| `scripts/generate_manifest.py` | Script to generate update-manifest.json from release artifacts |
| `scripts/generate_patch.py` | Script to generate bsdiff patches between versions |

### Existing Files — NO Modifications

No existing files are modified in this task. `build.bat` is preserved for local development builds.

---

## Dependencies & Prerequisites

- **GitHub repository**: Must exist (either create new or push existing code)
- **P0-02**: Dependencies must be added to `requirements.txt`

---

## Implementation Details

### `.github/workflows/test.yml`

```yaml
name: Tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/test_security.py tests/test_version_utils.py tests/test_integrity.py -v
```

### `.github/workflows/release.yml` (conceptual — details in planning/07-infrastructure-recommendations.md)

Triggered on `v*.*.*` tags. Steps:
1. Checkout → Setup Python → Install deps
2. Run all tests
3. PyInstaller build
4. Create ZIP archive
5. Generate SHA-256 checksums
6. Generate bsdiff patches (if previous release exists)
7. Generate update-manifest.json
8. Create GitHub Release with all artifacts
9. Deploy manifest to Firebase Hosting

---

## Validation Requirements

1. Pushing to `main` triggers the test workflow
2. Creating a `v*.*.*` tag triggers the release workflow
3. Test failures block the release
4. Release artifacts are attached to the GitHub Release
5. Workflow completes within the free tier limits (~10 min)

---

## Expected Outcomes

- Automated test pipeline runs on every push
- Tag-based releases produce consistent build artifacts
- No manual build steps required for releases
- Foundation for release pipeline extensions in Phase 2

---

## Testing Expectations

Verify by pushing a test tag (`v0.0.1-test`) and observing the workflow run in GitHub Actions. Delete the test tag and release afterward.

---

## Reasoning

**Why two separate workflows instead of one?**

Tests should run on every push for rapid feedback. The full release pipeline (build, package, publish) should only run on tags to avoid creating spurious releases. Separating them keeps each workflow focused and fast.

**Why not replace `build.bat`?**

`build.bat` is useful for local development and testing. Developers should be able to build locally without pushing to GitHub. The CI/CD pipeline is for production releases; `build.bat` is for development.
