import json
import time
import hmac
import hashlib
import requests
import os
import logging

from config import CONFIG_FILE, TOKEN_ENDPOINT
from src.core.security import decrypt_secret, DecryptionError

logger = logging.getLogger("camplife.auth")


def perform_hmac_auth(api_key, api_secret):
    """
    Perform HMAC-SHA256 authentication with Camplife API.
    Returns dict with 'success', 'token', 'expiry', and 'error' keys.
    """
    try:
        timestamp = str(int(time.time()))
        base_url = f"{TOKEN_ENDPOINT}&access_key={api_key}&timestamp={timestamp}"
        signature_base = f"GET{base_url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        signature = hmac.new(api_secret.encode(), signature_base.encode(), hashlib.sha256).hexdigest()
        final_url = f"{base_url}&signature={signature}"

        resp = requests.get(final_url, headers=headers, timeout=20)
        if resp.status_code != 200:
            logger.error(f"Token request failed with status {resp.status_code}")
            return {
                "success": False,
                "token": None,
                "expiry": None,
                "error": f"Status {resp.status_code}"
            }

        data = resp.json()
        access_token = data.get("access_token", "")
        expires_in = data.get("expires_in", 3600)
        token_expiry = time.time() + expires_in

        logger.info(f"Authentication successful via HMAC, token expires in {expires_in}s")
        return {
            "success": True,
            "token": access_token,
            "expiry": token_expiry,
            "error": None
        }

    except Exception as e:
        logger.exception("HMAC authentication failed")
        return {
            "success": False,
            "token": None,
            "expiry": None,
            "error": str(e)
        }


def load_credentials_from_config():
    """
    Load API key and secret from config.json.
    Returns dict with 'success', 'key', 'secret', and 'error' keys.
    """
    try:
        if not os.path.exists(CONFIG_FILE):
            logger.warning("Config file not found")
            return {
                "success": False,
                "key": None,
                "secret": None,
                "error": "Config file not found"
            }

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        key = data.get("api_key", "")
        raw_secret = data.get("api_secret", "")
        try:
            secret = decrypt_secret(raw_secret)
        except DecryptionError as de:
            logger.error(f"Failed to decrypt API secret: {de}")
            return {
                "success": False,
                "key": None,
                "secret": None,
                "error": str(de)
            }

        if not key or not secret:
            logger.warning("API credentials incomplete in config")
            return {
                "success": False,
                "key": None,
                "secret": None,
                "error": "Credentials incomplete"
            }

        return {
            "success": True,
            "key": key,
            "secret": secret,
            "error": None
        }

    except Exception as e:
        logger.exception("Failed to load credentials from config")
        return {
            "success": False,
            "key": None,
            "secret": None,
            "error": str(e)
        }
