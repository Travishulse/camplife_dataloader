# 06 — Authentication Strategy Recommendations

> **Target Application**: Camplife DataLoader v1.1.0  
> **Status**: PLANNING  
> **Created**: 2026-05-27

---

## 1. Current Authentication Model

The Camplife DataLoader currently uses a **direct API authentication** model with the Camplife platform:

```
User → Enters API Key + API Secret → Stored encrypted in config.json
                                      (Fernet, machine-specific MAC key)
                                           │
                                           ▼
App → HMAC-SHA256 signature → Camplife Token Endpoint → Access Token (in-memory)
                                                              │
                                                              ▼
                                                    Bearer token for API calls
                                                    (auto-refreshed on 401/403)
```

**Key characteristics**:
- No user identity system (no "users" — just API keys)
- No role-based access control
- No authentication for the application itself (anyone with the .exe can run it)
- Credentials are per-machine (encrypted with MAC-derived key)

---

## 2. Authentication Needs for the Update System

### 2.1 Requirements Analysis

| Requirement | Necessity | Rationale |
|------------|-----------|-----------|
| **Authenticate update source** | Mandatory | Verify updates come from the legitimate project maintainer |
| **Authenticate update content** | Mandatory | Verify downloaded files are not tampered |
| **Authenticate the user** | Optional | Only needed for beta/dev channels or restricted features |
| **Authorize update installation** | Not needed | Any user running the app should be able to update it |

### 2.2 What TUF Already Provides

The TUF (The Update Framework) integration via tufup already covers the first two requirements:

| Need | TUF Solution |
|------|-------------|
| Source authentication | Root key signs targets key; targets key signs release metadata |
| Content authentication | SHA-256 hashes in signed targets metadata |
| Freshness verification | Timestamp metadata with short expiry prevents replay attacks |

**For the stable channel, no additional authentication is needed.** TUF provides all necessary cryptographic verification.

---

## 3. Google Authentication Evaluation

### 3.1 When Google Auth Would Be Useful

| Use Case | Value | Phase |
|----------|-------|-------|
| **Beta channel access** | Restrict pre-release updates to authorized testers | Phase 3+ |
| **Update telemetry** | Track which organizations/users are on which versions | Future |
| **Per-organization settings** | Different update policies per campground organization | Future |
| **Admin dashboard** | Web dashboard for managing releases and monitoring adoption | Future |

### 3.2 Google Authentication Options

| Option | Cost | Complexity | Features |
|--------|------|-----------|----------|
| **Firebase Authentication** | Free (Spark plan: unlimited users) | Low | Google Sign-In, email/password, phone, anonymous |
| **Google Cloud Identity Platform** | Free (50K MAU) | Medium | Same as Firebase Auth with enterprise features |
| **Google OAuth 2.0 (raw)** | Free | Medium-High | Direct OAuth flow, requires custom token management |
| **Google Workspace domain restriction** | Free (if already using Workspace) | Low | Restrict to `@yourdomain.com` accounts |

### 3.3 Recommendation: Firebase Authentication (Deferred)

**Do NOT implement authentication in Phases 0-2.** It adds complexity without providing value for the stable update channel.

**Consider Firebase Authentication in Phase 3+ IF**:
- Beta testing requires restricted access
- Multi-organization management becomes necessary
- An admin dashboard is built for release management

**Rationale for Firebase Authentication when needed**:
1. **Free forever** for the expected user count (< 1000 users)
2. **Google Sign-In** eliminates password management burden
3. **Firebase Admin SDK** (Python) integrates easily for server-side verification
4. **JWT tokens** can be verified offline (no Firebase call needed for each check)
5. **Minimal code**: ~50 lines to add Google Sign-In to a PySide6 app via embedded web view

### 3.4 Firebase Auth Integration Sketch (Phase 3+)

If implemented, the authentication flow would be:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ User clicks       │────▶│ PySide6 QWebView │────▶│ Firebase Auth │
│ "Sign In for Beta"│     │ shows Google      │     │ returns JWT   │
│                   │     │ Sign-In page      │     │ token         │
└──────────────────┘     └──────────────────┘     └──────┬────────┘
                                                         │
                              ┌───────────────────────────┘
                              │
                       ┌──────▼──────┐     ┌──────────────┐
                       │ App stores   │────▶│ Include JWT   │
                       │ JWT locally  │     │ in update     │
                       │ (encrypted)  │     │ manifest      │
                       └─────────────┘     │ request       │
                                           └──────┬────────┘
                                                  │
                                           ┌──────▼──────┐
                                           │ Server       │
                                           │ verifies JWT │
                                           │ → serves     │
                                           │ beta manifest│
                                           └─────────────┘
```

---

## 4. Update Channel Authentication Model

### 4.1 Channel Access Matrix

| Channel | Authentication Required | Who Can Access |
|---------|----------------------|----------------|
| **stable** | None | All users |
| **beta** | Firebase Auth (Google Sign-In) | Authorized testers (email allowlist) |
| **dev** | Firebase Auth + role check | Developers only |

### 4.2 Channel Selection (Phase 3+)

```python
# update_config.py — channel configuration
UPDATE_CHANNELS = {
    "stable": {
        "manifest_url": "https://{project}.web.app/stable/update-manifest.json",
        "requires_auth": False,
    },
    "beta": {
        "manifest_url": "https://{project}.web.app/beta/update-manifest.json",
        "requires_auth": True,
        "auth_provider": "firebase",
        "allowed_emails": [],  # Managed via Firebase Console
    },
    "dev": {
        "manifest_url": "https://{project}.web.app/dev/update-manifest.json",
        "requires_auth": True,
        "auth_provider": "firebase",
        "required_role": "developer",
    },
}
```

---

## 5. Existing Camplife API Authentication — Impact Assessment

The update system has **zero interaction** with the Camplife API authentication system:

| Aspect | Update System | Camplife API |
|--------|--------------|-------------|
| Credentials | TUF signing keys (developer-side only) | API Key + Secret (user-side) |
| Token type | None (client doesn't authenticate to update server) | Bearer token (HMAC-SHA256) |
| Storage | TUF root.json (public metadata, bundled with app) | config.json (encrypted, machine-specific) |
| Network | GitHub API / Firebase Hosting | camplife.com REST API |

**The two authentication systems are completely independent.** Implementing the update system does not affect, weaken, or interact with the existing Camplife API authentication in any way.

---

## 6. Authentication Cost Summary

| Component | Cost | Notes |
|-----------|------|-------|
| TUF metadata signing | Free | Keys generated locally; open-source tooling |
| SHA-256 verification | Free | Built-in Python `hashlib` |
| Firebase Authentication | Free | Spark plan: unlimited auth users, Google Sign-In |
| Google OAuth 2.0 | Free | No cost for OAuth flows |
| Firebase Hosting (manifest) | Free | 10 GB storage, 10 GB/month transfer |

**Total authentication cost: $0/month** (for the expected usage pattern)

---

## 7. Recommendations Summary

| Phase | Authentication Action | Cost |
|-------|----------------------|------|
| **Phase 0-2** | TUF metadata verification only. No user authentication. | Free |
| **Phase 3** | Evaluate Firebase Auth for beta channel. Implement only if beta testing is active. | Free |
| **Phase 4+** | Consider Firebase Auth for admin dashboard if multi-org management is needed. | Free |

**Key principle**: Don't add authentication complexity until a concrete use case demands it. TUF provides all the cryptographic verification the stable update channel needs.

---

> **Next**: See [07-infrastructure-recommendations.md](./07-infrastructure-recommendations.md) for hosting and tooling evaluation.
