# Camplife DataLoader — Known Issues

> Version: 1.1.0 | Last Updated: 2026-05-15

---

## Active Issues

### 1. Web Application Firewall (WAF) blocks
- **Severity**: Low
- **Description**: The Camplife API sits behind a WAF. Rapid successive requests from the same IP may trigger rate limiting or a block, resulting in HTML error pages instead of JSON responses. The application handles this gracefully (retries + error logging) but the user may see failed rows.
- **Workaround**: If many rows fail with non-JSON responses, wait a few minutes and retry.

### 2. Machine-specific encryption is MAC-based
- **Severity**: Low
- **Description**: The encryption key for stored API secrets is derived from the machine's MAC address (`uuid.getnode()`). If the network adapter changes (e.g., docking station), decryption will fail silently and the raw ciphertext is returned as the "secret", causing authentication failure.
- **Workaround**: Re-enter API credentials via the Setup dialog after a hardware change.

---

## Resolved Issues

| Version | Issue | Resolution |
|---------|-------|------------|
| v1.1.0 | Token expiration during long uploads | Fixed — New `refresh_token_sync()` method in `CamplifeAPIClient` automatically refreshes token on 401/403 errors during upload. Uses `threading.Lock` for thread-safe access from `UploadWorker`. |
| v1.1.0 | Upload logs saved to working directory | Fixed — Upload log files now saved to `APP_DIR/logs/` directory; created automatically on app startup |
| v1.0.0 | Progress dialog status codes recorded before extraction | Fixed — `record_status()` now called after values are set |
| v1.0.0 | Debug `print()` statements in production code | Removed from `security.py` and `setup_dialog.py` |
| v1.0.0 | Encryption failure leaked plaintext secret as return value | `encrypt_secret()` now returns empty string on failure |
