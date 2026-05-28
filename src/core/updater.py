import os
import sys
import json
import urllib.request
import tempfile
from PySide6.QtCore import QThread, Signal

def is_newer_version(current_str, latest_str):
    """Compare two semantic version strings."""
    try:
        c = [int(x) for x in current_str.lstrip('v').split('.')]
        l = [int(x) for x in latest_str.lstrip('v').split('.')]
        # Pad with zeros if version parts differ in length (e.g. 1.0 vs 1.0.1)
        max_len = max(len(c), len(l))
        c += [0] * (max_len - len(c))
        l += [0] * (max_len - len(l))
        return l > c
    except Exception:
        return latest_str != current_str

class UpdateChecker(QThread):
    """Background thread to check for updates from GitHub Releases API."""
    update_available = Signal(str, str, str)  # latest_version, release_notes, download_url
    no_update = Signal()
    error = Signal(str)

    def __init__(self, current_version, repo_owner, repo_name):
        super().__init__()
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name

    def run(self):
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Camplife-DataLoader-Updater"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            tag_name = data.get("tag_name", "")
            release_notes = data.get("body", "No release notes available.")
            
            # Find first asset containing .exe or zip, fallback to zipball_url
            download_url = None
            assets = data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe") or name.endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break
            
            if not download_url:
                download_url = data.get("zipball_url")
                
            if is_newer_version(self.current_version, tag_name):
                self.update_available.emit(tag_name, release_notes, download_url)
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.error.emit(str(e))


class UpdateDownloader(QThread):
    """Background thread to download the update executable/archive."""
    progress = Signal(int)  # percentage (0-100)
    finished = Signal(str)  # path to downloaded file
    error = Signal(str)

    def __init__(self, download_url, filename="update_package.exe"):
        super().__init__()
        self.download_url = download_url
        self.filename = filename

    def run(self):
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": "Camplife-DataLoader-Updater"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.info().get('Content-Length', 0))
                
                # Write to temp file or user directory
                temp_dir = tempfile.gettempdir()
                dest_path = os.path.join(temp_dir, self.filename)
                
                block_size = 8192
                downloaded = 0
                
                with open(dest_path, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        downloaded += len(buffer)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
                            
                self.finished.emit(dest_path)
        except Exception as e:
            self.error.emit(str(e))
