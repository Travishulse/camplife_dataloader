# 03 — Security Considerations

> **Target Application**: Camplife DataLoader v1.1.0  
> **Status**: PLANNING  
> **Created**: 2026-05-27

---

## 1. Threat Model

### 1.1 Attack Surface

The update system introduces the following new attack surfaces:

```
┌───────────────────────────────────────────────────────────────┐
│                    ATTACK SURFACE MAP                          │
│                                                               │
│  [Network]                                                    │
│  ├── Update manifest fetch (HTTPS GET)                        │
│  ├── Archive/patch download (HTTPS GET)                       │
│  └── GitHub API queries (HTTPS GET)                           │
│                                                               │
│  [Local Filesystem]                                           │
│  ├── Staged update archives (.updates/)                       │
│  ├── Backup directories (.backups/)                           │
│  ├── Update state file (update_state.json)                    │
│  ├── TUF metadata (root.json, targets.json, etc.)             │
│  └── External updater script (apply_update.bat)               │
│                                                               │
│  [Process]                                                    │
│  ├── Main application process (reads/writes update state)     │
│  └── Updater script process (modifies application directory)  │
└───────────────────────────────────────────────────────────────┘
```

### 1.2 Threat Actors

| Actor | Capability | Motivation |
|-------|-----------|-----------|
| **Network attacker** | MITM, DNS spoofing | Distribute malware via fake update |
| **Local user** | File system access | Tamper with update state, inject malicious archive |
| **Compromised CI/CD** | Build pipeline access | Inject backdoor into legitimate release |
| **Compromised dependency** | Code execution during build | Supply chain attack |

### 1.3 Security Properties Required

| Property | Description | Mechanism |
|----------|-------------|-----------|
| **Authenticity** | Updates must originate from the project maintainer | TUF metadata signing (root key → targets key chain) |
| **Integrity** | Update content must not be modified in transit | SHA-256 checksums, HTTPS transport |
| **Freshness** | Client must not be fed stale/old versions as "updates" | TUF timestamp + snapshot metadata with expiry |
| **Non-repudiation** | Release artifacts are traceable to a specific build | GitHub Actions audit log + signed commits |

---

## 2. The Update Framework (TUF) Security Model

### 2.1 Why TUF

TUF (The Update Framework) is a CNCF-graduated project specifically designed to secure software update systems. It defends against:

| Attack | TUF Defense |
|--------|------------|
| **Arbitrary software** (attacker provides malicious file) | Targets metadata specifies exact expected hash |
| **Rollback attack** (attacker serves old vulnerable version) | Version monotonicity enforced by snapshot metadata |
| **Freeze attack** (attacker replays old valid metadata) | Timestamp metadata has short expiry (e.g., 1 day) |
| **Endless data** (attacker sends oversized download) | Targets metadata specifies expected file size |
| **Mix-and-match** (attacker combines files from different versions) | Snapshot metadata binds all target metadata to a single consistent state |
| **Key compromise** (attacker steals a signing key) | Role separation (root, targets, snapshot, timestamp) limits blast radius |

### 2.2 Key Hierarchy

```
root key (offline, air-gapped)
  └── targets key (build server, rotatable)
        ├── snapshot key (automated, short-lived)
        └── timestamp key (automated, short-lived)
```

| Key | Storage | Rotation | Compromise Impact |
|-----|---------|----------|-------------------|
| **Root key** | Offline USB drive, encrypted | Manual, infrequent (yearly or on compromise) | Can revoke all other keys; must be the most protected |
| **Targets key** | GitHub Actions secret (encrypted) | Per-release or quarterly | Attacker could sign malicious targets until revoked |
| **Snapshot key** | GitHub Actions secret (automated) | Automatic per release | Limited — can only freeze metadata, not change targets |
| **Timestamp key** | GitHub Actions secret (automated) | Automatic per release | Limited — can only freeze metadata, not change targets |

### 2.3 TUF Metadata Files

Distributed with the application and hosted on the update server:

| File | Purpose | Signed By | Expiry |
|------|---------|-----------|--------|
| `root.json` | Trust anchor; defines all other key roles | Root key | 1 year |
| `targets.json` | Lists all available update files with hashes and sizes | Targets key | 1 month |
| `snapshot.json` | Binds targets.json to a specific version (prevents mix-and-match) | Snapshot key | 1 week |
| `timestamp.json` | Proves metadata freshness (prevents freeze attacks) | Timestamp key | 1 day |

---

## 3. Transport Security

### 3.1 HTTPS Enforcement

