import json
import time
import requests
import threading
import logging
from PySide6.QtCore import QObject, Signal

from config import BASE_API
from src.api.workers import AuthWorker
from src.api.auth_utils import perform_hmac_auth, load_credentials_from_config

logger = logging.getLogger("camplife.api")

class CamplifeAPIClient(QObject):
    """Handles authentication and all network requests to Camplife."""

    status_msg = Signal(str, int)
    connection_changed = Signal(bool)
    resorts_loaded = Signal(list)
    memberships_loaded = Signal(list)

    def __init__(self):
        super().__init__()
        self.access_token = ""
        self.token_expiry = 0
        self._auth_worker = None
        self._token_lock = threading.Lock()

    def connect(self):
        """Asynchronously starts the connection and data loading process."""
        if self._auth_worker:
            try:
                if self._auth_worker.isRunning():
                    return
            except RuntimeError:
                self._auth_worker = None

        self._auth_worker = AuthWorker()
        
        # Forward signals from worker to client signals
        self._auth_worker.status_msg.connect(self.status_msg)
        self._auth_worker.resorts_loaded.connect(self.resorts_loaded)
        self._auth_worker.memberships_loaded.connect(self.memberships_loaded)
        
        # Handle completion
        self._auth_worker.finished.connect(self._on_auth_finished)
        
        self._auth_worker.start()

    def _on_auth_finished(self, success):
        """Callback when the background auth worker finishes."""
        if success:
            res = getattr(self._auth_worker, "auth_result", {})
            self.access_token = res.get("token", "")
            self.token_expiry = res.get("expiry", 0)
            self.connection_changed.emit(True)
        else:
            self.connection_changed.emit(False)
        
        # Clean up worker reference safely to avoid QThread destruction errors
        if self._auth_worker:
            self._auth_worker.deleteLater()
            # We don't set it to None immediately so Python GC doesn't destroy the wrapper
            # before the C++ thread fully exits. It will be overwritten on the next connect().

    def refresh_token_sync(self):
        """
        Synchronously refresh the access token from config.json.
        This is safe to call from background threads like UploadWorker.
        Returns True on success, False on failure.
        """
        with self._token_lock:
            try:
                creds = load_credentials_from_config()
                if not creds["success"]:
                    logger.error(f"Failed to load credentials for sync refresh: {creds['error']}")
                    return False

                auth_result = perform_hmac_auth(creds["key"], creds["secret"])
                if not auth_result["success"]:
                    logger.error(f"Sync token refresh failed: {auth_result['error']}")
                    return False

                self.access_token = auth_result["token"]
                self.token_expiry = auth_result["expiry"]
                logger.info("Token refreshed successfully during upload")
                return True

            except Exception as e:
                logger.exception("Sync token refresh raised exception")
                return False

    def make_api_call_with_retry(self, method, url, headers=None, json_payload=None, params=None, max_retries=6):
        """
        Perform an API call with exponential retries on connection exceptions,
        auth credentials errors (401/403), rate limits (429), or server errors (500/502/503/504).
        """
        headers = headers or {}
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                with self._token_lock:
                    headers["Authorization"] = f"Bearer {self.access_token}"

                resp = requests.request(method, url, headers=headers, json=json_payload, params=params, timeout=20)
                
                # Check status code categories
                if resp.status_code in (401, 403):
                    logger.warning(f"Credential error {resp.status_code} (attempt {attempt}/{max_retries}), attempting token refresh")
                    if attempt < max_retries:
                        if self.refresh_token_sync():
                            logger.info("Token refreshed, retrying request immediately")
                            continue
                        else:
                            logger.warning("Token refresh failed, backing off before retry")
                            time.sleep(min(16, 2 ** attempt))
                            continue
                    else:
                        self.status_msg.emit(f"Credential error after token refresh (attempt {attempt}/{max_retries}).", 5000)
                
                elif resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        sleep_time = int(retry_after)
                        sleep_time = min(30, max(2, sleep_time)) # cap between 2s and 30s
                    except Exception:
                        sleep_time = min(16, 2 ** attempt)
                    
                    logger.warning(f"Rate limited (429) on {url} (attempt {attempt}/{max_retries}). Sleeping for {sleep_time}s.")
                    self.status_msg.emit(f"Rate limited. Retrying in {sleep_time}s...", 4000)
                    if attempt < max_retries:
                        time.sleep(sleep_time)
                        continue
                        
                elif resp.status_code in (500, 502, 503, 504):
                    sleep_time = min(16, 2 ** attempt)
                    logger.warning(f"Server error {resp.status_code} on {url} (attempt {attempt}/{max_retries}). Sleeping for {sleep_time}s.")
                    self.status_msg.emit(f"Server error {resp.status_code}. Retrying in {sleep_time}s...", 4000)
                    if attempt < max_retries:
                        time.sleep(sleep_time)
                        continue
                
                # If we get here, it's either success (2xx) or client error (400, 404, etc.)
                try:
                    resp_json = resp.json()
                except Exception:
                    resp_json = None
                logger.info(f"{method} {url} -> {resp.status_code}")
                return {"status_code": resp.status_code, "json": resp_json, "text": resp.text}

            except Exception as e:
                sleep_time = min(16, 2 ** attempt)
                logger.warning(f"Request exception (attempt {attempt}/{max_retries}) on {url}: {e}. Sleeping for {sleep_time}s.")
                self.status_msg.emit(f"Connection issue. Retrying in {sleep_time}s...", 4000)
                if attempt < max_retries:
                    time.sleep(sleep_time)
                    continue

        logger.error(f"Request failed after {max_retries} attempts: {method} {url}")
        return {"status_code": None, "json": None, "text": f"Failed after {max_retries} attempts."}

