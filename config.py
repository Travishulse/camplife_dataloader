import os
import sys

VERSION = "1.2.4"
BASE_API = "https://www.camplife.com/hub/api"
TOKEN_ENDPOINT = "https://www.camplife.com/hub/token?grant_type=client_signature"

# GitHub Update Repository Configuration
UPDATE_REPO_OWNER = "Travishulse"
UPDATE_REPO_NAME = "camplife_dataloader"

# Store config relative to the executable path for PyInstaller compatibility
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, '_MEIPASS', APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR

CONFIG_FILE = os.path.join(APP_DIR, "config.json")
CACHE_FILE = os.path.join(APP_DIR, "cache.json")
LOG_DIR = os.path.join(APP_DIR, "logs")