| Requirement | Implementation |
|------------|---------------|
| All update URLs must use HTTPS | Hardcoded in `update_config.py`; no HTTP fallback |
| TLS version | TLS 1.2 minimum (Python's `ssl` default); TLS 1.3 preferred |
| Certificate validation | Python `requests` library validates by default via `certifi` bundle |
| Certificate pinning | Optional — pin to GitHub and Firebase root CAs for defense-in-depth |

### 3.2 Endpoint Hardening

```python
# update_config.py — endpoints are constants, not user-configurable
UPDATE_ENDPOINTS = {
    "primary": "https://api.github.com/repos/{owner}/{repo}/releases/latest",
    "fallback": "https://{project}.web.app/update-manifest.json",
}
# Users cannot override these URLs via config.json or environment variables
```

---

## 4. Update Verification Pipeline

Every downloaded update passes through this verification pipeline before any file operations occur:

```
Downloaded File
      │
      ▼
┌─────────────────┐     FAIL
│ 1. Size Check   │────────────▶ Reject + Log + Delete
│    (matches     │
│     manifest)   │
└────────┬────────┘
         │ PASS
         ▼
┌─────────────────┐     FAIL
│ 2. SHA-256      │────────────▶ Reject + Log + Delete
│    Checksum     │
│    Verify       │
└────────┬────────┘
         │ PASS
         ▼
┌─────────────────┐     FAIL
│ 3. TUF Metadata │────────────▶ Reject + Log + Delete
│    Signature    │
│    Verify       │
└────────┬────────┘
         │ PASS
         ▼
┌─────────────────┐     FAIL
│ 4. Archive      │────────────▶ Reject + Log + Delete
│    Structure    │
│    Validate     │
└────────┬────────┘
         │ PASS
         ▼
   Stage for Apply
```

### 4.1 Archive Structure Validation

After passing cryptographic verification, the archive is extracted to a temporary directory and validated for expected structure:

```python
REQUIRED_FILES = [
    "main.py",
    "config.py",
    "src/__init__.py",
    "src/api/client.py",
    "src/core/uploader.py",
    "src/gui/main_window.py",
]
# Archive must contain all required files or it is rejected
```

---

## 5. Local Security

### 5.1 File Permissions

| Directory/File | Permissions | Rationale |
|---------------|------------|-----------|
| `.updates/` | User read/write | Staging area for downloads; cleaned after apply |
| `.backups/` | User read/write | Recovery archives; must be accessible to batch script |
| `update_state.json` | User read/write | State tracking; no secrets stored |
| `apply_update.bat` | User read/execute | External updater; must not be world-writable |

### 5.2 Secrets Management

The update system does **not** introduce any new secrets. Specifically:

| Item | Contains Secrets? | Rationale |
|------|-------------------|-----------|
| `update_state.json` | No | Only contains version numbers, timestamps, paths |
| `update_config.py` | No | Only contains public URLs and constants |
| TUF metadata | No | Contains public keys (verification only, not signing) |
| Build secrets (TUF signing keys) | Yes — in CI/CD only | Stored as GitHub Actions encrypted secrets; never in repo or local files |

### 5.3 Interaction with Existing Security

The update system must not weaken the existing Fernet encryption of API credentials:

| Concern | Assessment |
|---------|-----------|
| Does the update system read `config.json`? | No — it only preserves/copies it as an opaque file |
| Does the update system write to `config.json`? | No — it is on the protected file list |
| Does the update system expose credentials in logs? | No — update logging never accesses credential fields |
| Does the update system change the machine key? | No — no interaction with `security.py` or MAC-based key derivation |

---

## 6. Security Risks Specific to This Application

### 6.1 Application-Specific Concerns

| Concern | Risk Level | Assessment |
|---------|-----------|------------|
| **API key exposure during update** | Low | `config.json` is on the protected list; never extracted from backups to logs |
| **Camplife API token theft via update** | Very Low | Tokens are in-memory only; not stored in files that the update system touches |
| **Malicious update calls Camplife API** | Very Low | Even a compromised update would need valid credentials from `config.json` (encrypted) |
| **Network credential sniffing during update** | Very Low | Update traffic is over HTTPS; Camplife API traffic is separate and also HTTPS |

### 6.2 Windows-Specific Security Concerns

| Concern | Mitigation |
|---------|-----------|
| UAC elevation | App installs in user-writable directory (`APP_DIR`); no elevation needed |
| SmartScreen warnings | Code signing (see cost analysis); or distribute via trusted internal channels |
| Windows Defender quarantine | Code signing + consistent naming + no obfuscation |
| NTFS alternate data streams | Archive extraction uses standard `zipfile` library which ignores ADS |

---

## 7. Code Signing Strategy

### 7.1 Options Evaluation

| Option | Cost | Trust Level | Complexity | Recommendation |
|--------|------|------------|------------|----------------|
| **No signing** | Free | Low (SmartScreen warnings) | None | ⚠️ Acceptable for internal distribution |
| **Self-signed certificate** | Free | None (users must manually trust) | Low | ❌ Not suitable |
| **Azure Artifact Signing** | ~$10/month | High (Microsoft-trusted) | Medium | ✅ Best for direct distribution |
| **Microsoft Store (MSIX)** | Free | High (Microsoft signs) | High (store packaging) | ⚠️ Overkill for this app |
| **SignPath Foundation** | Free (open source) | High | Medium | ❌ Only for open-source projects |

### 7.2 Recommendation

**Phase 1-2 (Development)**: No signing. Internal distribution to known users.

**Phase 3+ (Production)**: Adopt Azure Artifact Signing ($10/month) for professional trust. Integrate into GitHub Actions pipeline for automated signing on release.

---

## 8. Security Checklist for Implementation

Before marking each phase as complete, the following security checks must pass:

### Phase 0 (Foundation)
- [ ] TUF root key generated and stored offline (not in repository)
- [ ] GitHub Actions secrets configured (not hardcoded)
- [ ] No credentials in any planning or configuration files

### Phase 1 (Core Logic)
- [ ] SHA-256 verification tested with known-corrupt files
- [ ] Protected file list tested — `config.json` verified preserved
- [ ] Update state file contains no secrets
- [ ] All network calls use HTTPS with certificate validation

### Phase 2 (UI & Pipeline)
- [ ] No user-facing error messages leak internal paths or keys
- [ ] Download progress does not expose internal URLs to users
- [ ] CI/CD pipeline does not log signing keys or secrets

### Phase 3 (Security Hardening)
- [ ] TUF metadata verification rejects tampered metadata
- [ ] TUF metadata verification rejects expired metadata
- [ ] Archive with wrong SHA-256 is rejected
- [ ] Archive with valid SHA-256 but unsigned metadata is rejected
- [ ] No plaintext secrets in logs, state files, or error messages

---

> **Next**: See [04-rollback-recovery-strategy.md](./04-rollback-recovery-strategy.md) for recovery mechanisms.
