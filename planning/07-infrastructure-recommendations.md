# 07 — Infrastructure Recommendations

> **Target Application**: Camplife DataLoader v1.1.0  
> **Status**: PLANNING  
> **Created**: 2026-05-27

---

## 1. Infrastructure Requirements

| Requirement | Description |
|------------|-------------|
| **Update manifest hosting** | Serve a JSON file (< 10 KB) over HTTPS with CDN |
| **Binary artifact hosting** | Host release archives (50-80 MB) and patches (1-5 MB) for download |
| **CI/CD pipeline** | Automated build, test, package, and release on version tag |
| **Version control** | Git repository with branch protection and tag-based releases |
| **TUF metadata hosting** | Serve TUF metadata files alongside update manifests |
| **Monitoring (optional)** | Basic visibility into download counts and error rates |

---

## 2. Infrastructure Options Comparison

### 2.1 Update Hosting

| Option | Cost | Storage | Bandwidth | CDN | HTTPS | Ease of Use | Recommendation |
|--------|------|---------|-----------|-----|-------|------------|----------------|
| **GitHub Releases** | Free | Unlimited (per release) | Generous (soft limits) | GitHub CDN | ✅ Built-in | Very Easy | ✅ **Primary** |
| **Firebase Hosting** | Free (Spark) | 10 GB | 10 GB/month | ✅ Global | ✅ Built-in | Easy | ✅ **Manifest CDN** |
| **Google Cloud Storage** | Free (5 GB) | 5 GB free | 1 GB/month free | ❌ (needs LB) | ❌ (needs LB) | Medium | ❌ Over-complex |
| **AWS S3 + CloudFront** | ~$1-5/month | Pay-per-use | Pay-per-use | ✅ | ✅ | Medium | ❌ Unnecessary cost |
| **Cloudflare R2** | Free (10 GB) | 10 GB free | Free egress | ✅ Cloudflare | ✅ Built-in | Medium | ⚠️ Good fallback |
| **Self-hosted (VPS)** | $5-10/month | Depends on VPS | Depends on VPS | ❌ | Needs Let's Encrypt | Hard | ❌ Operational burden |
| **Gitea/Forgejo** | Free (self-hosted) | Depends on host | Depends on host | ❌ | Needs setup | Hard | ❌ Operational burden |

### 2.2 Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  RECOMMENDED INFRASTRUCTURE                  │
│                                                              │
│  ┌───────────────────┐     ┌────────────────────────┐       │
│  │  GitHub Releases   │     │  Firebase Hosting       │       │
│  │  (PRIMARY)         │     │  (MANIFEST CDN)         │       │
│  │                    │     │                          │       │
│  │  • Release archives│     │  • update-manifest.json  │       │
│  │  • Patch files     │     │  • version-catalog.json  │       │
│  │  • SHA-256 sums    │     │  • TUF metadata files    │       │
│  │  • Changelogs      │     │  • (fast global CDN)     │       │
│  │  • Source code     │     │                          │       │
│  └───────────────────┘     └────────────────────────┘       │
│           │                           │                      │
│           └───────────┬───────────────┘                      │
│                       │                                      │
│              ┌────────▼────────┐                             │
│              │  GitHub Actions  │                             │
│              │  (CI/CD)         │                             │
│              │                  │                             │
│              │  • Build         │                             │
│              │  • Test          │                             │
│              │  • Package       │                             │
│              │  • Sign metadata │                             │
│              │  • Publish       │                             │
│              └─────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

**Why this split?**

| Component | Why GitHub Releases | Why Firebase Hosting |
|-----------|-------------------|---------------------|
| Binary archives | Designed for large file hosting; integrated with tags/releases | N/A (10 GB limit less suitable for many large files) |
| Update manifest | Version check API available but rate-limited (60 req/hr unauthenticated) | Global CDN, no rate limiting, < 1 KB JSON served in < 50ms |
| TUF metadata | Could work, but metadata changes frequently | CDN with instant global propagation; metadata < 10 KB |

---

