# Task P0-05: Set Up Firebase Hosting for Manifest CDN

> **Phase**: 0 — Foundation | **Priority**: Medium | **Status**: ⬜ Not Started

---

## Context

Firebase Hosting serves as the CDN for the update manifest and TUF metadata files. It provides global distribution, free SSL, and no rate limiting — making it ideal as a fallback to the rate-limited GitHub API.

### Architectural Intent

- **Manifest-only hosting**: Only JSON metadata files (~10 KB total) are hosted on Firebase; binary archives stay on GitHub Releases
- **Free tier sufficient**: 10 GB storage + 10 GB/month transfer vastly exceeds needs
- **Automated deployment**: Firebase CLI deploys manifests from the CI/CD pipeline

---

## Affected Files

### Files to Create

| File | Purpose |
|------|---------|
| `firebase/firebase.json` | Firebase Hosting configuration |
| `firebase/.firebaserc` | Firebase project alias |
| `firebase/public/update-manifest.json` | Initial empty manifest |
| `firebase/public/version-catalog.json` | Initial version catalog |

---

## Dependencies & Prerequisites

- **P0-03**: GitHub repository must exist (for CI/CD deployment)
- Google account with Firebase access
- Firebase CLI installed (`npm install -g firebase-tools`)

---

## Implementation Details

1. Create a Firebase project via Firebase Console
2. Initialize Firebase Hosting in a `firebase/` subdirectory
3. Deploy initial placeholder manifest files
4. Configure CORS and caching headers
5. Document the Firebase project ID for CI/CD integration

---

## Validation Requirements

1. `https://{project}.web.app/update-manifest.json` returns valid JSON
2. SSL certificate is provisioned automatically
3. Response headers include appropriate Cache-Control (5 min max-age)

---

## Reasoning

**Why a separate `firebase/` directory?** Keeps Firebase configuration isolated from the Python application. The application code never references Firebase directly — only the URLs in `update_config.py`.
