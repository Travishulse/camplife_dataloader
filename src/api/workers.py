import requests
import logging
from PySide6.QtCore import QThread, Signal

from config import BASE_API
from src.api.auth_utils import perform_hmac_auth, load_credentials_from_config

logger = logging.getLogger("camplife.auth")

class AuthWorker(QThread):
    """
    Background worker that handles:
    1. Authenticating with Camplife API
    2. Fetching Resorts
    3. Fetching Membership Types
    """
    status_msg = Signal(str, int)
    finished = Signal(bool)
    resorts_loaded = Signal(list)
    memberships_loaded = Signal(list)

    def run(self):
        try:
            creds = load_credentials_from_config()
            if not creds["success"]:
                logger.warning(f"Failed to load credentials: {creds['error']}")
                self.status_msg.emit(f"API credentials error: {creds['error']}", 5000)
                self.finished.emit(False)
                return

            logger.info("Starting authentication")
            self.status_msg.emit("Authenticating...", 0)
            auth_result = perform_hmac_auth(creds["key"], creds["secret"])
            if not auth_result["success"]:
                logger.error(f"Authentication failed: {auth_result['error']}")
                self.status_msg.emit(f"Token request failed: {auth_result['error']}", 5000)
                self.finished.emit(False)
                return

            access_token = auth_result["token"]
            token_expiry = auth_result["expiry"]

            logger.info("Loading resorts")
            self.status_msg.emit("Loading resorts...", 0)
            headers_auth = {"Authorization": f"Bearer {access_token}"}
            resp_res = requests.get(f"{BASE_API}/property", headers=headers_auth, timeout=15)
            resorts = []
            if resp_res.status_code == 200:
                resorts = resp_res.json()
                logger.info(f"Loaded {len(resorts)} resorts")
                self.resorts_loaded.emit(resorts)
            else:
                logger.warning(f"Failed to fetch resorts: status {resp_res.status_code}")
                self.status_msg.emit(f"Failed to fetch resorts: {resp_res.status_code}", 5000)

            logger.info("Loading membership types")
            self.status_msg.emit("Loading memberships...", 0)
            resp_mem = requests.get(f"{BASE_API}/account/membership", headers=headers_auth, timeout=15)
            if resp_mem.status_code == 200:
                mem_data = resp_mem.json()
                names = []
                for entry in mem_data:
                    if isinstance(entry, dict):
                        for k in entry.keys():
                            names.append(k)
                filtered = [ (n[:100] + "...") if len(n) > 100 else n for n in names if n and str(n).strip() != "" ]
                logger.info(f"Loaded {len(filtered)} membership types")
                self.memberships_loaded.emit(filtered)
            else:
                logger.warning(f"Failed to fetch memberships: status {resp_mem.status_code}")
                self.status_msg.emit(f"Failed to fetch memberships: {resp_mem.status_code}", 5000)

            logger.info("Authentication and data loading complete")
            self.status_msg.emit("Connected ✅", 5000)
            self.auth_result = {
                "token": access_token,
                "expiry": token_expiry
            }
            self.finished.emit(True)

        except Exception as e:
            logger.exception("Authentication failed with exception")
            self.status_msg.emit(f"Connection error: {str(e)}", 7000)
            self.finished.emit(False)


class FetchStaticDataWorker(QThread):
    """
    Fetches resorts and membership types given explicit api_key and api_secret strings.
    Used by the setup dialog's Refresh button and can be reused elsewhere.
    """
    resorts_loaded = Signal(list)
    memberships_loaded = Signal(list)
    finished = Signal(bool, str)  # (success, message)

    def __init__(self, api_key, api_secret, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.api_secret = api_secret

    def run(self):
        try:
            auth_result = perform_hmac_auth(self.api_key, self.api_secret)
            if not auth_result["success"]:
                self.finished.emit(False, f"Auth failed: {auth_result['error']}")
                return

            headers_auth = {"Authorization": f"Bearer {auth_result['token']}"}

            resp_res = requests.get(f"{BASE_API}/property", headers=headers_auth, timeout=15)
            resorts = []
            if resp_res.status_code == 200:
                resorts = resp_res.json()
                self.resorts_loaded.emit(resorts)
            else:
                self.finished.emit(False, f"Failed to fetch resorts: {resp_res.status_code}")
                return

            resp_mem = requests.get(f"{BASE_API}/account/membership", headers=headers_auth, timeout=15)
            memberships = []
            if resp_mem.status_code == 200:
                mem_data = resp_mem.json()
                names = [k for entry in mem_data if isinstance(entry, dict) for k in entry.keys()]
                memberships = [(n[:100] + "...") if len(n) > 100 else n for n in names if n and str(n).strip()]
                self.memberships_loaded.emit(memberships)
            else:
                self.finished.emit(False, f"Failed to fetch memberships: {resp_mem.status_code}")
                return

            self.finished.emit(True, f"Loaded {len(resorts)} resorts, {len(memberships)} membership types")

        except Exception as e:
            logger.exception("FetchStaticDataWorker failed")
            self.finished.emit(False, f"Error: {str(e)}")