## 3. CI/CD Pipeline Design

### 3.1 GitHub Actions Workflow

| Trigger | Workflow |
|---------|---------|
| Push to `main` | Run tests only (no build) |
| Tag `v*.*.*` | Full release pipeline: build → test → package → sign → publish |
| Manual dispatch | Build for testing (no publish) |

### 3.2 Release Pipeline Steps

```yaml
# .github/workflows/release.yml (conceptual)
name: Release Pipeline
on:
  push:
    tags: ['v*.*.*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      # 1. Checkout
      - uses: actions/checkout@v4

      # 2. Setup Python
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'

      # 3. Install dependencies
      - run: pip install -r requirements.txt pyinstaller tufup bsdiff4

      # 4. Run tests
      - run: python -m pytest tests/

      # 5. Build with PyInstaller
      - run: pyinstaller --noconfirm "Camplife DataLoader.spec"

      # 6. Create release archive
      - run: |
          cd dist
          Compress-Archive -Path "Camplife DataLoader" -DestinationPath "camplife-dataloader-${{ github.ref_name }}-win64.zip"

      # 7. Generate checksums
      - run: |
          Get-FileHash "dist/camplife-dataloader-*.zip" -Algorithm SHA256 | 
            Select-Object -ExpandProperty Hash > "dist/SHA256SUMS.txt"

      # 8. Generate patch (if previous version exists)
      - run: python scripts/generate_patch.py --from-version $PREV_VERSION --to-version ${{ github.ref_name }}

      # 9. Sign TUF metadata
      - run: python scripts/sign_tuf_metadata.py
        env:
          TUF_TARGETS_KEY: ${{ secrets.TUF_TARGETS_KEY }}

      # 10. Create GitHub Release
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            dist/camplife-dataloader-*.zip
            dist/SHA256SUMS.txt
            dist/patch-*.bsdiff
          body_path: RELEASE_NOTES.md

      # 11. Deploy manifest to Firebase
      - uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          projectId: camplife-dataloader-updates
          channelId: live
```

### 3.3 GitHub Actions Free Tier

| Resource | Free Limit | Expected Usage | Sufficient? |
|----------|-----------|----------------|-------------|
| Build minutes (public repo) | Unlimited | ~10 min per release | ✅ Yes |
| Build minutes (private repo) | 2,000 min/month | ~10 min per release × ~4 releases/month = 40 min | ✅ Yes |
| Storage (artifacts) | 500 MB | ~80 MB per release (auto-cleaned) | ✅ Yes |
| Concurrent jobs | 20 | 1 per release | ✅ Yes |

---

## 4. Firebase Hosting Setup

### 4.1 Project Structure

```
firebase-hosting/
├── firebase.json           # Hosting configuration
├── .firebaserc             # Project alias
└── public/
    ├── update-manifest.json
    ├── version-catalog.json
    └── tuf/
        ├── root.json
        ├── targets.json
        ├── snapshot.json
        └── timestamp.json
```

### 4.2 Firebase Free Tier (Spark Plan)

| Resource | Free Limit | Expected Usage | Sufficient? |
|----------|-----------|----------------|-------------|
| Hosting storage | 10 GB | < 1 MB (JSON metadata only) | ✅ Yes |
| Hosting transfer | 10 GB/month | ~10 KB × ~100 checks/month = ~1 MB | ✅ Yes |
| Custom domain | ✅ Included | Optional | ✅ Yes |
| SSL certificate | ✅ Auto-provisioned | Required | ✅ Yes |

### 4.3 Firebase Hosting Configuration

```json
// firebase.json
{
  "hosting": {
    "public": "public",
    "ignore": ["firebase.json", "**/.*"],
    "headers": [
      {
        "source": "**/*.json",
        "headers": [
          { "key": "Cache-Control", "value": "public, max-age=300" },
          { "key": "Access-Control-Allow-Origin", "value": "*" }
        ]
      }
    ]
  }
}
```

---

## 5. TUF Key Management Infrastructure

### 5.1 Key Storage Locations

| Key | Storage | Backup | Access |
|-----|---------|--------|--------|
| **Root key** | Encrypted USB drive (offline) | Second encrypted USB in separate physical location | Project owner only |
| **Targets key** | GitHub Actions secret (`TUF_TARGETS_KEY`) | Encrypted backup on root USB | CI/CD pipeline only |
| **Snapshot key** | GitHub Actions secret (`TUF_SNAPSHOT_KEY`) | Auto-generated; can be re-derived | CI/CD pipeline only |
| **Timestamp key** | GitHub Actions secret (`TUF_TIMESTAMP_KEY`) | Auto-generated; can be re-derived | CI/CD pipeline only |

### 5.2 Key Rotation Schedule

| Key | Rotation Frequency | Procedure |
|-----|-------------------|-----------|
| Root key | Annually or on compromise | Generate new root key offline; sign new root.json; distribute with next release |
| Targets key | Quarterly or on compromise | Generate new targets key; sign with root key; update GitHub secret |
| Snapshot key | Automatic per release | Generated by CI/CD pipeline |
| Timestamp key | Automatic per release | Generated by CI/CD pipeline |

---

## 6. Tooling Recommendations

### 6.1 Development Tools

| Tool | Purpose | Cost | Alternative |
|------|---------|------|------------|
| **Python 3.9+** | Application runtime | Free | — |
| **PyInstaller** | Executable packaging | Free | Nuitka (more complex, smaller binaries) |
| **tufup** | Secure update framework | Free | Custom TUF integration (more work) |
| **bsdiff4** | Binary diff generation | Free | xdelta3 (similar capability) |
| **GitHub Actions** | CI/CD pipeline | Free | GitLab CI (also free), Jenkins (self-hosted) |
| **Firebase CLI** | Hosting deployment | Free | — |

### 6.2 Monitoring Tools (Optional, Phase 4+)

| Tool | Purpose | Cost | Recommendation |
|------|---------|------|----------------|
| **GitHub Release download counts** | Track adoption | Free | ✅ Use (built-in) |
| **Firebase Analytics** | Track manifest fetch counts | Free | ⚠️ Consider |
| **Sentry (Python SDK)** | Error tracking and crash reporting | Free (5K events/month) | ⚠️ Consider for Phase 4+ |
| **Custom telemetry** | Update success/failure rates | Free (if using Firebase) | ⚠️ Consider for Phase 4+ |

---

## 7. Infrastructure Decision Log

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Primary artifact hosting | GitHub Releases | S3, R2, self-hosted | Free, integrated with CI/CD, trusted CDN |
| Manifest CDN | Firebase Hosting | GitHub Pages, Cloudflare Pages | Better CDN performance, no rate limiting, easy deploy |
| CI/CD | GitHub Actions | GitLab CI, CircleCI, Jenkins | Free for public repos, native GitHub integration |
| Update framework | tufup | Custom TUF, PyUpdater (deprecated), manual checksums | Active maintenance, TUF-based security, PyInstaller compatible |
| Patch format | bsdiff | xdelta3, courgette, custom | Python-native library, well-tested, good compression for binaries |
| Key management | Offline root + GitHub secrets | HashiCorp Vault, AWS KMS | Minimal cost, appropriate security for this threat model |

---

## 8. Infrastructure Cost Summary

| Component | Monthly Cost | Annual Cost |
|-----------|-------------|-------------|
| GitHub (repository + releases + actions) | $0 | $0 |
| Firebase Hosting (manifest CDN) | $0 | $0 |
| Firebase Authentication (future) | $0 | $0 |
| TUF key management (USB drives) | $0 (one-time ~$20) | $0 |
| Code signing (optional, Phase 3+) | $10 | $120 |
| Domain name (optional) | $0-12 | $0-12 |
| **Total (minimum)** | **$0** | **$0** |
| **Total (with code signing)** | **$10** | **$120** |

---

> **Next**: See [08-cost-analysis.md](./08-cost-analysis.md) for detailed cost projections and Claude API estimates.
